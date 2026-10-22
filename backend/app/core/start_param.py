"""Encodes/decodes the Mini App `startapp` deep-link parameter.

Telegram restricts `start_param`/`startapp` to `^[A-Za-z0-9_-]{1,64}$` — no
slashes, no padding `=`, nothing else is legal in that query value. Rather
than inventing a prefix per destination (the old `product_<id>` /
`invite_<token>` scheme, which meant the frontend router guard had to know
every prefix up front — see `frontend/src/app/router/index.ts`'s old
`pendingProductRedirect()`/`redeemPendingInvite()`), the actual app-relative
path itself (e.g. `/product/5`, `/invite/<token>`) is base64url-encoded into
the param. The guard just decodes it and redirects straight to that path —
no per-destination frontend code needed when a new kind of share link shows
up later.

Base64url (`A-Za-z0-9-_`) was picked specifically because it already is a
subset of what `startapp` allows, once the `=` padding is stripped.
"""

import base64


def encode_start_param(path: str) -> str:
    """Base64url-encodes an app-relative path (e.g. `/product/5`) into a
    value legal for Telegram's `startapp`/`start_param`."""
    raw = base64.urlsafe_b64encode(path.encode("utf-8")).rstrip(b"=")
    return raw.decode("ascii")


def decode_start_param(value: str) -> str | None:
    """Inverse of `encode_start_param()` — used by tests to assert the round
    trip rather than hard-coding the encoded form. The frontend has its own
    copy of this (`decodeStartPath()` in `app/router/index.ts`) since it
    decodes client-side, not via a backend call."""
    padding = "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(value + padding).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None
