from bot.jobs.jobs import BriefingData, ReflectionData, build_evening_reflection, build_morning_briefing


def test_build_morning_briefing():
    text = build_morning_briefing(
        BriefingData(tasks=["Задача 1"], next_reminder="10:00", workday_label="Рабочий день")
    )
    assert "Задача 1" in text


def test_build_evening_reflection():
    text = build_evening_reflection(ReflectionData(questions=["Q1", "Q2"]))
    assert "Q1" in text
