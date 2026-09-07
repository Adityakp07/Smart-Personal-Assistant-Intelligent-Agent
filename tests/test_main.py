from src.main import perceive, decide


def test_greeting():
    assert decide(perceive("hello")) == "greeting"


def test_datetime():
    assert decide(perceive("what is the time?")) == "datetime"


def test_add_note():
    assert decide(perceive("add note")) == "add_note"


def test_view_notes():
    assert decide(perceive("show notes")) == "view_notes"


def test_add_reminder():
    assert decide(perceive("add reminder")) == "add_reminder"


def test_view_reminders():
    assert decide(perceive("show reminders")) == "view_reminders"


def test_calculator():
    assert decide(perceive("calculate")) == "calculator"


def test_unknown():
    assert decide(perceive("blah xyz")) == "unknown"