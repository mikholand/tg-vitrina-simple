#!/usr/bin/env python3
"""Drop stored certs for DOMAIN so Traefik re-issues with preferredChain."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ACME_PATH = Path(__import__("os").environ.get("ACME_PATH", "/letsencrypt/acme.json"))
DOMAIN = sys.argv[1] if len(sys.argv) > 1 else "alenazhao.ru"


def domain_matches(entry: dict, domain: str) -> bool:
    d = entry.get("domain") or {}
    if d.get("main") == domain:
        return True
    return domain in (d.get("sans") or [])


def main() -> None:
    data = json.loads(ACME_PATH.read_text())
    resolver = data.get("letsencrypt") or data.get("default") or {}
    certs = resolver.get("Certificates") or []
    kept = [c for c in certs if not domain_matches(c, DOMAIN)]
    removed = len(certs) - len(kept)
    if removed:
        resolver["Certificates"] = kept
        ACME_PATH.write_text(json.dumps(data, indent=2))
    print(f"removed={removed} kept={len(kept)} domain={DOMAIN}")


if __name__ == "__main__":
    main()
