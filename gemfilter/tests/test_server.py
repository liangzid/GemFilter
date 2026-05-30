"""
Smoke tests for the GemFilter HTTP server handler.
"""

import json
import threading
from http.server import HTTPServer
from urllib.request import ProxyHandler, Request, build_opener

from gemfilter import SandFilter
from gemfilter.server.main import FilterHandler


def _run_test_server():
    sf = SandFilter()
    sf.enable_rules("email")
    FilterHandler.gemfilter = sf
    server = HTTPServer(("127.0.0.1", 0), FilterHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_port}"


def _post_json(url, payload):
    request = Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    opener = build_opener(ProxyHandler({}))
    with opener.open(request, timeout=5) as response:
        return json.loads(response.read().decode())


def test_filter_endpoint_omits_raw_matches_by_default():
    server, base_url = _run_test_server()
    try:
        response = _post_json(
            f"{base_url}/filter",
            {"text": "Contact user@example.com"},
        )

        assert "user@example.com" not in json.dumps(response)
        assert "match_length" in response["detections"][0]
        assert "match" not in response["detections"][0]
    finally:
        server.shutdown()
        server.server_close()


def test_filter_endpoint_can_include_matches_with_unsafe_flag():
    server, base_url = _run_test_server()
    try:
        response = _post_json(
            f"{base_url}/filter",
            {
                "text": "Contact user@example.com",
                "unsafe_include_matches": True,
            },
        )

        assert response["detections"][0]["match"] == "user@example.com"
    finally:
        server.shutdown()
        server.server_close()
