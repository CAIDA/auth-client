#!/usr/bin/env python3
# python character encoding: utf-8

import sys
import time
import requests
import urllib
import json
from requests_oauthlib import OAuth2Session

if len(sys.argv) != 2:
    print("usage: offline_query.py {refresh_token}")
    sys.exit(2)

# Keycloak parameters
auth_url = 'https://auth.caida.org/realms/CAIDA_TEST/protocol/openid-connect'
client_id = "river-offline"

# service parameters
api_url = "https://river.caida.org:8081/test"


def token_updater(tokens):
    # Save the received tokens for reuse
    print("#### token_updater: ", json.dumps(tokens, indent=2))
    token_params = tokens

data = b"{foo:'bar'}"
headers = {
    'Content-type': 'application/json; charset=utf-8'
}

token_params = {
    'access_token': '0',
    'refresh_token': None,
    # below are needed by requests_oauthlib
    'token_type': 'Bearer',
    'expires_in': '-1'
}

# load refresh token from file
#with open(sys.argv[3], "rb") as f:
#    token_params['refresh_token'] = str(f.read().strip(), 'ascii')

# read refresh token from cmdline
token_params['refresh_token'] = sys.argv[1]

verify_ssl = False  # True normally; False for testing with self-signed cert
manual_auth = False

# request access token from auth server
if manual_auth:
    # Manual method, for when requests-oauthlib isn't available, as a model
    # for other languages, or for educational purposes.  We use the refresh
    # token once up front to get an access token.  This is fine if we only
    # need to make one protected query, or even multiple queries before the
    # access token expires (~300s), but a long-lived process that makes
    # multiple queries will need additional code to periodically refresh the
    # access token.  (Refreshing before every query would technically work,
    # but would be very inefficient.)
    session = requests.Session()
    query_params = {
        "client_id": client_id,
        "refresh_token": token_params['refresh_token'],
        "scope": "openid offline_access",
        "grant_type": "refresh_token",
    }

    endpoint = '/token'
    authheaders = {'Content-type': 'application/x-www-form-urlencoded'}
    authdata = urllib.parse.urlencode(query_params)
    print(f"\n#### {endpoint}: {authdata}\n")
    response = session.post(auth_url + endpoint, data=authdata,
        headers=authheaders, allow_redirects=False)

    if response.status_code < 200 or response.status_code > 299:
        print(response.text)
        exit(1)
    r = json.loads(response.text)
    token_params['access_token'] = r['access_token']
    headers['Authorization'] = f'Bearer {token_params["access_token"]}'

else:
    # Recommended method for python: use requests-oauthlib.  After the session
    # is created, each session.get() or session.post() will automatically
    # use the refresh token to refresh the access token as needed.
    session = OAuth2Session(client_id=client_id,
            token=token_params,
            auto_refresh_url=(auth_url+'/token'),
            auto_refresh_kwargs={'client_id':client_id},
            token_updater=token_updater)


print("Request headers:  %r" % (headers,))
print("Request data:  %r" % (data,))
print()

# Make the request
response = session.get(api_url + "/measurement", data=data, headers=headers, verify=verify_ssl)
print("\x1b[31mHTTP response status: %r\x1b[m" % (response.status_code,))
print("HTTP response headers: %r" % (response.headers,))
print("HTTP response text:")
print(response.text)

