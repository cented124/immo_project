"""Portable desktop controller. Processes and data are owned by this project only."""

import argparse
import contextlib
import hashlib
import http.client
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from urllib.parse import urlsplit
import webbrowser
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".runtime"
CONTROL = RUNTIME / "control"
LOGS = RUNTIME / "logs"
STATE = CONTROL / "state.json"
DATA = ROOT / "DATEN"


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False)
    temporary.replace(path)


class FileLock:
    def __init__(self, path):
        self.path, self.handle = path, None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = open(self.path, "a+b")
        self.handle.seek(0)
        if not self.handle.read(1):
            self.handle.write(b"0")
            self.handle.flush()
        self.handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.handle.close()
            raise RuntimeError(
                "Dieser Schritt laeuft bereits. Bitte das andere Startfenster abwarten."
            )
        return self

    def __exit__(self, *_):
        if self.handle:
            self.handle.close()  # OS releases the lock even after a crash.


def local_call(state, route, method="GET"):
    url = urlsplit(state["url"])
    if url.scheme != "http" or url.hostname != "127.0.0.1" or not url.port:
        raise ValueError("Ungueltige lokale Adresse")
    connection = http.client.HTTPConnection("127.0.0.1", url.port, timeout=3)
    try:
        connection.request(
            method, route, headers={"X-Raumwerk-Control": state.get("control", "")}
        )
        response = connection.getresponse()
        data = json.loads(response.read(65536))
        if response.status != 200:
            raise ValueError("Lokaler Zugriff fehlgeschlagen")
        return data
    finally:
        connection.close()


def running():
    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
        status = local_call(state, "/__desktop/health")
        return (
            state
            if status.get("instance") == state["instance"] and status.get("ready")
            else None
        )
    except (OSError, ValueError, KeyError, http.client.HTTPException):
        return None


def node_executable():
    if os.name == "nt":
        path = RUNTIME / "node/node.exe"
    else:
        path = Path(shutil.which("node") or "/missing-node")
    if not path.is_file():
        raise RuntimeError(
            "Node-Laufzeit fehlt. Bitte STARTEN.cmd beziehungsweise REPARIEREN.cmd verwenden."
        )
    return path


def clean_text(value):
    value = re.sub(r"(https?://)[^\s/@]+:[^\s/@]+@", r"\1[ZUGANG]@", value)
    value = re.sub(r"\b\d{7,12}:[A-Za-z0-9_-]{25,50}\b", "[BOT-TOKEN]", value)
    return value


class Process:
    """A private process tree: Job Object on Windows; new session on POSIX."""

    def __init__(self, args, **kwargs):
        self.job = None
        flags = (
            subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
            if os.name == "nt"
            else 0
        )
        self.process = subprocess.Popen(
            args, creationflags=flags, start_new_session=os.name != "nt", **kwargs
        )
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes

            class Basic(ctypes.Structure):
                _fields_ = [
                    ("PerProcessUserTimeLimit", ctypes.c_int64),
                    ("PerJobUserTimeLimit", ctypes.c_int64),
                    ("LimitFlags", wintypes.DWORD),
                    ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t),
                    ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t),
                    ("PriorityClass", wintypes.DWORD),
                    ("SchedulingClass", wintypes.DWORD),
                ]

            class IO(ctypes.Structure):
                _fields_ = [
                    (name, ctypes.c_uint64)
                    for name in [
                        "ReadOperationCount",
                        "WriteOperationCount",
                        "OtherOperationCount",
                        "ReadTransferCount",
                        "WriteTransferCount",
                        "OtherTransferCount",
                    ]
                ]

            class Extended(ctypes.Structure):
                _fields_ = [
                    ("BasicLimitInformation", Basic),
                    ("IoInfo", IO),
                    ("ProcessMemoryLimit", ctypes.c_size_t),
                    ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t),
                    ("PeakJobMemoryUsed", ctypes.c_size_t),
                ]

            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.CreateJobObjectW.restype = wintypes.HANDLE
            kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
            kernel.SetInformationJobObject.argtypes = [
                wintypes.HANDLE,
                ctypes.c_int,
                ctypes.c_void_p,
                wintypes.DWORD,
            ]
            kernel.AssignProcessToJobObject.argtypes = [
                wintypes.HANDLE,
                wintypes.HANDLE,
            ]
            kernel.CloseHandle.argtypes = [wintypes.HANDLE]
            job = kernel.CreateJobObjectW(None, None)
            limits = Extended()
            limits.BasicLimitInformation.LimitFlags = 0x2000
            if (
                not job
                or not kernel.SetInformationJobObject(
                    job, 9, ctypes.byref(limits), ctypes.sizeof(limits)
                )
                or not kernel.AssignProcessToJobObject(job, int(self.process._handle))
            ):
                if job:
                    kernel.CloseHandle(job)
                self.process.kill()
                self.process.wait()
                raise RuntimeError(
                    "Windows hat die lokale Prozessverwaltung blockiert. Details: DIAGNOSE.cmd."
                )
            self.job = (kernel, job)

    def close(self):
        if self.process.poll() is None:
            if os.name == "nt":
                self.process.terminate()
            else:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(self.process.pid, signal.SIGTERM)
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                if os.name == "nt":
                    self.process.kill()
                else:
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(self.process.pid, signal.SIGKILL)
                self.process.wait(timeout=5)
        if self.job:
            self.job[0].CloseHandle(self.job[1])
            self.job = None


