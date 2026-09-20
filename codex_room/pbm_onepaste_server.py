"""Local authenticated coordinator server for PBM v3."""

from __future__ import annotations

import argparse
import json
import secrets
import sys
import time
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from . import pbm
from . import pbm_onepaste as onepaste
from . import pbm_onepaste_room as room_control


def run_room_platform(run_id: str) -> dict[str, Any]:
    while True:
        action = onepaste.next_action(run_id, "room")
        if action["action"] == "complete":
            return {
                "ok": True,
                "run_id": run_id,
                "platform": "room",
                "complete": True,
            }
        if action["action"] == "wait":
            time.sleep(1)
            continue

        task_id = str(action["task_id"])
        onepaste.before_arm(run_id, task_id)
        state = onepaste.load_state(run_id)
        room_control.execute_task(
            run_id=run_id,
            task_id=task_id,
            base=str(state["room_base"]),
            database=pbm.PROJECT_ROOT / "data" / "codex-room.db",
        )
        onepaste.after_arm(run_id, task_id)


class CoordinatorHandler(BaseHTTPRequestHandler):
    server_version = "PBMOnePaste/3"

    @property
    def run_id(self) -> str:
        return str(getattr(self.server, "run_id"))

    @property
    def token(self) -> str:
        return str(getattr(self.server, "token"))

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write(
            "%s - %s\n" % (self.address_string(), format % args)
        )

    def authorized(self) -> bool:
        query = urllib.parse.parse_qs(
            urllib.parse.urlparse(self.path).query
        )
        supplied = (query.get("token") or [""])[0]
        return secrets.compare_digest(supplied, self.token)

    def send_json(self, status: int, payload: Any) -> None:
        body = (
            json.dumps(payload, sort_keys=True) + "\n"
        ).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        if not self.authorized():
            self.send_json(HTTPStatus.UNAUTHORIZED, {"ok": False})
            return
        if path == "/health":
            self.send_json(
                HTTPStatus.OK,
                {"ok": True, "run_id": self.run_id},
            )
            return
        if path == "/status":
            self.send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "run_id": self.run_id,
                    "desktop": onepaste.next_action(
                        self.run_id,
                        "desktop",
                    ),
                    "room": onepaste.next_action(
                        self.run_id,
                        "room",
                    ),
                },
            )
            return
        self.send_json(HTTPStatus.NOT_FOUND, {"ok": False})

    def do_POST(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        if not self.authorized():
            self.send_json(HTTPStatus.UNAUTHORIZED, {"ok": False})
            return
        if path != "/room/run":
            self.send_json(HTTPStatus.NOT_FOUND, {"ok": False})
            return
        try:
            result = run_room_platform(self.run_id)
        except Exception as exc:
            self.send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "detail": str(exc)[:1000],
                },
            )
            return
        self.send_json(HTTPStatus.OK, result)


def serve(run_id: str, port: int) -> None:
    state = onepaste.load_state(run_id)
    server = ThreadingHTTPServer(
        ("127.0.0.1", port),
        CoordinatorHandler,
    )
    setattr(server, "run_id", run_id)
    setattr(server, "token", str(state["token"]))
    server.serve_forever(poll_interval=0.5)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pbm-onepaste-server")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--port", type=int, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        serve(args.run_id, args.port)
    except (
        onepaste.OnePasteError,
        room_control.RoomControlError,
        pbm.PBMError,
        OSError,
        json.JSONDecodeError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
