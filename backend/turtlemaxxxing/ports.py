"""Finding a free local port at setup time.

Ports are only ever checked on 127.0.0.1. Nothing is opened to the network.
"""

import socket
from collections.abc import Iterable

from .config import DEFAULT_PORT, HOST

# Ports other tools commonly use; skip them to avoid surprise clashes later.
COMMON_DEV_PORTS = {3000, 3001, 4200, 5000, 5173, 5432, 6379, 8000, 8080, 8081, 8443, 8888, 9000}

# Default first, then a short, memorable range.
CANDIDATES = [DEFAULT_PORT, *range(8766, 8800)]


def is_free(port: int) -> bool:
    """Free means nothing answers on it and we can bind it. Both checks matter:
    on Windows, a program listening on all addresses doesn't always block a
    bind to 127.0.0.1, but it does answer a connection."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.3)
        if probe.connect_ex((HOST, port)) == 0:
            return False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((HOST, port))
        except OSError:
            return False
    return True


def find_free(candidates: Iterable[int] = CANDIDATES) -> int | None:
    for port in candidates:
        if port not in COMMON_DEV_PORTS and is_free(port):
            return port
    return None
