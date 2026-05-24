#!/usr/bin/env python3
"""
GemFilter HTTP Server

A simple HTTP server that provides GemFilter as a REST API.
Privacy protection for LLM and AI applications.
"""

import json
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

from gemfilter import SandFilter, FilterResult


class FilterHandler(BaseHTTPRequestHandler):
    """HTTP request handler for GemFilter API."""

    gemfilter: SandFilter = None

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        elif parsed.path == "/rules":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            rules = {
                "enabled": self.gemfilter.get_enabled_rules(),
                "disabled": self.gemfilter.get_disabled_rules(),
            }
            self.wfile.write(json.dumps(rules).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        """Handle POST requests."""
        parsed = urlparse(self.path)
        if parsed.path == "/filter":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
                return

            text = data.get("text", "")
            if not text:
                self.send_error(400, "Missing 'text' field")
                return
            include_matches = bool(data.get("unsafe_include_matches", False))

            # Process the text
            result = self.gemfilter.filter(text)

            # Build response
            response = result.to_dict(include_matches=include_matches)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        elif parsed.path == "/filter/batch":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
                return

            texts = data.get("texts", [])
            if not texts:
                self.send_error(400, "Missing 'texts' field")
                return
            include_matches = bool(data.get("unsafe_include_matches", False))

            results = []
            for text in texts:
                result = self.gemfilter.filter(text)
                results.append(result.to_dict(include_matches=include_matches))

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(results).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Log HTTP requests."""
        print(f"[{self.log_date_time_string()}] {args[0]}")


def run_server(
    host: str = "localhost",
    port: int = 8080,
    config: str = None,
):
    """Run the GemFilter HTTP server.

    Args:
        host: Host to bind to
        port: Port to listen on
        config: Optional config file path
    """
    # Initialize GemFilter
    if config:
        gemfilter = SandFilter.from_config(config)
    else:
        gemfilter = SandFilter()

    FilterHandler.gemfilter = gemfilter

    server = HTTPServer((host, port), FilterHandler)
    print(f"GemFilter server running at http://{host}:{port}")
    print(f"Endpoints:")
    print(f"  GET  /health     - Health check")
    print(f"  GET  /rules     - List enabled/disabled rules")
    print(f"  POST /filter    - Filter single text")
    print(f"  POST /filter/batch - Filter multiple texts")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="GemFilter HTTP Server")
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host to bind to (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to listen on (default: 8080)",
    )
    parser.add_argument(
        "--config",
        help="Path to config file (YAML or JSON)",
    )

    args = parser.parse_args()
    run_server(args.host, args.port, args.config)


if __name__ == "__main__":
    main()