def command(args, *, cwd=ROOT, env=None, label="installation", timeout=900):
    LOGS.mkdir(parents=True, exist_ok=True)
    process = Process(
        [str(a) for a in args],
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        try:
            output, _ = process.process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                f"{label}: Zeitlimit erreicht. Internetverbindung und DIAGNOSE.cmd pruefen."
            )
        text = clean_text(output.decode("utf-8", errors="replace"))
        (LOGS / (label + ".log")).write_text(text[-2_000_000:], encoding="utf-8")
        if process.process.returncode:
            raise RuntimeError(
                f"{label} fehlgeschlagen. Details stehen unter .runtime/logs/{label}.log. REPARIEREN.cmd kann die Programme neu einrichten."
            )
        return text
    finally:
        process.close()


def source_digest():
    digest = hashlib.sha256()
    folder = ROOT / "frontend"
    paths = []
    for current, directories, files in os.walk(folder):
        directories[:] = [
            d
            for d in directories
            if not d.startswith(".")
            and d not in {"node_modules", "tests", "test-results"}
        ]
        paths.extend(Path(current) / name for name in files)
    for path in sorted(paths):
        rel = path.relative_to(folder)
        if not path.is_file() or any(
            p.startswith(".") or p in {"node_modules", "tests", "test-results"}
            for p in rel.parts
        ):
            continue
        if path.name in {
            "next-env.d.ts",
            "tsconfig.tsbuildinfo",
            "AGENTS.md",
            "playwright.config.ts",
        }:
            continue
        digest.update(rel.as_posix().encode())
        digest.update(path.read_bytes())
    digest.update(sys.platform.encode())
    return digest.hexdigest()


def prepare():
    node = node_executable()
    version = command([node, "--version"], label="node-version").strip()
    if not version.startswith("v24."):
        raise RuntimeError(
            "Fuer dieses Paket wird die mitgelieferte Node-24-Laufzeit benoetigt."
        )
    signature = hashlib.sha256((source_digest() + version).encode()).hexdigest()
    target = RUNTIME / ("web-" + signature[:16])
    marker = target / "desktop-ready.json"
    try:
        if (
            json.loads(marker.read_text(encoding="utf-8"))["signature"] == signature
            and (target / ".next/BUILD_ID").is_file()
        ):
            return target
    except (OSError, ValueError, KeyError):
        pass
    print(
        "Die Website wird einmalig vorbereitet. Das kann einige Minuten dauern.",
        flush=True,
    )
    stage = RUNTIME / ("web-build-" + secrets.token_hex(6))
    shutil.copytree(
        ROOT / "frontend",
        stage,
        ignore=shutil.ignore_patterns(
            "node_modules", ".next*", "tests", "test-results", "*.tsbuildinfo"
        ),
    )
    (stage / "next-env.d.ts").write_text(
        '/// <reference types="next" />\n/// <reference types="next/image-types/global" />\n',
        encoding="utf-8",
    )
    env = {
        **os.environ,
        "NEXT_TELEMETRY_DISABLED": "1",
        "RAUMWERK_DESKTOP": "1",
        "NEXT_DIST_DIR": ".next",
        "NODE_USE_SYSTEM_CA": "1",
    }
    if os.name == "nt":
        npm = node.parent / "node_modules/npm/bin/npm-cli.js"
    else:
        npm = Path(shutil.which("npm")).resolve()
    env["PATH"] = str(node.parent) + os.pathsep + env.get("PATH", "")
    try:
        command(
            [
                node,
                npm,
                "ci",
                "--ignore-scripts",
                "--include=dev",
                "--no-audit",
                "--no-fund",
                "--cache",
                RUNTIME / "npm-cache",
                "--registry",
                "https://registry.npmjs.org",
            ],
            cwd=stage,
            env=env,
            label="frontend-install",
        )
        command(
            [node, stage / "node_modules/next/dist/bin/next", "build"],
            cwd=stage,
            env=env,
            label="frontend-build",
        )
        if not (stage / ".next/BUILD_ID").is_file():
            raise RuntimeError("Der Frontend-Build ist unvollstaendig.")
        if target.exists():
            shutil.rmtree(target)
        stage.rename(target)
        atomic_json(marker, {"signature": signature, "node": version})
        return target
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def configure_environment():
    DATA.mkdir(parents=True, exist_ok=True)
    os.environ.update(
        DATA_DIR=str(DATA),
        DATABASE_URL="sqlite:///" + (DATA / "app.db").as_posix(),
        COOKIE_SECURE="0",
        TRUST_PROXY_HEADERS="0",
        SESSION_COOKIE_NAME="raumwerk_desktop_"
        + hashlib.sha256(str(DATA.resolve()).casefold().encode()).hexdigest()[:16],
    )
    os.environ.pop(
        "ENCRYPTION_KEY", None
    )  # Desktop key lives beside its own SQLite DB.
    sys.path.insert(0, str(ROOT / "backend"))


