#!/usr/bin/env python3
# python character encoding: utf-8

import sys
import os
import time
import argparse
import json
import requests
import getpass

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
            save_tokens(token_res)
            return True
        print(f"\nStatus: {response.status_code}\n{response.text}")
        return False

def auth_login_flow(auth_url, client_id, scope):
    password = getpass.getpass(prompt=f'Password for {g.args.login} at {g.args.realm}: ')
    authdata = {
        "client_id": client_id,
        "scope": scope,
        "username": g.args.login,
        "password": password,
        "grant_type": "password",
    }
    rs = requests.Session() # session for getting refresh token
    authheaders = {'Content-type': 'application/x-www-form-urlencoded'}
    response = rs.post(g.args.auth_url + '/token', data=authdata,
        headers=authheaders, allow_redirects=False, verify=g.args.ssl_verify)
    token_res = response.json()
    if response.status_code == 200:
        save_tokens(token_res)
        return True
    print(f"\nStatus: {response.status_code}\n{response.text}")
    return False

def default_auth_url(realm):
    return f'https://auth.caida.org/realms/{realm}/protocol/openid-connect'

def save_tokens(token_info):
    oldmask = os.umask(0o077)
    if "expires_at" not in token_info and "expires_in" in token_info:
        token_info["expires_at"] = time.time() + token_info["expires_in"]
    with open(g.args.token_file, "w") as f:
        json.dump(token_info, f)
    os.umask(oldmask)

def main():
    parser = argparse.ArgumentParser(
        description="Get OIDC access and refresh tokens for use with "
            "`sso_query` or another client that connects to a service "
            "protected by OIDC.",
        epilog="There are two authentication methods: "
            "Device Flow (the default), where you will be instructed to "
            "visit a URL in a browser and sign in to the authentication "
            "system there; and Login (with the --login option), where you "
            "will be prompted for a password locally. Most services allow "
            "only one of these methods. After you have authenticated, SSO "
            "tokens will be saved to TOKEN_FILE.")
    parser.add_argument("client_id",
        metavar='CLIENT_ID',
        help=f"OIDC client id (e.g. 'foobar-offline')")
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
    parser.add_argument("-l", "--login",
        metavar='USERNAME',
        help=f"Login as USERNAME")
    parser.add_argument("--no-verify",
        dest='ssl_verify', default=True, action='store_false',
        help=f"Disable SSL host verification")
    g.args = parser.parse_args()

    if g.args.token_file is None:
        g.args.token_file = g.args.client_id + ".token"
    if g.args.auth_url is None:
        g.args.auth_url = default_auth_url(g.args.realm)

    if g.args.login:
        auth = auth_login_flow
    else:
        auth = auth_device_flow

    if not auth(g.args.auth_url, g.args.client_id, g.args.scope):
        sys.exit(1)
    print(f"Saved token to {g.args.token_file}")

if __name__ == '__main__':
    main()

