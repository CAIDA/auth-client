# CAIDA OIDC client

Simple command-line tools for accessing protected CAIDA services.
These can be used directly as-is, or as an example for writing your own clients.

To find the client_id for a particular service, see the documentation for that service.

## Installation

```
python3 -m pip install git+https://github.org/CAIDA/auth/client.git
```
For more information, see the
[Python packaging guide](https://packaging.python.org/en/latest/tutorials/installing-packages/).

## `get_offline_token`
Get access and refresh tokens for use with `offline_query` or another client
that connects to a protected CAIDA service.

Typical usage:
```
get_offline_token myapp-offline
```
This will instruct you to visit a URL in a browser, where you can sign in to
the CAIDA SSO system.  Once you have done that, the script will store an
access token and offline refresh token for client `myapp-offline` in the file
`myapp-offline.token`.

Run `get_offline_token --help` for more information.

## `offline_query`
Make an HTTP request to a protected CAIDA service.

Typical usage:
```
offline_query -t myapp-offline.token myapp-offline https://api.myapp.caida.org/v1/foo
```
This will use the OIDC access token stored in `myapp-offline.token` to query
the given URL.
But if the access token is expired, it will first use the refresh token
to fetch an access token from the authorization server, and store the new
access token in the file.

Run `offline_query --help` for more information.
