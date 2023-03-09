#!/usr/bin/env python3
# python character encoding: utf-8

import sys
import os
import argparse
import requests
from requests_oauthlib import OAuth2Session

DEFAULT_SCOPE = "openid offline_access"
DEFAULT_REALM = 'CAIDA'
manual_auth = False


def default_auth_url(realm):
    return f'https://auth.caida.org/realms/{realm}/protocol/openid-connect'

parser = argparse.ArgumentParser(
    description='Make a request to a protected CAIDA service.')
parser.add_argument("client_id",
    help="OIDC client id (e.g. 'myapp-offline')")
parser.add_argument("-t", "--token-file",
    help="name of file containing offline token (default: {CLIENT_ID}.tok)")
parser.add_argument("-r", "--realm", default=DEFAULT_REALM,
    help="Authorization realm (default: %(default)s)")
parser.add_argument("-a", "--auth-url",
    help=f"Authorization URL (default: {default_auth_url('{REALM}')})")
parser.add_argument("-s", "--scope", default=DEFAULT_SCOPE,
    help="Authorization scope (default: %(default)s)")
parser.add_argument("-X", "--method", default='GET',
    help="Query method (default: %(default)s)")
parser.add_argument("-d", "--data", type=os.fsencode,
    help="JSON query data (with -X POST or -X PUT)")
parser.add_argument("--no-verify", default=True,
    dest='ssl_verify', action='store_false',
    help="Disable SSL host verification")
parser.add_argument("query",
    help="Query URL")
args = parser.parse_args()

if args.token_file is None:
    args.token_file = args.client_id + ".tok"
if args.auth_url is None:
    args.auth_url = default_auth_url(args.realm)

def update_token_info(new_token_info):
    token_info.clear()
    token_info.update(new_token_info)

headers = {
    'Content-type': 'application/json; charset=utf-8'
}

token_info = {
    'access_token': 'dummy value for oauthlib',
    'refresh_token': None,
    'expires_in': '-1' # tell OAuth2Session: access_token needs to be refreshed
}

with open(args.token_file, "r") as f:
    token_info['refresh_token'] = f.read().strip()

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
    authdata = {
        "client_id": args.client_id,
        "refresh_token": token_info['refresh_token'],
        "scope": args.scope,
        "grant_type": "refresh_token",
    }

    authheaders = {'Content-type': 'application/x-www-form-urlencoded'}
    response = session.post(args.auth_url + '/token', data=authdata,
        headers=authheaders, allow_redirects=False)

    if response.status_code < 200 or response.status_code > 299:
        print(response.text)
        sys.exit(1)
    r = response.json()
    token_info['access_token'] = r['access_token']
    headers['Authorization'] = f'Bearer {token_info["access_token"]}'

else:
    # Recommended method for python: use requests-oauthlib.  After the session
    # is created, each session.get() or session.post() will automatically
    # use the refresh token to refresh the access token as needed.

    session = OAuth2Session(client_id=args.client_id,
            token=token_info,
            auto_refresh_url=(args.auth_url+'/token'),
            auto_refresh_kwargs={'client_id':args.client_id},
            token_updater=update_token_info)


# Make the request
print("Request headers:  %r" % (headers,))
print("Request data:  %r" % (args.data,))
print()

response = session.request(args.method, args.query, data=args.data,
        headers=headers, verify=args.ssl_verify)
print("\x1b[31mHTTP response status: %r\x1b[m" % (response.status_code,))
print("HTTP response headers: %r" % (response.headers,))
print("HTTP response text:")
print(response.text)

