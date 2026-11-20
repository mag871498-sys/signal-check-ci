import json
import os
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


@dataclass(frozen=True)
class Settings:
    port: int
    version: str
    health_code: int

    @classmethod
    def from_env(cls):
        port = int(os.getenv("SERVICE_PORT", "8080"))
        version = os.getenv("APP_VERSION", "dev").strip()
        health_code = int(os.getenv("IMAGE_HEALTH_CODE", "200"))
        if not 1 <= port <= 65535:
            raise ValueError("SERVICE_PORT must be in 1..65535")
        if not version:
            raise ValueError("APP_VERSION must not be empty")
        if health_code not in (200, 503):
            raise ValueError("IMAGE_HEALTH_CODE must be 200 or 503")
        return cls(port, version, health_code)


def make_handler(settings):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/health":
                code = settings.health_code
                body = {"state": "ready" if code == 200 else "unavailable"}
            elif self.path == "/version":
                code, body = 200, {"version": settings.version}
            else:
                code, body = 404, {"error": "not found"}

            payload = json.dumps(body).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    return Handler


if __name__ == "__main__":
    settings = Settings.from_env()
    with ThreadingHTTPServer(("0.0.0.0", settings.port), make_handler(settings)) as server:
        print(f"Signal Check {settings.version} listens on {settings.port}", flush=True)
        server.serve_forever()