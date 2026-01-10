from bot.llm.parser import parse_intent_response


def test_parse_intent_response_valid():
    raw = '{"intent":"chat","reply":"ok","proposals":[]}'
    result = parse_intent_response(raw)
    assert result.intent == "chat"
    assert result.reply == "ok"
    assert result.valid_json is True


def test_parse_intent_response_invalid():
    raw = "not-json"
    result = parse_intent_response(raw)
    assert result.intent == "chat"
    assert result.reply == "not-json"
    assert result.valid_json is False
