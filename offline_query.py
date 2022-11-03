#!/usr/bin/env python3
# python character encoding: utf-8
# Usage: offline_query.py [{refresh_token_file}]

import sys
import requests
from requests_oauthlib import OAuth2Session

# authorization parameters
auth_url = 'https://auth.caida.org/realms/CAIDA_TEST/protocol/openid-connect'
client_id = "river-offline"
scope = "openid offline_access"
manual_auth = False

# service parameters
api_url = "https://river.caida.org:8081/test"
verify_ssl = True  # True normally; False for testing with self-signed cert


def update_token_info(new_token_info):
    token_info.clear()
    token_info.update(new_token_info)

data = b"{foo:'bar'}"
headers = {
    'Content-type': 'application/json; charset=utf-8'
}

token_info = {
    'access_token': 'dummy value for oauthlib',
    'refresh_token': None,
    'expires_in': '-1' # tell OAuth2Session: access_token needs to be refreshed
}

token_filename = sys.argv[1]
with open(token_filename, "r") as f:
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
        "client_id": client_id,
        "refresh_token": token_info['refresh_token'],
        "scope": scope,
        "grant_type": "refresh_token",
    }

    endpoint = '/token'
    authheaders = {'Content-type': 'application/x-www-form-urlencoded'}
    response = session.post(auth_url + endpoint, data=authdata,
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

    session = OAuth2Session(client_id=client_id,
            token=token_info,
            auto_refresh_url=(auth_url+'/token'),
            auto_refresh_kwargs={'client_id':client_id},
            token_updater=update_token_info)


print("Request headers:  %r" % (headers,))
print("Request data:  %r" % (data,))
print()

# Make the request
response = session.get(api_url + "/measurement", data=data, headers=headers, verify=verify_ssl)
print("\x1b[31mHTTP response status: %r\x1b[m" % (response.status_code,))
print("HTTP response headers: %r" % (response.headers,))
print("HTTP response text:")
print(response.text)

