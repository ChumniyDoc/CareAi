from pathlib import Path

from bot.services.apple_health import aggregate_daily, parse_export


def test_parse_and_aggregate():
    xml_path = Path(__file__).parents[1] / "fixtures" / "health_export.xml"
    xml_bytes = xml_path.read_bytes()
    records = parse_export(xml_bytes, "Asia/Almaty")
    aggregates = aggregate_daily(records)
    assert len(records) == 3
    assert len(aggregates) == 1
    day = next(iter(aggregates.values()))
    assert day.steps == 100
    assert day.sleep_duration == 6
