import json
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from threading import Thread

import pytest

from service import Settings, make_handler


@pytest.fixture
def api(monkeypatch):
    monkeypatch.setenv("APP_VERSION", "test.6")
    monkeypatch.setenv("SERVICE_PORT", "8080")
    monkeypatch.setenv("IMAGE_HEALTH_CODE", "200")
    with ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Settings.from_env())) as server:
        thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05})
        thread.start()
        try:
            yield server.server_port
        finally:
            server.shutdown()
            thread.join()


def test_health_contract(api):
    conn = HTTPConnection("127.0.0.1", api, timeout=2)
    try:
        conn.request("GET", "/health")
        response = conn.getresponse()
        assert response.status == 200
        assert json.load(response) == {"state": "ready"}
    finally:
        conn.close()


@pytest.mark.parametrize(
    ("path", "status", "body"),
    [
        ("/version", 200, {"version": "test.6"}),
        ("/missing", 404, {"error": "not found"}),
    ],
)
def test_routes(api, path, status, body):
    conn = HTTPConnection("127.0.0.1", api, timeout=2)
    try:
        conn.request("GET", path)
        response = conn.getresponse()
        assert response.status == status
        assert json.load(response) == body
    finally:
        conn.close()


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("SERVICE_PORT", "0"),
        ("SERVICE_PORT", "70000"),
        ("SERVICE_PORT", "abc"),
        ("APP_VERSION", "  "),
        ("IMAGE_HEALTH_CODE", "204"),
    ],
)
def test_invalid_configuration(monkeypatch, key, value):
    monkeypatch.setenv(key, value)
    with pytest.raises(ValueError):
        Settings.from_env()