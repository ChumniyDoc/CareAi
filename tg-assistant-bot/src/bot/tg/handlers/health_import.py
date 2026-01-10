from __future__ import annotations

import io
import zipfile

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import load_settings
from bot.db import models, repo
from bot.services.apple_health import aggregate_daily, compute_import_id, parse_export

router = Router()


@router.message(Command("health"))
async def health_help(message: Message) -> None:
    await message.answer("Отправь ZIP из Apple Health (Export All Health Data).")


@router.message(F.document)
async def handle_health_zip(message: Message, session: AsyncSession, bot) -> None:
    document = message.document
    if not document.file_name or not document.file_name.lower().endswith(".zip"):
        return
    user = await repo.get_or_create_user(session, message.from_user.id)
    file = await bot.get_file(document.file_id)
    content = await bot.download_file(file.file_path)
    data = content.read()
    import_id = compute_import_id(data)
    if await repo.has_health_import(session, import_id):
        await message.answer("Этот файл уже импортирован.")
        return
    settings = load_settings()
    zip_bytes = io.BytesIO(data)
    with zipfile.ZipFile(zip_bytes) as zf:
        with zf.open("export.xml") as xml_file:
            xml_bytes = xml_file.read()
    records = parse_export(xml_bytes, settings.tz)
    await repo.store_health_import(session, user.id, import_id)
    raw_records = [
        models.AppleHealthRawRecord(
            user_id=user.id,
            import_id=import_id,
            source=record.source,
            record_type=record.record_type,
            start_at=record.start_at,
            end_at=record.end_at,
            value=record.value,
            unit=record.unit,
            raw_json=record.raw_json,
        )
        for record in records
    ]
    await repo.store_health_raw_records(session, raw_records)
    aggregates = aggregate_daily(records)
    for aggregate in aggregates.values():
        await repo.upsert_health_aggregate(
            session,
            models.AppleHealthDailyAggregate(
                user_id=user.id,
                date=aggregate.date,
                steps=aggregate.steps,
                distance=aggregate.distance,
                active_energy=aggregate.active_energy,
                sleep_duration=aggregate.sleep_duration,
                avg_hr=aggregate.avg_hr,
                min_hr=aggregate.min_hr,
                max_hr=aggregate.max_hr,
            ),
        )
    await session.commit()
    await message.answer("Импорт завершен.")
