from bot.llm.parser import parse_llm_response


def test_parse_llm_response_valid_json():
    raw = '{"response":"ok","proposals":[{"tool":"create_task","args":{"title":"test"},"reason":"x"}]}'
    result = parse_llm_response(raw)
    assert result.response == "ok"
    assert len(result.proposals) == 1
    assert result.proposals[0].tool == "create_task"
    assert result.proposals[0].args["title"] == "test"


def test_parse_llm_response_invalid_json():
    raw = "not-json"
    result = parse_llm_response(raw)
    assert result.response == "not-json"
    assert result.proposals == []
