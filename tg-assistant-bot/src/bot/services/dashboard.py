from __future__ import annotations

import io
import matplotlib.pyplot as plt


def build_simple_chart(title: str, labels: list[str], values: list[float]) -> bytes:
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(labels, values, marker="o")
    ax.set_title(title)
    ax.set_xlabel("День")
    ax.set_ylabel("Значение")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf.read()
