#!/usr/bin/env python3
# python character encoding: utf-8
"""Get OIDC refresh and access tokens"""

import sys
import time
import argparse
import getpass
from collections.abc import Callable
import requests
import caida_oidc_client

DEFAULT_REALM = 'CAIDA'
DEFAULT_SCOPE = ['openid']

class g: # pylint: disable=invalid-name, too-few-public-methods
    """global variables"""
    args = None
    save_tokens: Callable

def auth_device_flow(auth_url, client_id, scope):
    """
    Prompt the user to visit a URL to create a refresh token.  Then poll
    the auth server until it's available.
    """
    rs = requests.Session() # session for getting refresh token
    response = rs.post(auth_url + "/auth/device",
        data={ "client_id": client_id, "scope": scope },
        allow_redirects=False, verify=g.args.ssl_verify)
    if response.status_code != 200:
        print(f"\nStatus: {response.status_code}\n{response.text}")
        return False
    dev_res = response.json()
    tokentype = "an offline refresh" if "offline_access" in g.args.scope \
            else "a refresh"
    print(f"\nTo authorize the creation of {tokentype} token, "
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
            g.save_tokens(token_res)
            return True
        print(f"\nStatus: {response.status_code}\n{response.text}")
        return False

def auth_login_flow(auth_url, client_id, scope):
    """
    Prompt the user for a password and execute a Direct Access.
    """
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
    response = rs.post(auth_url + '/token', data=authdata,
        headers=authheaders, allow_redirects=False, verify=g.args.ssl_verify)
    token_res = response.json()
    if response.status_code == 200:
        g.save_tokens(token_res)
        return True
    print(f"\nStatus: {response.status_code}\n{response.text}")
    return False

def default_auth_url(realm):
    return f'https://auth.caida.org/realms/{realm}/protocol/openid-connect'

def main():
    """Main"""
    parser = argparse.ArgumentParser(
        description="Get OIDC access and refresh tokens for use with "
            "`oidc_query` or another client that connects to a service "
            "protected by OIDC.",
        epilog="There are two authentication methods: "
            "Device Flow (without --login), where you will be instructed to "
            "visit a URL in a browser and sign in to the authentication "
            "system there; and Direct Access (with --login), where "
            "you will be prompted for a password locally. Some services may "
            "not allow every method. After you have authenticated, OIDC "
            "tokens will be saved to TOKEN_FILE.")
    rare = parser.add_argument_group("rarely used options")
    parser.add_argument("client_id",
        metavar='CLIENT_ID',
        help="OIDC client id (e.g. 'foobar-offline')")
    parser.add_argument("token_file",
        nargs='?', metavar='TOKEN_FILE',
        help="name of file to save tokens (default: {CLIENT_ID}.token)")
    parser.add_argument("-o", "--offline",
        dest='scope', default=DEFAULT_SCOPE,
        action='append_const', const='offline_access',
        help="Request 'offline' tokens that don't expire when you log out "
            "(equivalent to `--scope offline_access`)")
    parser.add_argument("-l", "--login",
        metavar='USERNAME',
        help="Login as USERNAME")
    parser.add_argument("-s", "--scope",
        action='append', default=DEFAULT_SCOPE,
        help="Space-separated list of authorization scopes "
            "(repeatable) "
            f"('{' '.join(DEFAULT_SCOPE)}' will be added automatically)")
    rare.add_argument("-r", "--realm",
        default=DEFAULT_REALM,
        help=f"Authorization realm (default: {DEFAULT_REALM})")
    rare.add_argument("-a", "--auth-url",
        help=f"Authorization URL (default: {default_auth_url('{REALM}')})")
    rare.add_argument("--no-verify",
        dest='ssl_verify', default=True, action='store_false',
        help="Disable SSL host verification")
    g.args = parser.parse_args()

    if g.args.token_file is None:
        g.args.token_file = g.args.client_id + ".token"
    if g.args.auth_url is None:
        g.args.auth_url = default_auth_url(g.args.realm)

    g.save_tokens = caida_oidc_client.make_save_tokens(g.args.token_file)

    if g.args.login:
        auth = auth_login_flow
    else:
        auth = auth_device_flow

    scope = ' '.join(g.args.scope)

    try:
        if auth(g.args.auth_url, g.args.client_id, scope):
            print(f"Saved token to {g.args.token_file}")
            sys.exit(0)
    except KeyboardInterrupt:
        pass
    sys.exit(1)

if __name__ == '__main__':
    main()
