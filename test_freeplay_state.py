from engine.freeplay import FreeplayState, apply_turn_result, HEALTH_DELTA_BOUNDS, MAX_NEW_ITEMS_PER_TURN


def test_add_find_update_remove_item():
    s = FreeplayState()
    s.add_item("Gun", "6 rounds")
    assert s.find_item("gun") is not None  # case-insensitive
    assert s.find_item("gun")["detail"] == "6 rounds"

    s.update_item("gun", "5 rounds")
    assert s.find_item("Gun")["detail"] == "5 rounds"

    s.add_item("Rope")
    assert len(s.inventory) == 2

    # adding an already-present item with a new detail just updates it, doesn't duplicate
    s.add_item("gun", "4 rounds")
    assert len(s.inventory) == 2
    assert s.find_item("gun")["detail"] == "4 rounds"

    s.remove_item("rope")
    assert len(s.inventory) == 1
    assert s.find_item("rope") is None

    # updating a not-yet-present item just adds it
    s.update_item("Torch", "half burned")
    assert s.find_item("torch")["detail"] == "half burned"
    print("test_add_find_update_remove_item OK")


def test_health_clamps_and_death():
    s = FreeplayState(health=50)
    s.apply_health_delta(-1000)
    assert s.health == 0
    assert s.alive is False

    s2 = FreeplayState(health=90)
    s2.apply_health_delta(1000)
    assert s2.health == 100
    assert s2.alive is True
    print("test_health_clamps_and_death OK")


def test_apply_turn_result_clamps_health_delta():
    s = FreeplayState(health=50)
    apply_turn_result(s, {"health_delta": 99999})
    assert s.health == 50 + HEALTH_DELTA_BOUNDS[1]

    s2 = FreeplayState(health=50)
    apply_turn_result(s2, {"health_delta": -99999})
    assert s2.health == max(0, 50 + HEALTH_DELTA_BOUNDS[0])
    print("test_apply_turn_result_clamps_health_delta OK")


def test_apply_turn_result_caps_new_items():
    s = FreeplayState()
    many_items = [{"name": f"item{i}", "detail": ""} for i in range(10)]
    apply_turn_result(s, {"health_delta": 0, "inventory_add": many_items})
    assert len(s.inventory) == MAX_NEW_ITEMS_PER_TURN
    print("test_apply_turn_result_caps_new_items OK")


def test_apply_turn_result_update_and_remove():
    s = FreeplayState()
    s.add_item("torch", "full")
    apply_turn_result(s, {
        "health_delta": 0,
        "inventory_update": [{"name": "torch", "detail": "half burned"}],
    })
    assert s.find_item("torch")["detail"] == "half burned"

    apply_turn_result(s, {"health_delta": 0, "inventory_remove": ["torch"]})
    assert s.find_item("torch") is None
    print("test_apply_turn_result_update_and_remove OK")


def test_apply_turn_result_missing_keys_are_safe():
    s = FreeplayState(health=80)
    apply_turn_result(s, {})  # no keys at all
    assert s.health == 80
    assert s.inventory == []
    print("test_apply_turn_result_missing_keys_are_safe OK")


if __name__ == "__main__":
    test_add_find_update_remove_item()
    test_health_clamps_and_death()
    test_apply_turn_result_clamps_health_delta()
    test_apply_turn_result_caps_new_items()
    test_apply_turn_result_update_and_remove()
    test_apply_turn_result_missing_keys_are_safe()
    print("\nAll Freeplay state tests passed.")
