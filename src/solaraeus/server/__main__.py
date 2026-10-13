"""
Entry point for python -m solaraeus.server
"""

import argparse
from solaraeus.server.app import run_server

def main():
    parser = argparse.ArgumentParser(description="Run SOLARAEUS Digital Twin Engine Web Interface")
    parser.add_argument("--host", default="127.0.0.1", help="Host address")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    args = parser.parse_args()
    print(f"\n=======================================================")
    print(f"  SOLARAEUS DIGITAL TWIN ENGINE SERVER")
    print(f"  Interface running at: http://{args.host}:{args.port}")
    print(f"=======================================================\n")
    run_server(host=args.host, port=args.port)

if __name__ == "__main__":
    main()
