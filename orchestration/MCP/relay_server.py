#!/usr/bin/env python3
"""FastAPI-based relay server that exposes health + heartbeat endpoints."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from custody.custodian_ledger import ledger_from_config, load_global_config
from telemetry.emit_heartbeat import HeartbeatEmitter

CONFIG_CACHE: Dict[str, Any] | None = None


def get_config() -> Dict[str, Any]:
    global CONFIG_CACHE
    if CONFIG_CACHE is None:
        CONFIG_CACHE = load_global_config()
    return CONFIG_CACHE


app = FastAPI(title="Codex MCP Relay", version="0.1.0", docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    config = get_config()
    app.state.ledger = ledger_from_config()
    app.state.heartbeat = HeartbeatEmitter()
    app.state.identity = {
        "service": config.get("relay", {}).get("service_name", "codex-mcp-relay"),
        "version": app.version,
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    identity = getattr(app.state, "identity")
    return {"status": "ok", **identity}


@app.get("/heartbeat")
async def heartbeat() -> Dict[str, Any]:
    emitter: HeartbeatEmitter = getattr(app.state, "heartbeat")
    return emitter.emit()


if __name__ == "__main__":
    cfg = get_config()
    relay_cfg = cfg.get("relay", {})
    host = relay_cfg.get("host", "127.0.0.1")
    port = int(relay_cfg.get("port", 8000))
    uvicorn.run(app, host=host, port=port)
