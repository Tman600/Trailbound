import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from engine.ai import LocalAI
from engine.freeplay import FreeplayState

RESPONSE = {"content": "{}"}


def _send_json(handler, obj, status=200):
    body = json.dumps(obj).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *a):
        pass

    def do_GET(self):
        if self.path == "/v1/models":
            _send_json(self, {"object": "list", "data": [{"id": "mock-model"}]})
        else:
            _send_json(self, {"error": "not found"}, 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length) if length else None
        _send_json(self, {"choices": [{"message": {"content": RESPONSE["content"]}}]})


def start_server(port=8080):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def make_state():
    s = FreeplayState(health=80, goal="find the lighthouse")
    s.add_item("gun", "6 rounds")
    s.note("You stand at a crossroads.")
    return s


def test_clean_response():
    RESPONSE["content"] = json.dumps({
        "narration": "You fire a warning shot into the air.",
        "health_delta": -5,
        "inventory_add": [{"name": "spent shell", "detail": ""}],
        "inventory_update": [{"name": "gun", "detail": "5 rounds"}],
        "inventory_remove": [],
    })
    result = ai.interpret_freeplay_action(make_state(), "fire the gun into the air")
    assert result["health_delta"] == -5
    assert result["inventory_update"][0]["detail"] == "5 rounds"
    print("test_clean_response OK")


def test_huge_values_pass_through_raw_but_engine_clamps_later():
    # interpret_freeplay_action itself doesn't clamp numeric bounds (that's
    # apply_turn_result's job) -- it should just safely coerce types.
    RESPONSE["content"] = json.dumps({
        "narration": "Something huge happens.",
        "health_delta": 999999,
        "inventory_add": [{"name": f"item{i}", "detail": ""} for i in range(10)],
        "inventory_update": [],
        "inventory_remove": [],
    })
    result = ai.interpret_freeplay_action(make_state(), "do something absurd")
    assert result["health_delta"] == 999999  # raw pass-through, coerced to int
    assert len(result["inventory_add"]) == 2  # but capped to 2 here already
    print("test_huge_values_pass_through_raw_but_engine_clamps_later OK")


def test_missing_keys():
    RESPONSE["content"] = json.dumps({"narration": "Just a narration, nothing else."})
    result = ai.interpret_freeplay_action(make_state(), "look around")
    assert result["health_delta"] == 0
    assert result["inventory_add"] == []
    assert result["inventory_update"] == []
    assert result["inventory_remove"] == []
    print("test_missing_keys OK")


def test_bad_types_do_not_crash():
    RESPONSE["content"] = json.dumps({
        "narration": None,
        "health_delta": "a lot",
        "inventory_add": "not a list",
        "inventory_update": [{"name": 123, "detail": None}, {"detail": "no name field"}],
        "inventory_remove": "also not a list",
    })
    result = ai.interpret_freeplay_action(make_state(), "do something weird")
    assert result["health_delta"] == 0
    assert result["inventory_add"] == []
    assert result["inventory_update"] == []  # both entries invalid (bad name types)
    assert result["inventory_remove"] == []
    assert isinstance(result["narration"], str) and len(result["narration"]) > 0
    print("test_bad_types_do_not_crash OK")


def test_chatty_wrapped_json_still_parses():
    RESPONSE["content"] = ("Sure! Here's what happens:\n" + json.dumps({
        "narration": "You climb the ridge carefully.",
        "health_delta": 0, "inventory_add": [], "inventory_update": [], "inventory_remove": [],
    }) + "\nLet me know what's next!")
    result = ai.interpret_freeplay_action(make_state(), "climb the ridge")
    assert "climb the ridge" in result["narration"].lower()
    print("test_chatty_wrapped_json_still_parses OK")


def test_model_refuses_json_entirely():
    RESPONSE["content"] = "I will not provide JSON."
    result = ai.interpret_freeplay_action(make_state(), "try anyway")
    assert result["health_delta"] == 0
    assert "attempts it" in result["narration"] or "try anyway" in result["narration"].lower()
    print("test_model_refuses_json_entirely OK")


def test_no_action_text_short_circuits():
    result = ai.interpret_freeplay_action(make_state(), "   ")
    assert result["health_delta"] == 0
    print("test_no_action_text_short_circuits OK")


if __name__ == "__main__":
    server = start_server(8080)
    try:
        time.sleep(0.2)
        ai = LocalAI()
        assert ai.available and ai.backend == "llamacpp"

        test_clean_response()
        test_huge_values_pass_through_raw_but_engine_clamps_later()
        test_missing_keys()
        test_bad_types_do_not_crash()
        test_chatty_wrapped_json_still_parses()
        test_model_refuses_json_entirely()
        test_no_action_text_short_circuits()
        print("\nAll interpret_freeplay_action tests passed.")
    finally:
        server.shutdown()
