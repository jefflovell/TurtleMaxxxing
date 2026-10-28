"""Command line for TurtleMaxxxing.

    turtlemaxxxing                 start the app
    turtlemaxxxing --find-port     scan for a free local port and save it
    turtlemaxxxing --hostname NAME set the friendly address (must end in .localhost)
    turtlemaxxxing --demo          start on a throwaway folder of fictional demo data
"""

import argparse
import atexit
import os
import shutil
import sys
import tempfile
from datetime import date

TURTLE = r"""
          ________       ___
       .-'  /\  /\'-.   / o \
      /  /\/  \/  \/ \_/  __/
     |  /  \  /\  /  |___/
      \/____\/__\/__/
       |_|  |_|  |_|
"""


def _configure(args: argparse.Namespace) -> int:
    from . import config, ports

    current = config.load_settings()
    port, hostname = current.port, current.hostname
    if args.hostname:
        hostname = args.hostname.lower()
        if not config.valid_hostname(hostname):
            print(f"✗ {hostname!r} won't work. Use a name ending in .localhost, e.g. turtle.localhost")
            return 2
    if args.find_port:
        found = ports.find_free()
        if found is None:
            print("✗ No free port found in 8765-8799. Close another app, or set one with TURTLE_PORT.")
            return 1
        port = found
        print(f"✓ Port {port} is free.")
    path = config.save_settings(config.Settings(port=port, hostname=hostname))
    print(f"✓ Saved to {path}")
    print(f"  TurtleMaxxxing will open at http://{hostname}:{port}")
    return 0


def _serve(demo: bool) -> int:
    import uvicorn

    if demo:
        throwaway = tempfile.mkdtemp(prefix="turtlemaxxxing-demo-")
        os.environ["TURTLE_DATA_DIR"] = throwaway
        atexit.register(shutil.rmtree, throwaway, ignore_errors=True)

    from . import config, db, demo as demo_data, ports
    from .app import create_app

    settings = config.load_settings()
    if demo:
        conn = db.connect(config.db_path())
        db.migrate(conn)
        demo_data.seed(conn, date.today())
        conn.close()

    if not ports.is_free(settings.port):
        print(f"✗ Port {settings.port} is already in use. TurtleMaxxxing may already be running:")
        print(f"  try {settings.url}")
        print("  Or pick another port:  uv run turtlemaxxxing --find-port")
        print("  More help: docs/troubleshooting/app-wont-start.md")
        return 1

    print(TURTLE)
    print(f"TurtleMaxxxing is running at  {settings.url}")
    print(f"               (also works at http://{config.HOST}:{settings.port})")
    if demo:
        print("DEMO MODE: fictional data in a throwaway folder. Nothing you do here is kept.")
    else:
        print(f"Your data lives in {config.data_dir()}")
    print("Press Ctrl+C to stop.\n")
    uvicorn.run(create_app(settings=settings), host=config.HOST, port=settings.port, log_level="warning")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="turtlemaxxxing", description="Local-first personal assistant. 🐢")
    parser.add_argument("--find-port", action="store_true", help="scan for a free local port and save it")
    parser.add_argument("--hostname", help="friendly address to save, e.g. turtle.localhost")
    parser.add_argument("--demo", action="store_true", help="run with fictional data in a throwaway folder")
    args = parser.parse_args(argv)

    if args.find_port or args.hostname:
        sys.exit(_configure(args))
    sys.exit(_serve(args.demo))


if __name__ == "__main__":
    main()