def serve(web_dir, no_delivery=False):
    from desktop_proxy import Gateway

    with FileLock(CONTROL / "running.lock"):
        configure_environment()
        migration_env = {**os.environ, "PYTHONPATH": str(ROOT / "backend")}
        command(
            [
                sys.executable,
                "-X",
                "utf8",
                "-m",
                "alembic",
                "-c",
                ROOT / "backend/alembic.ini",
                "upgrade",
                "head",
            ],
            env=migration_env,
            label="migration",
        )
        from app.project import import_project

        import_project(ROOT / "project/project.json")
        from app.db import Session, User, engine
        from sqlalchemy import select
        from app.security import hasher
        from pydantic import EmailStr, TypeAdapter

        def has_admin():
            with Session() as db:
                return (
                    db.scalar(
                        select(User.id)
                        .where(User.role == "admin", User.active == True)
                        .limit(1)
                    )
                    is not None
                )

        def create_admin(data):
            try:
                email = str(
                    TypeAdapter(EmailStr).validate_python(data.get("email", ""))
                ).lower()
                password = data.get("password", "")
                if (
                    not isinstance(password, str)
                    or not 12 <= len(password) <= 512
                    or password != data.get("repeat")
                ):
                    raise ValueError()
            except Exception:
                raise ValueError("Ungueltige Anmeldung")
            with Session() as db:
                db.add(User(email=email, password=hasher.hash(password), role="admin"))
                db.commit()

        stop = threading.Event()
        signal.signal(signal.SIGTERM, lambda *_: stop.set())
        try:
            gateway = Gateway(
                3000,
                instance=secrets.token_hex(16),
                control=secrets.token_urlsafe(32),
                setup=secrets.token_urlsafe(32),
                create_admin=create_admin,
                has_admin=has_admin,
                stop=stop,
            )
        except OSError:
            gateway = Gateway(
                0,
                instance=secrets.token_hex(16),
                control=secrets.token_urlsafe(32),
                setup=secrets.token_urlsafe(32),
                create_admin=create_admin,
                has_admin=has_admin,
                stop=stop,
            )
        api_socket = socket.socket()
        api_socket.bind(("127.0.0.1", 0))
        gateway.api_port = api_socket.getsockname()[1]
        os.environ["PUBLIC_ORIGIN"] = (
            gateway.url + f",http://localhost:{gateway.server_port}"
        )
        os.environ["DELIVERY_WORKER"] = "0" if no_delivery else "1"
        from app.main import app
        import uvicorn

        class SafeFormatter(logging.Formatter):
            def formatException(self, info):
                return (
                    info[0].__name__
                    + ": technische Ausnahme; Anfrageinhalte werden nicht protokolliert."
                )

        LOGS.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            LOGS / "backend.log", maxBytes=1_000_000, backupCount=2, encoding="utf-8"
        )
        handler.setFormatter(SafeFormatter("%(asctime)s %(levelname)s %(message)s"))
        logger = logging.getLogger("uvicorn.error")
        logger.handlers = [handler]
        logger.propagate = False
        server = uvicorn.Server(
            uvicorn.Config(
                app, log_config=None, access_log=False, timeout_graceful_shutdown=25
            )
        )
        api_thread = threading.Thread(
            target=lambda: server.run(sockets=[api_socket]), daemon=True
        )
        api_thread.start()
        node_file = CONTROL / ("node-" + gateway.instance + ".json")
        child = None
        try:
            env = {
                **os.environ,
                "API_INTERNAL_URL": f"http://127.0.0.1:{gateway.api_port}",
                "RAUMWERK_DESKTOP": "1",
                "NEXT_DIST_DIR": ".next",
                "NEXT_TELEMETRY_DISABLED": "1",
                "NODE_USE_ENV_PROXY": "0",
            }
            env["NO_PROXY"] = "127.0.0.1,localhost," + env.get("NO_PROXY", "")
            log = open(LOGS / "web.log", "wb")
            child = Process(
                [
                    str(node_executable()),
                    str(ROOT / "scripts/desktop-web.cjs"),
                    str(web_dir),
                    str(node_file),
                ],
                cwd=web_dir,
                env=env,
                stdin=subprocess.PIPE,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline:
                if child.process.poll() is not None or not api_thread.is_alive():
                    raise RuntimeError(
                        "Ein Programmteil konnte nicht starten. Bitte DIAGNOSE.cmd oeffnen."
                    )
                if server.started and node_file.is_file():
                    gateway.web_port = json.loads(
                        node_file.read_text(encoding="utf-8")
                    )["port"]
                    break
                time.sleep(0.2)
            else:
                raise RuntimeError("Start dauert zu lange. Bitte DIAGNOSE.cmd oeffnen.")
            gateway.ready = True
            proxy_thread = threading.Thread(target=gateway.serve_forever, daemon=True)
            proxy_thread.start()
            atomic_json(
                STATE,
                {
                    "instance": gateway.instance,
                    "control": gateway.control,
                    "url": gateway.url,
                    "pid": os.getpid(),
                    "web_dir": str(web_dir),
                },
            )
            while not stop.wait(0.5):
                if child.process.poll() is not None or not api_thread.is_alive():
                    raise RuntimeError(
                        "Ein Programmteil wurde beendet. Bitte STARTEN.cmd erneut oeffnen."
                    )
        finally:
            gateway.ready = False
            if "proxy_thread" in locals():
                gateway.shutdown()
            gateway.server_close()
            server.should_exit = True
            api_thread.join(timeout=30)
            if child:
                with contextlib.suppress(OSError, ValueError):
                    child.process.stdin.write(b"stop\n")
                    child.process.stdin.flush()
                with contextlib.suppress(subprocess.TimeoutExpired):
                    child.process.wait(timeout=5)
                child.close()
            if "log" in locals():
                log.close()
            engine.dispose()
            api_socket.close()
            handler.close()
            node_file.unlink(missing_ok=True)
            STATE.unlink(missing_ok=True)


def launch(no_browser=False, no_delivery=False):
    with FileLock(CONTROL / "install.lock"):
        state = running()
        if not state:
            web = prepare()
            LOGS.mkdir(parents=True, exist_ok=True)
            args = [
                sys.executable,
                "-X",
                "utf8",
                str(Path(__file__).resolve()),
                "serve",
                "--web-dir",
                str(web),
            ]
            if no_delivery:
                args.append("--no-delivery")
            output = open(LOGS / "desktop.log", "wb")
            flags = (
                subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
                if os.name == "nt"
                else 0
            )
            process = subprocess.Popen(
                args,
                cwd=ROOT,
                stdout=output,
                stderr=subprocess.STDOUT,
                creationflags=flags,
                start_new_session=os.name != "nt",
            )
            try:
                deadline = time.monotonic() + 100
                while time.monotonic() < deadline:
                    state = running()
                    if state:
                        break
                    if process.poll() is not None:
                        raise RuntimeError(
                            "Der Baukasten konnte nicht starten. Details: .runtime/logs/desktop.log und DIAGNOSE.cmd."
                        )
                    time.sleep(0.25)
                if not state:
                    process.terminate()
                    raise RuntimeError(
                        "Startzeit ueberschritten. Bitte DIAGNOSE.cmd oeffnen."
                    )
            finally:
                output.close()
        target = local_call(state, "/__desktop/open", "POST")["url"]
        if not no_browser:
            webbrowser.open(target)
        print("Baukasten ist bereit: " + state["url"])
        print("STARTEN.cmd oeffnet ihn erneut. STOPPEN.cmd beendet diese Installation.")


def stop():
    state = running()
    if not state:
        print("Diese Installation ist bereits gestoppt.")
        return
    local_call(state, "/__desktop/stop", "POST")
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        if not STATE.exists():
            if os.name == "nt":
                import ctypes
                from ctypes import wintypes

                kernel = ctypes.WinDLL("kernel32", use_last_error=True)
                kernel.OpenProcess.argtypes = [
                    wintypes.DWORD,
                    wintypes.BOOL,
                    wintypes.DWORD,
                ]
                kernel.OpenProcess.restype = wintypes.HANDLE
                kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
                kernel.CloseHandle.argtypes = [wintypes.HANDLE]
                handle = kernel.OpenProcess(0x100000, False, state["pid"])
                if handle:
                    result = kernel.WaitForSingleObject(handle, 5000)
                    kernel.CloseHandle(handle)
                    if result == 258:
                        raise RuntimeError(
                            "Das Programm beendet sich noch. Bitte kurz warten und STOPPEN.cmd erneut ausfuehren."
                        )
            print("Baukasten gestoppt. Deine Daten bleiben erhalten.")
            return
        time.sleep(0.25)
    raise RuntimeError(
        "Stoppen dauert ungewoehnlich lange. Bitte DIAGNOSE.cmd verwenden. Es werden keine fremden Prozesse beendet."
    )


def backup():
    # A second STARTEN must not reopen the database while its files are copied.
    with FileLock(CONTROL / "install.lock"):
        stop()
        if not (DATA / "app.db").is_file():
            raise RuntimeError("Noch keine lokale Datenbank vorhanden.")
        folder = ROOT / "SICHERUNGEN"
        folder.mkdir(mode=0o700, exist_ok=True)
        target = folder / (
            time.strftime("Raumwerk-%Y%m%d-%H%M%S-") + secrets.token_hex(3) + ".zip"
        )
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in DATA.rglob("*"):
                if path.is_file() and not path.is_symlink():
                    archive.write(path, "DATEN/" + path.relative_to(DATA).as_posix())
    print("Sicherung erstellt: " + str(target))
    print(
        "Enthaelt private Daten und den Schluessel. Nicht in GitHub oder im Chat veroeffentlichen."
    )


def diagnose():
    state = running()
    print("Raumwerk Desktop-Diagnose (ohne Zugangsdaten)")
    print("System: " + sys.platform + "; Python: " + sys.version.split()[0])
    print(
        "Status: "
        + ("gestartet, " + state["url"] if state else "gestoppt / nicht erreichbar")
    )
    print(
        "Lokale Datenbank: "
        + ("vorhanden" if (DATA / "app.db").is_file() else "noch nicht angelegt")
    )
    print("Daten: DATEN; Protokolle: .runtime/logs")
    print("Freier Speicher: " + str(shutil.disk_usage(ROOT).free // (1024**2)) + " MB")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action", choices=["prepare", "launch", "serve", "stop", "diagnose", "backup"]
    )
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--no-delivery", action="store_true")
    parser.add_argument("--web-dir", type=Path)
    args = parser.parse_args()
    os.chdir(ROOT)
    RUNTIME.mkdir(exist_ok=True)
    CONTROL.mkdir(exist_ok=True)
    if args.action == "prepare":
        with FileLock(CONTROL / "install.lock"):
            prepare()
    elif args.action == "launch":
        launch(args.no_browser, args.no_delivery)
    elif args.action == "serve":
        if not args.web_dir or args.web_dir.resolve().parent != RUNTIME.resolve():
            raise RuntimeError("Ungueltiges Frontendverzeichnis")
        serve(args.web_dir, args.no_delivery)
    elif args.action == "stop":
        stop()
    elif args.action == "backup":
        backup()
    else:
        diagnose()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Abgebrochen. Daten wurden nicht geloescht.")
        sys.exit(1)
    except Exception as error:
        print(
            "Fehler: "
            + (
                str(error)
                if isinstance(error, RuntimeError)
                else type(error).__name__ + ". Bitte DIAGNOSE.cmd oeffnen."
            ),
            file=sys.stderr,
        )
        sys.exit(1)
