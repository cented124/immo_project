"""Loopback-only desktop gateway. No Docker, public listener or external proxy."""

import hmac
import http.client
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

MAX_BODY = 12 * 1024 * 1024
HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "proxy-connection",
}

SETUP_HTML = """<!doctype html><html lang="de"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Raumwerk einrichten</title>
<style>body{font:15px/1.7 system-ui;background:#f4f7f3;color:#23463c;margin:0;padding:40px 20px}
main{max-width:470px;margin:5vh auto;background:white;padding:35px;border:1px solid #dbe4d9;border-radius:12px}
h1{font-size:29px;line-height:1.2}label{display:block;margin:20px 0}input{box-sizing:border-box;width:100%;padding:12px;border:1px solid #ccd9cd;border-radius:5px;font:inherit}
button{background:#244e45;color:white;border:0;padding:14px 20px;border-radius:5px;font:inherit;cursor:pointer}button:disabled{opacity:.5}
#message{white-space:pre-wrap}small{color:#6f8174}</style><main><small>RAUMWERK · LOKALE EINRICHTUNG</small>
<h1>Dein Baukasten.<br>Ohne Docker.</h1><p>Lege einmal deinen Administrator an. Die Daten bleiben auf diesem Computer.</p>
<form id="setup"><label>E-Mail-Adresse<input name="email" type="email" autocomplete="username" required maxlength="254"></label>
<label>Neues Passwort<input name="password" type="password" autocomplete="new-password" minlength="12" maxlength="512" required></label>
<label>Passwort wiederholen<input name="repeat" type="password" autocomplete="new-password" minlength="12" maxlength="512" required></label>
<button>Administrator anlegen</button><p id="message" role="status"></p></form>
<small>Mindestens 12 Zeichen. Es wird kein vorgegebenes Passwort verwendet.</small></main>
<script>const key=location.hash.slice(1);history.replaceState(null,'',location.pathname);
document.querySelector('#setup').addEventListener('submit',async e=>{e.preventDefault();const form=e.currentTarget,button=form.querySelector('button'),message=document.querySelector('#message');const data=Object.fromEntries(new FormData(form));
if(!key){message.textContent='Bitte STARTEN.cmd erneut oeffnen. Der Einrichtungslink fehlt.';return}
if(data.password!==data.repeat){message.textContent='Die Passwoerter stimmen nicht ueberein.';return}
button.disabled=true;try{const response=await fetch('/__desktop/setup',{method:'POST',headers:{'Content-Type':'application/json','X-Raumwerk-Setup':key},body:JSON.stringify(data)});const result=await response.json();if(!response.ok)throw new Error(result.error||'Einrichtung fehlgeschlagen.');form.reset();location.replace('/admin');}catch(error){message.textContent=error.message;button.disabled=false}});</script></html>"""


class RequestError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message


def read_body(handler, maximum=MAX_BODY):
    lengths = handler.headers.get_all("Content-Length", [])
    encoding = handler.headers.get("Transfer-Encoding", "").lower()
    if len(lengths) > 1 or (lengths and encoding):
        raise RequestError(400, "Mehrdeutige Groessenangabe")
    if encoding:
        if encoding != "chunked":
            raise RequestError(400, "Ungueltige Uebertragung")
        data = bytearray()
        while True:
            line = handler.rfile.readline(128)
            if not line.endswith(b"\r\n"):
                raise RequestError(400, "Ungueltiger Datenblock")
            try:
                raw = line[:-2].split(b";", 1)[0]
                if (
                    not raw
                    or len(raw) > 16
                    or any(c not in b"0123456789abcdefABCDEF" for c in raw)
                ):
                    raise ValueError()
                length = int(raw, 16)
            except ValueError:
                raise RequestError(400, "Ungueltiger Datenblock")
            if not length:
                total = 0
                while True:
                    trailer = handler.rfile.readline(8193)
                    total += len(trailer)
                    if total > 8192 or not trailer.endswith(b"\r\n"):
                        raise RequestError(400, "Ungueltiger Abschluss")
                    if trailer == b"\r\n":
                        return bytes(data)
            if len(data) + length > maximum:
                raise RequestError(413, "Datei zu gross (maximal 12 MB pro Anfrage)")
            block = handler.rfile.read(length)
            if len(block) != length or handler.rfile.read(2) != b"\r\n":
                raise RequestError(400, "Unvollstaendige Anfrage")
            data.extend(block)
    try:
        length = int(lengths[0]) if lengths else 0
    except ValueError:
        raise RequestError(400, "Ungueltige Groessenangabe")
    if length < 0:
        raise RequestError(400, "Ungueltige Groessenangabe")
    if length > maximum:
        raise RequestError(413, "Datei zu gross (maximal 12 MB pro Anfrage)")
    raw = handler.rfile.read(length)
    if len(raw) != length:
        raise RequestError(400, "Unvollstaendige Anfrage")
    return raw


