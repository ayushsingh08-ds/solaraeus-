"""
SOLARAEUS 3D Interactive Simulation Viewer Application
Serves the Three.js WebGL/WebGPU microclimate simulator,
ray-traced shadow engine, and cinematic aerial map interface.
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

PORT = 8080
DIRECTORY = Path(__file__).resolve().parent.parent.parent.parent / "simulation_3d"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

    def end_headers(self):
        # Enable CORS and disable aggressive caching for local simulation development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

def main():
    print("=" * 70)
    print("SOLARAEUS: DATA-DRIVEN 3D CINEMATIC SIMULATION VIEWER")
    print("=" * 70)
    print(f"Serving 3D simulation from: {DIRECTORY}")
    print(f"Local URL: http://localhost:{PORT}/index.html")
    print("Preserves all verified CPU/GPU microclimate and ray-tracing results.")
    print("Press Ctrl+C to terminate the viewer server.")
    print("=" * 70)

    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"Server active on port {PORT}. Opening browser...")
            webbrowser.open(f"http://localhost:{PORT}/index.html")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nViewer server stopped by user.")
    except Exception as e:
        print(f"Error starting viewer server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
