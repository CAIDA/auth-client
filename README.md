# CAIDA OIDC client

Simple command-line tools for accessing services protected by
[CAIDA SSO](https://www.caida.org/about/sso).
These can be used directly as-is, or as an example for writing your own clients.

To find the client\_id for a particular service, see the documentation for that service.

## Installation

### 1. OPTIONAL: Create a python [virtual environment](https://docs.python.org/3/library/venv.html)
```
python3 -m venv /path/to/new/virtual/environment
source /path/to/new/virtual/environment/bin/activate
```

### 2. Install this package
```
python3 -m pip install git+https://github.com/CAIDA/auth/client.git
```

For more information, see the
[Python packaging guide](https://packaging.python.org/en/latest/tutorials/installing-packages/).

## Usage

### `get_oidc_tokens`
Get access and refresh tokens for use with `oidc_query` or another client
that connects to a protected CAIDA service.

Typical usage:
```
get_oidc_tokens -o $client_id
```

where `$client_id` is the client id for the service you are trying to use, e.g. `foobar-offline`.
This will instruct you to visit a URL in a browser, where you can sign in to
the CAIDA SSO system.  Once you have done that, the script will store an
access token and refresh token for `$client_id` in the file
`$client_id.token`.

Run `get_oidc_tokens --help` for more information.

### `oidc_query`
Make an HTTP request to a protected CAIDA service.

Typical usage:
```
oidc_query $client_id $service_url
```
where `$client_id` is the client id for the service you are trying to use, e.g. `foobar-offline`,
and `$service_url` is the url of the service you are trying to use, e.g. `https://api.foobar.caida.org/v1/foo`.
This will use the OIDC access token stored in the file `$client_id.token` to
query the given URL.
But if the access token is expired, it will first use the refresh token
to fetch an access token from the authorization server, and store the new
access token in the file.

The response from the service will be written to standard output, which you
can easily redirect to a file.
All other diagnostic output from `oidc_query` will be written to standard
error.

Run `oidc_query --help` for more information.
