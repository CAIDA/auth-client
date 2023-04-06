#!/usr/bin/env python3
# python character encoding: utf-8

import sys
import os
import time
import argparse
import requests

DEFAULT_REALM = 'CAIDA'
DEFAULT_SCOPE = "openid offline_access"

class g: # global variables
    args = None

# Prompt the user to visit a URL to create an offline token.  Then poll
# the auth server until it's available.
def auth_device_flow(auth_url, client_id, scope):
    rs = requests.Session() # session for getting refresh token
    response = rs.post(auth_url + "/auth/device",
        data={ "client_id": client_id, "scope": scope },
        allow_redirects=False, verify=g.args.ssl_verify)
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
            }, verify=g.args.ssl_verify)
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

def update_token_info(new_token_info):
    # Save the received refresh token for reuse
    os.umask(0o077)
    with open(g.args.token_file, "w") as f:
        f.write(new_token_info['refresh_token'])

def main():
    parser = argparse.ArgumentParser(description=
        "Get an offline token")
    parser.add_argument("client_id",
        metavar='CLIENT_ID',
        help=f"OIDC client id (e.g. 'myapp-offline')")
    parser.add_argument("token_file",
        nargs='?', metavar='TOKEN_FILE',
        help="name of file to save offline token (default: {CLIENT_ID}.token)")
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
    g.args = parser.parse_args()

    if g.args.token_file is None:
        g.args.token_file = g.args.client_id + ".tok"
    if g.args.auth_url is None:
        g.args.auth_url = default_auth_url(g.args.realm)

    if not auth_device_flow(g.args.auth_url, g.args.client_id, g.args.scope):
        sys.exit(1)
    print(f"Saved token to {g.args.token_file}")

if __name__ == '__main__':
    main()

