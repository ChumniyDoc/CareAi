from __future__ import annotations

import datetime as dt
import hashlib
from dataclasses import dataclass
from typing import Iterable

from dateutil import tz
from lxml import etree

STEP_TYPE = "HKQuantityTypeIdentifierStepCount"
DISTANCE_TYPE = "HKQuantityTypeIdentifierDistanceWalkingRunning"
ENERGY_TYPE = "HKQuantityTypeIdentifierActiveEnergyBurned"
SLEEP_TYPE = "HKCategoryTypeIdentifierSleepAnalysis"
HEART_RATE_TYPE = "HKQuantityTypeIdentifierHeartRate"


@dataclass(slots=True)
class HealthRecord:
    source: str | None
    record_type: str
    start_at: dt.datetime
    end_at: dt.datetime
    value: str | None
    unit: str | None
    raw_json: dict


@dataclass(slots=True)
class HealthAggregate:
    date: dt.date
    steps: int | None = None
    distance: float | None = None
    active_energy: float | None = None
    sleep_duration: float | None = None
    avg_hr: float | None = None
    min_hr: float | None = None
    max_hr: float | None = None


def compute_import_id(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_export(xml_bytes: bytes, timezone: str) -> list[HealthRecord]:
    root = etree.fromstring(xml_bytes)
    records: list[HealthRecord] = []
    tzinfo = tz.gettz(timezone)
    for record in root.findall("Record"):
        record_type = record.get("type")
        start = _parse_date(record.get("startDate"), tzinfo)
        end = _parse_date(record.get("endDate"), tzinfo)
        value = record.get("value")
        unit = record.get("unit")
        source = record.get("sourceName")
        raw = {"attrib": record.attrib}
        records.append(
            HealthRecord(
                source=source,
                record_type=record_type,
                start_at=start,
                end_at=end,
                value=value,
                unit=unit,
                raw_json=raw,
            )
        )
    return records


def aggregate_daily(records: Iterable[HealthRecord]) -> dict[dt.date, HealthAggregate]:
    aggregates: dict[dt.date, HealthAggregate] = {}
    hr_values: dict[dt.date, list[float]] = {}
    for record in records:
        day = record.start_at.date()
        agg = aggregates.setdefault(day, HealthAggregate(date=day))
        if record.record_type == STEP_TYPE and record.value:
            agg.steps = (agg.steps or 0) + int(float(record.value))
        if record.record_type == DISTANCE_TYPE and record.value:
            agg.distance = (agg.distance or 0) + float(record.value)
        if record.record_type == ENERGY_TYPE and record.value:
            agg.active_energy = (agg.active_energy or 0) + float(record.value)
        if record.record_type == SLEEP_TYPE:
            duration = (record.end_at - record.start_at).total_seconds() / 3600
            agg.sleep_duration = (agg.sleep_duration or 0) + duration
        if record.record_type == HEART_RATE_TYPE and record.value:
            hr_values.setdefault(day, []).append(float(record.value))

    for day, values in hr_values.items():
        agg = aggregates.setdefault(day, HealthAggregate(date=day))
        agg.avg_hr = sum(values) / len(values)
        agg.min_hr = min(values)
        agg.max_hr = max(values)
    return aggregates


def _parse_date(value: str | None, tzinfo: dt.tzinfo | None) -> dt.datetime:
    if not value:
        return dt.datetime.now(tzinfo)
    parsed = dt.datetime.strptime(value, "%Y-%m-%d %H:%M:%S %z")
    if tzinfo:
        return parsed.astimezone(tzinfo)
    return parsed
