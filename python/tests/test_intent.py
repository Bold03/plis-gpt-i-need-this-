from copilot.intent import parse_intent


def test_bilingual_gear():
    assert parse_intent("gear up").name == "gear_up"
    assert parse_intent("tolong naikkan roda").name == "gear_up"
    assert parse_intent("turunkan roda").name == "gear_down"


def test_battery():
    assert parse_intent("nyalakan baterai").name == "battery_on"
    assert parse_intent("turn off battery").name == "battery_off"