class Gateway(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(
        self, port, *, instance, control, setup, create_admin, has_admin, stop
    ):
        super().__init__(("127.0.0.1", port), Handler)
        self.instance, self.control, self.setup = instance, control, setup
        self.create_admin, self.has_admin, self.stop_event = (
            create_admin,
            has_admin,
            stop,
        )
        self.setup_lock = threading.Lock()
        self.api_port = self.web_port = 0
        self.ready = False
        self.url = f"http://127.0.0.1:{self.server_port}"


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "Raumwerk"
    sys_version = ""

    def log_message(self, *_):
        pass  # URLs, cookies, passwords and form contents never enter access logs.

    def setup(self):
        super().setup()
        self.connection.settimeout(45)

    def reply(self, status, data, content_type="application/json; charset=utf-8"):
        raw = (
            json.dumps(data, ensure_ascii=False).encode()
            if not isinstance(data, bytes)
            else data
        )
        self.send_response(status)
        for key, value in [
            ("Content-Type", content_type),
            ("Content-Length", str(len(raw))),
            ("Cache-Control", "no-store"),
            ("Connection", "close"),
            ("X-Content-Type-Options", "nosniff"),
            ("X-Frame-Options", "DENY"),
        ]:
            self.send_header(key, value)
        if content_type.startswith("text/html"):
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
            )
        self.end_headers()
        self.close_connection = True
        if self.command != "HEAD":
            self.wfile.write(raw)

    def local_request(self):
        port = self.server.server_port
        if self.headers.get("Host") not in {f"127.0.0.1:{port}", f"localhost:{port}"}:
            raise RequestError(403, "Bitte die Adresse aus STARTEN.cmd verwenden")
        origin = self.headers.get("Origin")
        if origin and origin not in {
            f"http://127.0.0.1:{port}",
            f"http://localhost:{port}",
        }:
            raise RequestError(403, "Unzulaessiger Ursprung")

    def dispatch(self):
        try:
            self.local_request()
            route = urlsplit(self.path).path
            if route.startswith("/__desktop/"):
                self.desktop(route)
            elif route == "/einrichten" and self.command in {"GET", "HEAD"}:
                if self.server.has_admin():
                    self.reply(
                        409,
                        {
                            "error": "Einrichtung bereits abgeschlossen. Bitte /admin oeffnen."
                        },
                    )
                else:
                    self.reply(200, SETUP_HTML.encode(), "text/html; charset=utf-8")
            else:
                self.proxy()
        except RequestError as error:
            self.reply(error.status, {"error": error.message})
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            self.close_connection = True

    def desktop(self, route):
        if route == "/__desktop/health" and self.command == "GET":
            self.reply(
                200 if self.server.ready else 503,
                {"instance": self.server.instance, "ready": self.server.ready},
            )
            return
        if route == "/__desktop/setup" and self.command == "POST":
            if self.server.has_admin():
                raise RequestError(409, "Der Administrator wurde bereits angelegt")
            token = self.headers.get("X-Raumwerk-Setup", "")
            if not token or not hmac.compare_digest(
                token.encode(), self.server.setup.encode()
            ):
                raise RequestError(
                    403, "Einrichtungslink ungueltig. STARTEN.cmd erneut oeffnen."
                )
            try:
                data = json.loads(read_body(self, 16384))
                if not isinstance(data, dict):
                    raise ValueError()
            except (ValueError, UnicodeError):
                raise RequestError(400, "Ungueltige Eingabe")
            with self.server.setup_lock:
                if self.server.has_admin():
                    raise RequestError(409, "Der Administrator wurde bereits angelegt")
                try:
                    self.server.create_admin(data)
                except ValueError:
                    raise RequestError(
                        422,
                        "E-Mail pruefen. Passwort mindestens 12 Zeichen; beide Eingaben muessen gleich sein.",
                    )
                self.server.setup = ""
            self.reply(201, {"ok": True})
            return
        token = self.headers.get("X-Raumwerk-Control", "")
        if not token or not hmac.compare_digest(
            token.encode(), self.server.control.encode()
        ):
            raise RequestError(403, "Lokaler Steuerungszugriff verweigert")
        if self.command == "POST" and route == "/__desktop/open":
            target = (
                "/admin"
                if self.server.has_admin()
                else "/einrichten#" + self.server.setup
            )
            self.reply(200, {"url": self.server.url + target})
        elif self.command == "POST" and route == "/__desktop/stop":
            self.reply(200, {"ok": True})
            self.server.stop_event.set()
        else:
            raise RequestError(404, "Unbekannte Steuerungsfunktion")

    def proxy(self):
        if not self.server.ready:
            raise RequestError(503, "Der Baukasten startet noch. Bitte kurz warten.")
        is_api = self.path == "/api" or self.path.startswith("/api/")
        body = read_body(self)
        connection_headers = {
            x.strip().lower() for x in self.headers.get("Connection", "").split(",")
        }
        excluded = HOP | connection_headers | {"content-length", "expect"}
        headers = {k: v for k, v in self.headers.items() if k.lower() not in excluded}
        headers["Content-Length"] = str(len(body))
        # Use direct HTTPConnection: system proxy variables never receive local requests.
        connection = http.client.HTTPConnection(
            "127.0.0.1",
            self.server.api_port if is_api else self.server.web_port,
            timeout=60,
        )
        sent = False
        try:
            connection.request(self.command, self.path, body=body, headers=headers)
            response = connection.getresponse()
            self.send_response(response.status)
            blocked = HOP | {
                x.strip().lower()
                for x in response.getheader("Connection", "").split(",")
            }
            for key, value in response.getheaders():
                if key.lower() not in blocked:
                    self.send_header(
                        key, value
                    )  # Preserve multiple Set-Cookie headers.
            self.send_header("Connection", "close")
            self.end_headers()
            sent = True
            if self.command != "HEAD":
                while chunk := response.read(65536):
                    self.wfile.write(chunk)
        except (OSError, http.client.HTTPException):
            if not sent:
                self.reply(
                    502,
                    {
                        "error": "Ein Programmteil ist nicht erreichbar. Bitte DIAGNOSE.cmd oeffnen."
                    },
                )
        finally:
            self.close_connection = True
            connection.close()

    do_GET = do_HEAD = do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = dispatch
