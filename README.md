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
Get an offline token for use with `offline_query` or another client that connects to a
protected CAIDA service.

Typical usage:
```
get_offline_token myapp-offline
```
This will instruct you to visit a URL in a browser, where you can sign in to the CAIDA SSO system.
Once you have done that, the script will store an offline token for client `myapp-offline`
in the file `myapp-offline.tok`.

Run `get_offline_token --help` for more information.

## `offline_query`
Make an HTTP request to a protected CAIDA service.

Typical usage:
```
offline_query -t myapp-offline.tok myapp-offline https://api.myapp.caida.org/v1/foo
```
This will use the offline token stored in `myapp-offline.tok` to fetch an OIDC access token,
and then use that access token to query the given URL.

Run `offline_query --help` for more information.
