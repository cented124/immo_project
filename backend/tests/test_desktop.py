"""Desktop boundaries: no live mail/bot, database or user's processes."""

import http.client
import importlib.util
import io
import json
from pathlib import Path
import sys
import threading
from email.message import Message
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import desktop_proxy as proxy

spec = importlib.util.spec_from_file_location(
    "desktop_controller", SCRIPTS / "desktop.py"
)
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)


def body(raw, headers, maximum=100):
    class Request:
        rfile = io.BytesIO(raw)

    request = Request()
    request.headers = Message()
    for key, value in headers:
        request.headers.add_header(key, value)
    return proxy.read_body(request, maximum)


def test_desktop_bounded_chunked_uploads_and_ambiguous_lengths():
    assert (
        body(b"3\r\nabc\r\n2\r\nde\r\n0\r\n\r\n", [("Transfer-Encoding", "chunked")])
        == b"abcde"
    )
    for raw, headers, expected in [
        (b"", [("Content-Length", "101")], 413),
        (b"", [("Content-Length", "1"), ("Content-Length", "1")], 400),
        (b"", [("Content-Length", "1"), ("Transfer-Encoding", "chunked")], 400),
        (b"a", [("Content-Length", "3")], 400),
        (b"-1\r\n", [("Transfer-Encoding", "chunked")], 400),
        (b"65\r\n", [("Transfer-Encoding", "chunked")], 413),
    ]:
        with pytest.raises(proxy.RequestError) as error:
            body(raw, headers)
        assert error.value.status == expected


@pytest.fixture
def gateway():
    rows = []
    stopped = threading.Event()
    server = proxy.Gateway(
        0,
        instance="test-instance",
        control="private-control",
        setup="setup-once",
        create_admin=lambda data: rows.append(data),
        has_admin=lambda: bool(rows),
        stop=stopped,
    )
    server.ready = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server, rows, stopped
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


def request(server, method, path, data=None, headers=None):
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
    try:
        connection.request(
            method,
            path,
            body=json.dumps(data) if data is not None else None,
            headers=headers or {},
        )
        response = connection.getresponse()
        return response.status, response.read(), response.getheaders()
    finally:
        connection.close()


def test_first_admin_requires_secret_valid_origin_and_cannot_be_repeated(gateway):
    server, rows, _ = gateway
    assert request(server, "GET", "/einrichten")[0] == 200
    assert request(server, "POST", "/__desktop/setup", {})[0] == 403
    headers = {"X-Raumwerk-Setup": "setup-once", "Origin": "https://untrusted.example"}
    assert request(server, "POST", "/__desktop/setup", {}, headers)[0] == 403
    headers.pop("Origin")
    assert (
        request(
            server, "POST", "/__desktop/setup", {"email": "test@example.com"}, headers
        )[0]
        == 201
    )
    assert len(rows) == 1 and server.setup == ""
    assert request(server, "POST", "/__desktop/setup", {}, headers)[0] == 409
    assert request(server, "GET", "/einrichten")[0] == 409


def test_stop_ownership_hostname_and_diagnostics_do_not_expose_keys(gateway):
    server, _, stopped = gateway
    status, raw, _ = request(server, "GET", "/__desktop/health")
    assert status == 200 and b"private-control" not in raw and b"setup-once" not in raw
    assert (
        request(
            server, "GET", "/__desktop/health", headers={"Host": "rebinding.example"}
        )[0]
        == 403
    )
    assert request(server, "POST", "/__desktop/stop")[0] == 403
    assert not stopped.is_set()
    assert (
        request(
            server,
            "POST",
            "/__desktop/stop",
            headers={"X-Raumwerk-Control": "private-control"},
        )[0]
        == 200
    )
    assert stopped.is_set()


def test_proxy_preserves_downloads_cookies_bodies_and_private_file_denial(gateway):
    server, _, _ = gateway

    class Upstream(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            data = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            self.send_response(202)
            self.send_header("Set-Cookie", "a=1; HttpOnly")
            self.send_header("Set-Cookie", "b=2; HttpOnly")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            self.send_response(401 if self.path == "/api/admin/files/private" else 200)
            self.send_header("Content-Disposition", 'attachment; filename="test.pdf"')
            self.end_headers()
            self.wfile.write(b"%PDF-test")

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
    server.api_port = server.web_port = upstream.server_port
    thread = threading.Thread(target=upstream.serve_forever, daemon=True)
    thread.start()
    try:
        status, raw, headers = request(
            server, "POST", "/api/public/inquiries", {"message": "Grüße"}
        )
        assert status == 202 and json.loads(raw)["message"] == "Grüße"
        assert len([h for h in headers if h[0].lower() == "set-cookie"]) == 2
        status, raw, headers = request(server, "GET", "/api/public/files/demo")
        assert (
            status == 200
            and raw == b"%PDF-test"
            and any(h[0].lower() == "content-disposition" for h in headers)
        )
        assert request(server, "GET", "/api/admin/files/private")[0] == 401
    finally:
        upstream.shutdown()
        upstream.server_close()
        thread.join(timeout=5)


def test_process_lock_is_released_and_does_not_delete_existing_data(tmp_path):
    path = tmp_path / "install.lock"
    with controller.FileLock(path):
        with pytest.raises(RuntimeError):
            with controller.FileLock(path):
                pass
    with controller.FileLock(path):
        pass
    assert path.is_file()


def test_non_loopback_control_state_is_never_contacted():
    with pytest.raises(ValueError):
        controller.local_call(
            {"url": "https://example.com", "control": "never-send"},
            "/__desktop/stop",
            "POST",
        )
