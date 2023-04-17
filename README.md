# CAIDA OIDC client

Simple command-line tools for accessing protected CAIDA services.
These can be used directly as-is, or as an example for writing your own clients.

To find the client_id for a particular service, see the documentation for that service.

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

### `get_offline_token`
Get access and refresh tokens for use with `offline_query` or another client
that connects to a protected CAIDA service.

Typical usage:
```
get_offline_token $client_id
```

where `$client_id` is the client id for the service you are trying to use, e.g. `myapp-offline`.
This will instruct you to visit a URL in a browser, where you can sign in to
the CAIDA SSO system.  Once you have done that, the script will store an
access token and offline refresh token for `$client_id` in the file
`$client_id.token`.

The offline token will expire if not used within 30 days of issue,
but once it is used, it will remain valid indefinitely,
until explicitly revoked.

Run `get_offline_token --help` for more information.

### `offline_query`
Make an HTTP request to a protected CAIDA service.

Typical usage:
```
offline_query -t $client_id.token $client_id $service_url
```
where `$client_id` is the client id for the service you are trying to use, e.g. `myapp-offline`,
and `$service_url` is the url of the service you are trying to use, e.g. `https://api.myapp.caida.org/v1/foo`.
This will use the OIDC access token stored in `$client_id.token` to query
the given URL.
But if the access token is expired, it will first use the refresh token
to fetch an access token from the authorization server, and store the new
access token in the file.

Run `offline_query --help` for more information.
