# macOS System CA Fallback Design

## Problem

The standalone Python client uses `urllib.request`, which relies on Python's
OpenSSL trust configuration. A python.org installation on macOS can report a
default CA path even when that file does not exist. In that state, HTTPS image
requests fail with `CERTIFICATE_VERIFY_FAILED`, while macOS `curl` succeeds by
using the system trust store.

The failure was reproduced with Python 3.13.1. Its configured CA file was
missing. The same request succeeded when `SSL_CERT_FILE=/etc/ssl/cert.pem` was
set, proving that the API, proxy, and request payload were not the cause.

## Design

Add a focused `create_ssl_context()` helper to `generate.py`:

1. Preserve Python's normal behavior when its default CA file or CA directory
   is available.
2. Preserve an explicit `SSL_CERT_FILE` or `SSL_CERT_DIR`; Python remains
   responsible for validating those values.
3. On macOS only, when Python has neither an effective CA file nor CA directory,
   use `/etc/ssl/cert.pem` if that file exists.
4. Otherwise use `ssl.create_default_context()` unchanged.

Create the context once for each generation and pass it to both the generation
request and any subsequent image URL download. Never disable hostname checking
or certificate verification.

## Compatibility

- macOS Python installations with working certificate configuration remain
  unchanged.
- macOS Python installations with a missing default CA file gain a system CA
  fallback.
- Windows and Linux retain their existing Python/OpenSSL behavior.
- The client remains standard-library-only.

## Testing

Unit tests patch platform, environment, default verify paths, and context
creation to verify:

- explicit certificate configuration is preserved;
- a working Python default trust source is preserved;
- `/etc/ssl/cert.pem` is selected only for the affected macOS case;
- other platforms do not receive the macOS fallback.

The existing local HTTP integration suite continues to verify request payload,
response decoding, error handling, and atomic output behavior. A final real API
generation verifies the original failure path end to end.
