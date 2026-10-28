"""Where TurtleMaxxxing keeps its data, and the address it answers on.

The data folder lives outside the repo, in the user's local app-data folder,
so it is never committed and never sits inside a folder shared with an AI tool.

Address settings live in <data folder>/settings.json:

    {"port": 8765, "hostname": "turtle.localhost"}

- port: chosen at setup by `turtlemaxxxing --find-port`, which scans for a free one.
- hostname: the friendly name in the address bar. Browsers send every
  *.localhost name to this computer with no setup, so http://turtle.localhost:8765
  works out of the box. Only "localhost" or names ending in ".localhost" are
  allowed, so the app can never claim a real internet name.

Environment variables override the file: TURTLE_DATA_DIR, TURTLE_PORT, TURTLE_HOSTNAME.
"""

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

APP_NAME = "TurtleMaxxxing"

# Localhost only. The app must never listen on a network-reachable address;
# phone access (M5) goes through Tailscale, not by opening this up.
HOST = "127.0.0.1"

DEFAULT_PORT = 8765
DEFAULT_HOSTNAME = "turtle.localhost"

_LABEL = r"[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?"
_HOSTNAME_RE = re.compile(rf"^(localhost|({_LABEL}\.)+localhost)$")


def data_dir() -> Path:
    override = os.environ.get("TURTLE_DATA_DIR")
    if override:
        path = Path(override)
    elif os.name == "nt":
        local = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        path = Path(local) / APP_NAME
    else:
        share = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
        path = Path(share) / APP_NAME.lower()
    path.mkdir(parents=True, exist_ok=True)
    return path


def db_path() -> Path:
    return data_dir() / "turtle.db"


def backups_dir() -> Path:
    path = data_dir() / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


def settings_path() -> Path:
    return data_dir() / "settings.json"


def valid_hostname(name: str) -> bool:
    return bool(_HOSTNAME_RE.match(name))


def valid_port(port: int) -> bool:
    return 1024 <= port <= 65535


@dataclass(frozen=True)
class Settings:
    port: int = DEFAULT_PORT
    hostname: str = DEFAULT_HOSTNAME

    @property
    def url(self) -> str:
        return f"http://{self.hostname}:{self.port}"

    @property
    def allowed_hosts(self) -> set[str]:
        """Names the server answers to. Anything else is refused (see security.py)."""
        return {self.hostname, "localhost", HOST}


def load_settings() -> Settings:
    raw: dict = {}
    path = settings_path()
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raw = {}
    port = int(os.environ.get("TURTLE_PORT") or raw.get("port") or DEFAULT_PORT)
    hostname = (os.environ.get("TURTLE_HOSTNAME") or raw.get("hostname") or DEFAULT_HOSTNAME).lower()
    if not valid_port(port):
        raise ValueError(f"port must be between 1024 and 65535, got {port}")
    if not valid_hostname(hostname):
        raise ValueError(f"hostname must be 'localhost' or end in '.localhost', got {hostname!r}")
    return Settings(port=port, hostname=hostname)


def save_settings(settings: Settings) -> Path:
    path = settings_path()
    path.write_text(
        json.dumps({"port": settings.port, "hostname": settings.hostname}, indent=2) + "\n",
        encoding="utf-8",
    )
    return path
