from __future__ import annotations

import json
from typing import Dict, List

from flask import Blueprint, Response, current_app, request, session, stream_with_context

from .services.deepseek_client import get_deepseek_client


bp = Blueprint("api", __name__)


def _get_history() -> List[Dict[str, str]]:
    history = session.get("history")
    if not isinstance(history, list):
        history = []
    return history


def _save_history(history: List[Dict[str, str]]) -> None:
    max_h = int(current_app.config.get("MAX_HISTORY", 20))
    if len(history) > max_h:
        history = history[-max_h:]
    session["history"] = history


@bp.post("/chat")
def chat_stream() -> Response:
    payload = request.get_json(silent=True) or {}
    user_msg = (payload.get("message") or "").strip()
    if not user_msg:
        return Response(json.dumps({"error": "message required"}), 400, mimetype="application/json")

    if not (current_app.config.get("DEEPSEEK_API_KEY") or "").strip():
        return Response(
            json.dumps({"error": "Server missing DEEPSEEK_API_KEY. Set it in .env and restart."}),
            500,
            mimetype="application/json",
        )

    history = _get_history()
    history.append({"role": "user", "content": user_msg})

    client = get_deepseek_client()

    def generate():
        yield "{\n\"ok\": true, \"chunks\": ["
        first = True
        try:
            for delta in client.stream_chat(history):
                if not first:
                    yield ","
                first = False
                # Stream JSON-friendly chunks; frontend will join and render markdown
                yield json.dumps({"delta": delta})
        except Exception as e:
            err = {"error": str(e)}
            if not first:
                yield ","
            yield json.dumps(err)
        finally:
            yield "]}"

    resp = Response(stream_with_context(generate()), mimetype="application/json")
    # Update history with assistant message as a single concatenated string after streaming via WSGI closing callback is tricky.
    # Instead, the frontend will POST "/commit" to store the assistant message when done.
    return resp


@bp.get("/ping")
def ping() -> Response:
    """Small diagnostic endpoint to verify DeepSeek auth and connectivity without streaming."""
    if not (current_app.config.get("DEEPSEEK_API_KEY") or "").strip():
        return Response(json.dumps({"ok": False, "error": "DEEPSEEK_API_KEY not set"}), mimetype="application/json")
    try:
        client = get_deepseek_client()
        # Send a minimal non-streaming probe by reusing stream path but reading one chunk
        # We'll just try to open the stream and immediately stop after first delta.
        for _ in client.stream_chat([{"role": "user", "content": "ping"}]):
            break
        return Response(json.dumps({"ok": True}), mimetype="application/json")
    except Exception as e:
        return Response(json.dumps({"ok": False, "error": str(e)}), mimetype="application/json")


@bp.post("/commit")
def commit_assistant() -> Response:
    payload = request.get_json(silent=True) or {}
    content = (payload.get("content") or "").strip()
    if not content:
        return Response(json.dumps({"error": "content required"}), 400, mimetype="application/json")
    history = _get_history()
    history.append({"role": "assistant", "content": content})
    _save_history(history)
    return Response(json.dumps({"ok": True}), mimetype="application/json")


@bp.post("/reset")
def reset_history() -> Response:
    session["history"] = []
    return Response(json.dumps({"ok": True}), mimetype="application/json")

