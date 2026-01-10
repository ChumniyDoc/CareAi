from __future__ import annotations

import io
import matplotlib.pyplot as plt


def build_week_chart(days: list[str], mood: list[int], energy: list[int], stress: list[int]) -> bytes:
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(days, mood, label="Настроение")
    ax.plot(days, energy, label="Энергия")
    ax.plot(days, stress, label="Стресс")
    ax.legend()
    ax.set_title("Последние 7 дней")
    ax.set_xlabel("День")
    ax.set_ylabel("Балл")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf.read()
