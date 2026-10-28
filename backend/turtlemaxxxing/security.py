"""Protects the local server from websites open in the same browser.

A server on 127.0.0.1 is unreachable from the internet, but any web page you
visit runs inside your browser, on your computer. Two classic tricks let a
malicious page poke at local servers:

1. DNS rebinding: evil.example re-points itself to 127.0.0.1 so the page
   can read local responses. Blocked by the Host check: we only answer to
   our own names (turtle.localhost, localhost, 127.0.0.1).
2. Cross-site requests (CSRF): a page silently submits a form to
   http://127.0.0.1:8765/api/... to change data. Blocked by the Origin check:
   browsers label every cross-site request with its Origin, and we refuse
   changes from any origin that isn't ours.

We send no CORS headers, so other sites can't read our responses either.
Tools without a browser (curl, scripts, AI agents on this computer) send no
Origin header and are allowed, since they already run on this machine.
"""

from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _hostname(value: str) -> str:
    """'turtle.localhost:8765' -> 'turtle.localhost'; '[::1]:8765' -> '::1'."""
    return (urlsplit(f"//{value}").hostname or "").lower()


def install(app: FastAPI, allowed_hosts: set[str]) -> None:
    allowed = {h.lower() for h in allowed_hosts}

    @app.middleware("http")
    async def local_only(request: Request, call_next):
        host = _hostname(request.headers.get("host", ""))
        if host not in allowed:
            return JSONResponse({"detail": "Unknown host. TurtleMaxxxing only answers to its own address."}, status_code=400)

        if request.method in UNSAFE_METHODS:
            origin = request.headers.get("origin")
            if origin is not None:
                origin_host = (urlsplit(origin).hostname or "").lower() if origin != "null" else ""
                if origin_host not in allowed:
                    return JSONResponse({"detail": "Cross-site request refused."}, status_code=403)
            if request.headers.get("sec-fetch-site") == "cross-site":
                return JSONResponse({"detail": "Cross-site request refused."}, status_code=403)

        return await call_next(request)
