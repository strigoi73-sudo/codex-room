from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles

from .agent import AgentAdapter, CodexAgentAdapter
from .db import Database
from .exporter import as_json, as_markdown
from .models import (
    AddAgentRequest,
    BindInstitutionalReleaseRequest,
    CreateRoomRequest,
    DefaultProfilesUpdate,
    NewTopicRequest,
    ObserverMessageRequest,
    PrepareRoundRequest,
    RolloverRoomRequest,
    UpdateRoomRequest,
)
from .orchestrator import RoomRuntime


PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent


def create_app(
    *,
    database_path: Path | None = None,
    data_root: Path | None = None,
    adapter: AgentAdapter | None = None,
) -> FastAPI:
    root = data_root or PROJECT_ROOT / "data"
    db = Database(database_path or root / "codex-room.db")
    runtime = RoomRuntime(db, adapter or CodexAgentAdapter(), root)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        await runtime.initialize()
        yield
        await runtime.close()

    app = FastAPI(title="Codex Room", version="0.1.0", lifespan=lifespan)
    app.state.runtime = runtime

    @app.middleware("http")
    async def disable_local_ui_cache(request: Request, call_next):
        response = await call_next(request)
        if request.url.path in {"/", "/index.html", "/app.js", "/styles.css"}:
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/api/health")
    async def health() -> dict[str, Any]:
        return {"ok": True, "codex": runtime.auth_info}

    @app.get("/api/profiles/defaults")
    async def get_default_profiles() -> dict[str, dict[str, Any]]:
        return await db.get_default_profiles()

    @app.put("/api/profiles/defaults")
    async def update_default_profiles(
        request: DefaultProfilesUpdate,
    ) -> dict[str, dict[str, Any]]:
        return await db.update_default_profiles(**request.model_dump())

    @app.get("/api/rooms")
    async def list_rooms(include_archived: bool = Query(default=False)) -> list[dict[str, Any]]:
        rooms = await db.list_rooms(include_archived=include_archived)
        for room in rooms:
            room["agents"] = await db.get_agents(room["id"])
        return rooms

    @app.post("/api/rooms", status_code=201)
    async def create_room(request: CreateRoomRequest) -> dict[str, Any]:
        try:
            return await runtime.create_room(request)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.get("/api/rooms/{room_id}")
    async def get_room(room_id: str) -> dict[str, Any]:
        snapshot = await runtime.snapshot(room_id)
        if snapshot is None:
            raise HTTPException(status_code=404, detail="Room not found")
        return snapshot

    @app.post("/api/rooms/{room_id}/agents", status_code=201)
    async def add_agent(room_id: str, request: AddAgentRequest) -> dict[str, Any]:
        return await _translate_errors(runtime.add_agent(room_id, request))

    @app.post("/api/rooms/{room_id}/agents/{agent_key}/rebind-profile")
    async def rebind_agent_profile(room_id: str, agent_key: str) -> dict[str, Any]:
        return await _translate_errors(runtime.rebind_agent_profile(room_id, agent_key))

    @app.post("/api/rooms/{room_id}/rollover", status_code=201)
    async def rollover_room(room_id: str, request: RolloverRoomRequest) -> dict[str, Any]:
        return await _translate_errors(runtime.rollover(room_id, request))

    @app.post("/api/rooms/{room_id}/institutional-release")
    async def bind_institutional_release(
        room_id: str, request: BindInstitutionalReleaseRequest
    ) -> dict[str, Any]:
        return await _translate_errors(runtime.bind_institutional_release(room_id, request))

    @app.patch("/api/rooms/{room_id}", status_code=204)
    async def update_room(room_id: str, request: UpdateRoomRequest) -> Response:
        await _translate_errors(runtime.update_room(room_id, request))
        return Response(status_code=204)

    @app.post("/api/rooms/{room_id}/messages", status_code=201)
    async def send_message(room_id: str, request: ObserverMessageRequest) -> dict[str, Any]:
        return await _translate_errors(runtime.observer_message(room_id, request))

    @app.post("/api/rooms/{room_id}/pause", status_code=204)
    async def pause_room(room_id: str) -> Response:
        await _translate_errors(runtime.pause(room_id))
        return Response(status_code=204)

    @app.post("/api/rooms/{room_id}/resume", status_code=204)
    async def resume_room(room_id: str) -> Response:
        await _translate_errors(runtime.resume(room_id))
        return Response(status_code=204)

    @app.post("/api/rooms/{room_id}/stop", status_code=204)
    async def stop_room(room_id: str) -> Response:
        await _translate_errors(runtime.stop(room_id))
        return Response(status_code=204)

    @app.post("/api/rooms/{room_id}/new-topic")
    async def new_topic(room_id: str, request: NewTopicRequest) -> dict[str, Any]:
        return await _translate_errors(runtime.new_topic(room_id, request))

    @app.post("/api/rooms/{room_id}/rounds", status_code=201)
    async def prepare_round(room_id: str, request: PrepareRoundRequest) -> dict[str, Any]:
        return await _translate_errors(runtime.prepare_round(room_id, request))

    @app.post("/api/rooms/{room_id}/rounds/{round_id}/start")
    async def start_round(room_id: str, round_id: str) -> dict[str, Any]:
        return await _translate_errors(runtime.start_round(room_id, round_id))

    @app.post("/api/rooms/{room_id}/archive", status_code=204)
    async def archive_room(room_id: str) -> Response:
        await _translate_errors(runtime.archive(room_id))
        return Response(status_code=204)

    @app.post("/api/rooms/{room_id}/unarchive", status_code=204)
    async def unarchive_room(room_id: str) -> Response:
        await _translate_errors(runtime.unarchive(room_id))
        return Response(status_code=204)

    @app.post("/api/rooms/{room_id}/reset")
    async def reset_room(room_id: str) -> dict[str, Any]:
        return await _translate_errors(runtime.reset(room_id))

    @app.get("/api/rooms/{room_id}/export")
    async def export_room(room_id: str, format: str = Query(pattern="^(markdown|json)$")) -> Response:
        snapshot = await db.snapshot(room_id)
        if snapshot is None:
            raise HTTPException(status_code=404, detail="Room not found")
        safe_title = "".join(c if c.isalnum() or c in "-_" else "-" for c in snapshot["title"])
        if format == "json":
            return Response(
                as_json(snapshot),
                media_type="application/json",
                headers={"Content-Disposition": f'attachment; filename="{safe_title}.json"'},
            )
        return PlainTextResponse(
            as_markdown(snapshot),
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.md"'},
        )

    @app.websocket("/ws/rooms/{room_id}")
    async def room_socket(websocket: WebSocket, room_id: str) -> None:
        snapshot = await runtime.snapshot(room_id)
        if snapshot is None:
            await websocket.close(code=4404, reason="Room not found")
            return
        await websocket.accept()
        await websocket.send_json({"kind": "snapshot", "room": snapshot})
        try:
            async with runtime.hub.subscribe(room_id) as queue:
                while True:
                    payload = await queue.get()
                    await websocket.send_json(payload)
        except WebSocketDisconnect:
            return

    app.mount("/", StaticFiles(directory=PACKAGE_ROOT / "static", html=True), name="static")
    return app


async def _translate_errors(awaitable: Any) -> Any:
    try:
        return await awaitable
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Room not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


app = create_app()
