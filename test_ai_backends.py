"""
Exercises engine/ai.py's backend detection and generation against real
mock HTTP servers that mimic Ollama's and llama.cpp's actual API shapes
(no real model or GPU needed). This catches bugs in the HTTP/JSON plumbing
itself, not just in-memory logic.

Run it directly: `python test_ai_backends.py`

Note: this binds to 127.0.0.1:11434 and 127.0.0.1:8080 (Ollama's and
llama.cpp's default ports) for the duration of the test. Stop any real
Ollama/llama-server instance first if you want to run this.
"""
import json
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from engine import genres as genres_mod, events
from engine.ai import LocalAI

LLAMACPP_MODE = {"mode": "json"}  # json | fenced_json | chatty_json | not_json


def _send_json(handler, obj, status=200):
    body = json.dumps(obj).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class OllamaHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *a):
        pass

    def do_GET(self):
        if self.path == "/api/tags":
            _send_json(self, {"models": [{"name": "llama3.2:3b"}, {"name": "mistral:7b"}]})
        else:
            _send_json(self, {"error": "not found"}, 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        payload = json.loads(raw.decode("utf-8")) if raw else {}
        if self.path != "/api/generate":
            _send_json(self, {"error": "not found"}, 404)
            return
        if payload.get("format") == "json":
            content = json.dumps({
                "narration": "Ollama handles it.", "money_delta": 7, "food_delta": 0,
                "special_resource_delta": 0, "vehicle_health_delta": 0, "morale_delta": 0,
                "distance_delta": 0, "target": "", "target_health_delta": 0,
            })
        else:
            content = "plain ollama narration"
        _send_json(self, {"response": content})


class LlamaCppHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *a):
        pass

    def do_GET(self):
        if self.path == "/v1/models":
            _send_json(self, {"object": "list", "data": [{"id": "mock-gguf-model"}]})
        else:
            _send_json(self, {"error": "not found"}, 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        payload = json.loads(raw.decode("utf-8")) if raw else {}
        if self.path != "/v1/chat/completions":
            _send_json(self, {"error": "not found"}, 404)
            return
        wants_json = "response_format" in payload
        mode = LLAMACPP_MODE["mode"]
        base = {"money_delta": 0, "food_delta": 0, "special_resource_delta": 0,
                "vehicle_health_delta": 0, "morale_delta": 0, "distance_delta": 0,
                "target": "", "target_health_delta": 0}
        if not wants_json:
            content = "plain llamacpp narration"
        elif mode == "json":
            content = json.dumps({**base, "narration": "You handle it with quiet confidence.", "money_delta": 5})
        elif mode == "fenced_json":
            content = "```json\n" + json.dumps({**base, "narration": "It works out.", "food_delta": 10}) + "\n```"
        elif mode == "chatty_json":
            content = ("Sure! Here you go:\n" +
                       json.dumps({**base, "narration": "A little chatty, still parses.", "money_delta": 1}) +
                       "\nHope that helps!")
        else:  # not_json
            content = "I will not output JSON."
        _send_json(self, {"choices": [{"message": {"content": content}}]})


def _start(handler_cls, port):
    server = ThreadingHTTPServer(("127.0.0.1", port), handler_cls)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def test_llamacpp_detection_and_generation():
    server = _start(LlamaCppHandler, 8080)
    try:
        time.sleep(0.2)
        ai = LocalAI()
        assert ai.available is True
        assert ai.backend == "llamacpp"
        assert ai.model == "mock-gguf-model"

        text = ai.generate("prompt", system="sys", fallback="FALLBACK")
        assert text == "plain llamacpp narration"

        genre = genres_mod.get_genre("space")
        state = events.new_game(genre, random.Random(1))

        LLAMACPP_MODE["mode"] = "json"
        result = ai.interpret_action(genre, state, "situation", "action")
        assert result["money_delta"] == 5

        LLAMACPP_MODE["mode"] = "fenced_json"
        result = ai.interpret_action(genre, state, "situation", "action")
        assert result["food_delta"] == 10

        LLAMACPP_MODE["mode"] = "chatty_json"
        result = ai.interpret_action(genre, state, "situation", "action")
        assert result["money_delta"] == 1

        LLAMACPP_MODE["mode"] = "not_json"
        result = ai.interpret_action(genre, state, "situation", "action")
        assert result["money_delta"] == 0
        assert "attempts it" in result["narration"]

        print("test_llamacpp_detection_and_generation OK")
    finally:
        server.shutdown()


def test_ollama_detection_and_priority():
    ollama_server = _start(OllamaHandler, 11434)
    try:
        time.sleep(0.2)
        ai = LocalAI()
        assert ai.backend == "ollama"
        assert ai.model == "llama3.2:3b"  # prefers the smaller-looking model

        genre = genres_mod.get_genre("wasteland")
        state = events.new_game(genre, random.Random(2))
        result = ai.interpret_action(genre, state, "situation", "action")
        assert result["money_delta"] == 7

        # Ollama should be preferred even if a llama.cpp server is also up.
        llamacpp_server = _start(LlamaCppHandler, 8080)
        try:
            time.sleep(0.2)
            ai2 = LocalAI()
            assert ai2.backend == "ollama"
        finally:
            llamacpp_server.shutdown()

        print("test_ollama_detection_and_priority OK")
    finally:
        ollama_server.shutdown()


def test_no_backend_available():
    ai = LocalAI()
    assert ai.available is False
    assert ai.backend is None
    result = ai.interpret_action(genres_mod.get_genre("fantasy"), None, "situation", "action")
    assert result["money_delta"] == 0
    print("test_no_backend_available OK")


if __name__ == "__main__":
    test_no_backend_available()
    test_llamacpp_detection_and_generation()
    test_ollama_detection_and_priority()
    print("\nAll AI backend tests passed.")
