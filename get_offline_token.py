#!/usr/bin/env python3
# python character encoding: utf-8
# Usage: get_offline_token.py {refresh_token_file}

import sys
import os
import time
import requests
import argparse

DEFAULT_REALM = 'CAIDA'
DEFAULT_SCOPE = "openid offline_access"

# Prompt the user to visit a URL to create an offline token.  Then fetch it
# from the auth server.
def auth_device_flow(auth_url, client_id, scope):
    rs = requests.Session() # session for getting refresh token
    response = rs.post(auth_url + "/auth/device",
        data={ "client_id": client_id, "scope": scope },
        allow_redirects=False)
    if response.status_code != 200:
        print(f"\nStatus: {response.status_code}\n{response.text}")
        return False
    dev_res = response.json()
    expires = time.time() + dev_res['expires_in']
    print("\nTo authorize this client, use any web brower to visit:\n   ",
            dev_res['verification_uri_complete'])
    print("\nWaiting for authorization...", end="", flush=True)
    while True:
        time.sleep(dev_res['interval'])
        print(".", end="", flush=True)
        response = rs.post(auth_url + "/token", data={
            "client_id": client_id,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": dev_res['device_code'],
            })
        token_res = response.json()
        if response.status_code == 400 and \
                token_res["error"] == "authorization_pending":
            continue
        print()
        if response.status_code == 200:
            update_token_info(token_res)
            return True
        print(f"\nStatus: {response.status_code}\n{response.text}")
        return False

def default_auth_url(realm):
    return f'https://auth.caida.org/realms/{realm}/protocol/openid-connect'

parser = argparse.ArgumentParser(description=
    "Get an offline token")
parser.add_argument("client_id",
    help=f"OIDC client id")
parser.add_argument("token_file",
    nargs='?',
    help="name of offline token file (default: {CLIENT_ID}.tok)")
parser.add_argument("--realm", "-r",
    metavar='REALM', default=DEFAULT_REALM,
    help=f"Authorization realm (default: {DEFAULT_REALM})")
parser.add_argument("--auth_url", "-a",
    metavar='AUTH_URL',
    help=f"Authorization URL (default: {default_auth_url('{REALM}')})")
parser.add_argument("--scope", "-s",
    metavar='SCOPE', default=DEFAULT_SCOPE,
    help=f"Authorization scope (default: {DEFAULT_SCOPE})")
args = parser.parse_args()

if not args.token_file:
    args.token_file = args.client_id + ".tok"
if not args.auth_url:
    args.auth_url = default_auth_url(args.realm)

def update_token_info(new_token_info):
    # Save the received refresh token for reuse
    os.umask(0o077)
    with open(args.token_file, "w") as f:
        f.write(new_token_info['refresh_token'])

if not auth_device_flow(args.auth_url, args.client_id, args.scope):
    sys.exit(1)
print(f"Saved token to {args.token_file}")
