from bot.services.habits import handle_alcohol_portion, normalize_trigger


def test_trigger_detect():
    assert normalize_trigger("Была тяга") is True


def test_alcohol_relapse():
    result = handle_alcohol_portion(1)
    assert result.relapse is True


def test_alcohol_no_relapse():
    result = handle_alcohol_portion(0)
    assert result.relapse is False
