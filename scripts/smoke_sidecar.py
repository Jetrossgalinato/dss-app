from __future__ import annotations

import http.client
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]


def available_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def request(port: int, path: str, token: str | None = None) -> tuple[int, dict]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    headers = {"X-DSS-Token": token} if token else {}
    connection.request("GET", path, headers=headers)
    response = connection.getresponse()
    body = json.loads(response.read().decode("utf-8"))
    connection.close()
    return response.status, body


def main() -> None:
    executable = (
        ROOT
        / "backend"
        / "dist"
        / "dss-backend"
        / ("dss-backend.exe" if sys.platform == "win32" else "dss-backend")
    )
    if not executable.exists():
        raise SystemExit(f"Sidecar executable not found: {executable}")

    with tempfile.TemporaryDirectory() as temporary_directory:
        temporary = Path(temporary_directory)
        port = available_port()
        token = "desktop-smoke-token"
        process = subprocess.Popen(
            [
                str(executable),
                "--database",
                str(temporary / "enrollment.sqlite3"),
                "--port",
                str(port),
                "--token",
                token,
                "--log-file",
                str(temporary / "backend.log"),
            ]
        )
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"Sidecar exited with code {process.returncode}")
                try:
                    status, body = request(port, "/health")
                    if status == 200 and body.get("database") == "ready":
                        break
                except (ConnectionError, OSError, TimeoutError):
                    time.sleep(0.2)
            else:
                raise RuntimeError("Sidecar health check timed out")

            unauthorized, _ = request(port, "/api/enrollments")
            authorized, body = request(port, "/api/enrollments", token)
            if unauthorized != 401 or authorized != 200 or body.get("total") != 0:
                raise RuntimeError("Sidecar API authentication smoke test failed")
            if not (temporary / "enrollment.sqlite3").exists():
                raise RuntimeError("Sidecar did not create its persistent database")
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == "__main__":
    main()
