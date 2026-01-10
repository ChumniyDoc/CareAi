from bot.services.inbox import classify_message


def test_classify_task():
    result = classify_message("купить молоко завтра")
    assert result.kind == "task"


def test_classify_note():
    result = classify_message("просто заметка")
    assert result.kind == "note"
