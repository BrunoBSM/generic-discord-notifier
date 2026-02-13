#!/usr/bin/env python3
"""
Entry point for Discord Notifier Web UI.

Usage:
    python run_web.py                    # Run on localhost:5000
    python run_web.py --host 0.0.0.0     # Allow LAN access
    python run_web.py --port 8080        # Custom port
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Discord Notifier Web UI - Manage notifications via browser"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (use 0.0.0.0 for LAN access). Default: 127.0.0.1"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to listen on. Default: 5000"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (auto-reload on code changes)"
    )
    
    args = parser.parse_args()
    
    # Import here to avoid import errors if dependencies aren't installed
    try:
        from web_ui.app import create_app
    except ImportError as e:
        print(f"Error: Missing dependency - {e}", file=sys.stderr)
        print("Run: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)
    
    app = create_app()
    
    print(f"\n  Discord Notifier Web UI")
    print(f"  ───────────────────────")
    if args.host == "0.0.0.0":
        import socket
        local_ip = socket.gethostbyname(socket.gethostname())
        print(f"  Local:   http://127.0.0.1:{args.port}")
        print(f"  Network: http://{local_ip}:{args.port}")
    else:
        print(f"  Running: http://{args.host}:{args.port}")
    print()
    
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()

