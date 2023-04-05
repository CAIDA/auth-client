#!/usr/bin/env python3
# python character encoding: utf-8

import sys
import os
import time
import argparse
import requests

DEFAULT_REALM = 'CAIDA'
DEFAULT_SCOPE = "openid offline_access"

# Prompt the user to visit a URL to create an offline token.  Then poll
# the auth server until it's available.
def auth_device_flow(auth_url, client_id, scope):
    rs = requests.Session() # session for getting refresh token
    response = rs.post(auth_url + "/auth/device",
        data={ "client_id": client_id, "scope": scope },
        allow_redirects=False, verify=args.ssl_verify)
    if response.status_code != 200:
        print(f"\nStatus: {response.status_code}\n{response.text}")
        return False
    dev_res = response.json()
    print("\nTo authorize the creation of an offline token, "
            "use any web browser on any device to visit:\n   ",
            dev_res['verification_uri_complete'])
    print("\nWaiting for authorization...", end="", flush=True)
    while True:
        time.sleep(dev_res['interval'])
        print(".", end="", flush=True)
        response = rs.post(auth_url + "/token", data={
            "client_id": client_id,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": dev_res['device_code'],
            }, verify=args.ssl_verify)
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
    metavar='CLIENT_ID',
    help=f"OIDC client id (e.g. 'myapp-api')")
parser.add_argument("token_file",
    nargs='?', metavar='TOKEN_FILE',
    help="name of file to save offline token (default: {CLIENT_ID}.tok)")
parser.add_argument("-r", "--realm",
    default=DEFAULT_REALM,
    help=f"Authorization realm (default: {DEFAULT_REALM})")
parser.add_argument("-a", "--auth-url",
    help=f"Authorization URL (default: {default_auth_url('{REALM}')})")
parser.add_argument("-s", "--scope",
    default=DEFAULT_SCOPE,
    help=f"Authorization scope (default: {DEFAULT_SCOPE})")
parser.add_argument("--no-verify",
    dest='ssl_verify', default=True, action='store_false',
    help=f"Disable SSL host verification")
args = parser.parse_args()

if args.token_file is None:
    args.token_file = args.client_id + ".tok"
if args.auth_url is None:
    args.auth_url = default_auth_url(args.realm)

def update_token_info(new_token_info):
    # Save the received refresh token for reuse
    os.umask(0o077)
    with open(args.token_file, "w") as f:
        f.write(new_token_info['refresh_token'])

if not auth_device_flow(args.auth_url, args.client_id, args.scope):
    sys.exit(1)
print(f"Saved token to {args.token_file}")
