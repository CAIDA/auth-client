#!/usr/bin/env python3
# python character encoding: utf-8

import sys
import os
import time
import argparse
import json
import requests
from requests_oauthlib import OAuth2Session
import caida_oidc_client

DEFAULT_REALM = 'CAIDA'
manual_auth = False

class g: # pylint: disable=invalid-name, too-few-public-methods
    """global variables"""
    args = None
    token_info = {}
    save_tokens = None

def eprint(*args, **kwargs):
    """print() to stderr"""
    print(*args, file=sys.stderr, **kwargs)

def print_exc_chain(exc):
    """Print a chain of exceptions (without a stack trace)"""
    if exc.__context__:
        print_exc_chain(exc.__context__)
    eprint(f"{type(exc).__name__}: {str(exc)}")

def main():
    """Main"""
    parser = argparse.ArgumentParser(
        description='Make a request to a protected CAIDA service.',
        epilog=
            'The response from the service will be written to standard output. '
            'Any other diagnostic output will be written to standard error. ')
    rare = parser.add_argument_group('rarely used options')
    parser.add_argument("-t", "--token-file",
        help="name of file containing offline token (default: {CLIENT_ID}.token)")
    rare.add_argument("--force-refresh",
        action='store_true',
        help="get a new access token even if the one in TOKEN_FILE is not "
            "expired (useful after an 'invalid token' error)")
    rare.add_argument("-r", "--realm", default=DEFAULT_REALM,
        help="Authorization realm (default: %(default)s)")
    parser.add_argument("-X", "--method", default='GET',
        help="HTTP request method (default: %(default)s)")
    parser.add_argument("-d", "--data", type=os.fsencode,
        help="request body")
    parser.add_argument("--datafile",
        help="name of file contaning request body, or '-' for standard input")
    parser.add_argument("-H", "--header", dest='headers',
        nargs=2, action='append', default=[], metavar=('NAME', 'VALUE'),
        help="HTTP request header (repeatable)")
    ct_json = ['Content-type', 'application/json; charset=utf-8']
    parser.add_argument("-j", "--json", dest='headers',
        action='append_const', const=ct_json,
        help=f"Equivalent to -H '{ct_json[0]}' '{ct_json[1]}'")
    rare.add_argument("--no-verify", default=True,
        dest='ssl_verify', action='store_false',
        help="Disable SSL host verification")
    parser.add_argument("client_id",
        metavar="CLIENT_ID",
        help="OIDC client id (e.g. 'foobar-offline')")
    parser.add_argument("query",
        metavar="QUERY",
        help="Query URL (e.g. 'https://api.foobar.caida.org/v1/foo')")
    g.args = parser.parse_args()

    if g.args.token_file is None:
        g.args.token_file = g.args.client_id + ".token"

    g.save_tokens = caida_oidc_client.make_save_tokens(g.args.token_file)

    headers = {h[0]: h[1] for h in g.args.headers}

    data = None
    if g.args.method in ['PUT', 'POST']:
        if g.args.data is not None:
            data = g.args.data
        elif g.args.datafile == '-':
            data = sys.stdin.read()
        elif g.args.datafile is not None:
            with open(g.args.datafile, encoding="utf8") as f:
                data = f.read()

    with open(g.args.token_file, "r", encoding="ascii") as f:
        g.token_info = json.load(f)
    if (g.args.force_refresh or 'expires_at' not in g.token_info or
            g.token_info['expires_at'] < time.time()):
        refresh_token = g.token_info['refresh_token']
        g.token_info.clear()
        g.token_info['refresh_token'] = refresh_token
        g.token_info['expires_in'] = -1
        g.token_info['access_token'] = 'dummy value for oauthlib'

    refresh_data = caida_oidc_client.jwt_decode(g.token_info['refresh_token'])
    g.token_url = refresh_data["iss"] + '/protocol/openid-connect/token'

    # request access token from auth server
    if manual_auth:
        # Manual method, for when requests-oauthlib isn't available, as a model
        # for other languages, or for educational purposes.  We use the refresh
        # token once up front to get an access token.  This is fine if we only
        # need to make one protected query, or even multiple queries before the
        # access token expires (~300s), but a long-lived process that makes
        # multiple queries will need additional code to refresh the access token
        # if it expires.
        session = requests.Session()

        if 'access_token' not in g.token_info or g.token_info['expires_in'] <= 0:
            eprint("### getting new access token")
            authdata = {
                "client_id": g.args.client_id,
                "refresh_token": g.token_info['refresh_token'],
                "grant_type": "refresh_token",
            }

            authheaders = {'Content-type': 'application/x-www-form-urlencoded'}
            response = session.post(g.token_url, data=authdata,
                headers=authheaders, allow_redirects=False)

            if response.status_code < 200 or response.status_code > 299:
                print(response.text)
                sys.exit(1)
            g.token_info = response.json()
            g.save_tokens(g.token_info)
        else:
            eprint("### using stored access token")

        headers['Authorization'] = f'Bearer {g.token_info["access_token"]}'

    else:
        # Recommended method for python: use requests-oauthlib.  After the session
        # is created, each session.get() or session.post() will automatically
        # use the refresh token to refresh the access token as needed.

        session = OAuth2Session(client_id=g.args.client_id,
                token=g.token_info,
                auto_refresh_url=g.token_url,
                auto_refresh_kwargs={'client_id':g.args.client_id},
                token_updater=g.save_tokens)


    # Make the request
    # eprint("Request headers:  %r" % (headers,))
    # eprint("Request data:  %r" % (data,))
    # eprint("")

    try:
        response = session.request(g.args.method, g.args.query, data=data,
                headers=headers, verify=g.args.ssl_verify)
    except Exception as e: # pylint: disable=broad-except
        print_exc_chain(e)
        sys.exit(1)

    eprint(f"\x1b[31mHTTP response status: {repr(response.status_code)}\x1b[m")
    eprint(f"HTTP response headers: {repr(response.headers)}")
    eprint("HTTP response text:")
    sys.stderr.flush()
    print(response.text)

if __name__ == '__main__':
    main()
