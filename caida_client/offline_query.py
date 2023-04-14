#!/usr/bin/env python3
# python character encoding: utf-8

import sys
import os
import argparse
import time
import json
import requests
from requests_oauthlib import OAuth2Session

DEFAULT_SCOPE = "openid offline_access"
DEFAULT_REALM = 'CAIDA'
manual_auth = False

class g: # global variables
    args = None
    token_info = None

def default_auth_url(realm):
    return f'https://auth.caida.org/realms/{realm}/protocol/openid-connect'

def save_tokens(new_token_info):
    oldmask = os.umask(0o077)
    with open(g.args.token_file, "w") as f:
        json.dump(new_token_info, f)
    os.umask(oldmask)
    print(f"### Saved new tokens to {g.args.token_file}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(
        description='Make a request to a protected CAIDA service.',
        epilog='If method is PUT or POST, and neither --data nor --datafile '
            'are given, the request body will be read from standard input.')
    parser.add_argument("-t", "--token-file",
        help="name of file containing offline token (default: {CLIENT_ID}.token)")
    parser.add_argument("--force-refresh",
        action='store_true',
        help="get a new access token even if the one in TOKEN_FILE is not "
            "expired (useful after an 'invalid token' error)")
    parser.add_argument("-r", "--realm", default=DEFAULT_REALM,
        help="Authorization realm (default: %(default)s)")
    parser.add_argument("-a", "--auth-url",
        help=f"Authorization URL (default: {default_auth_url('{REALM}')})")
    parser.add_argument("-s", "--scope", default=DEFAULT_SCOPE,
        help="Authorization scope (default: %(default)s)")
    parser.add_argument("-X", "--method", default='GET',
        help="Query method (default: %(default)s)")
    parser.add_argument("-d", "--data", type=os.fsencode,
        help="JSON request body")
    parser.add_argument("--datafile",
        help="name of file contaning JSON request body")
    parser.add_argument("--no-verify", default=True,
        dest='ssl_verify', action='store_false',
        help="Disable SSL host verification")
    parser.add_argument("client_id",
        metavar="CLIENT_ID",
        help="OIDC client id (e.g. 'myapp-offline')")
    parser.add_argument("query",
        metavar="QUERY",
        help="Query URL (e.g. 'https://api.myapp.caida.org/v1/foo')")
    g.args = parser.parse_args()

    if g.args.token_file is None:
        g.args.token_file = g.args.client_id + ".token"
    if g.args.auth_url is None:
        g.args.auth_url = default_auth_url(g.args.realm)

    if g.args.method in ['PUT', 'POST']:
        if g.args.data:
            data = g.args.data
        if g.args.datafile:
            with open(g.args.datafile) as f:
                data = f.read()
        else:
            data = sys.stdin.read()
    else:
        data = None

    headers = {
        'Content-type': 'application/json; charset=utf-8'
    }

    with open(g.args.token_file, "r") as f:
        g.token_info = json.load(f)
    if g.args.force_refresh or 'expires_in' not in g.token_info:
        refresh_token = g.token_info['refresh_token']
        g.token_info.clear()
        g.token_info['refresh_token'] = refresh_token
        g.token_info['expires_in'] = -1
        g.token_info['access_token'] = 'dummy value for oauthlib'
    else:
        # Assume the access token was issued shortly before the file
        # modification time.  (Parsing the JWT access token for its "iat"
        # value would be more reliable, but harder.)
        age = time.time() - (os.path.getmtime(g.args.token_file) - 5)
        g.token_info['expires_in'] -= age
    print("### expires_in=%r" % (g.token_info['expires_in'],), file=sys.stderr) # XXX

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

        if not 'access_token' in g.token_info or g.token_info['expires_in'] <= 0:
            print(f"### getting new access token", file=sys.stderr)
            authdata = {
                "client_id": g.args.client_id,
                "refresh_token": g.token_info['refresh_token'],
                "scope": g.args.scope,
                "grant_type": "refresh_token",
            }

            authheaders = {'Content-type': 'application/x-www-form-urlencoded'}
            response = session.post(g.args.auth_url + '/token', data=authdata,
                headers=authheaders, allow_redirects=False)

            if response.status_code < 200 or response.status_code > 299:
                print(response.text)
                sys.exit(1)
            g.token_info = response.json()
            save_tokens(g.token_info)
        else:
            print(f"### using stored access token", file=sys.stderr)

        headers['Authorization'] = f'Bearer {g.token_info["access_token"]}'

    else:
        # Recommended method for python: use requests-oauthlib.  After the session
        # is created, each session.get() or session.post() will automatically
        # use the refresh token to refresh the access token as needed.

        session = OAuth2Session(client_id=g.args.client_id,
                token=g.token_info,
                auto_refresh_url=(g.args.auth_url+'/token'),
                auto_refresh_kwargs={'client_id':g.args.client_id},
                token_updater=save_tokens)


    # Make the request
    # print("Request headers:  %r" % (headers,), file=sys.stderr)
    # print("Request data:  %r" % (data,), file=sys.stderr)
    # print("", file=sys.stderr)
    response = session.request(g.args.method, g.args.query, data=data,
            headers=headers, verify=g.args.ssl_verify)

    print("\x1b[31mHTTP response status: %r\x1b[m" % (response.status_code,),
            file=sys.stderr)
    print("HTTP response headers: %r" % (response.headers,), file=sys.stderr)
    print("HTTP response text:", file=sys.stderr)
    sys.stderr.flush()
    print(response.text)

if __name__ == '__main__':
    main()

