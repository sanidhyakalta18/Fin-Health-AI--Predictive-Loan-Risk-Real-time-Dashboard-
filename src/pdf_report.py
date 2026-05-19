"""
Lightweight PDF risk report generation.

The project intentionally avoids a heavyweight PDF dependency here. This module
creates a clean, text-and-vector PDF using basic PDF drawing commands.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.core.config import get_config

PAGE_W = 612
PAGE_H = 792
MARGIN = 46
CONTENT_W = PAGE_W - (MARGIN * 2)


def _clean_text(value: Any) -> str:
    text = str(value)
    replacements = {
        "\u2014": "-",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2265": ">=",
        "\u25b2": "^",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode("latin-1", "replace").decode("latin-1")


def _pdf_escape(value: Any) -> str:
    text = _clean_text(value)
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _wrap(text: Any, max_chars: int) -> list[str]:
    words = _clean_text(text).split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


class _PdfCanvas:
    def __init__(self) -> None:
        self.pages: list[list[str]] = []
        self.ops: list[str] = []
        self.y = PAGE_H - MARGIN
        self.add_page()

    def add_page(self) -> None:
        if self.ops:
            self.pages.append(self.ops)
        self.ops = []
        self.y = PAGE_H - MARGIN
        self.fill_rgb(0.98, 0.99, 1.0)
        self.rect(0, 0, PAGE_W, PAGE_H, fill=True)

    def ensure_space(self, needed: float) -> None:
        if self.y - needed < MARGIN:
            self.add_page()

    def fill_rgb(self, r: float, g: float, b: float) -> None:
        self.ops.append(f"{r:.3f} {g:.3f} {b:.3f} rg")

    def stroke_rgb(self, r: float, g: float, b: float) -> None:
        self.ops.append(f"{r:.3f} {g:.3f} {b:.3f} RG")

    def line_width(self, width: float) -> None:
        self.ops.append(f"{width:.2f} w")

    def rect(self, x: float, y: float, w: float, h: float, *, fill: bool = False) -> None:
        self.ops.append(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re {'f' if fill else 'S'}")

    def line(self, x1: float, y1: float, x2: float, y2: float) -> None:
        self.ops.append(f"{x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S")

    def text(
        self,
        value: Any,
        x: float,
        y: float,
        *,
        size: int = 10,
        font: str = "F1",
        color: tuple[float, float, float] = (0.10, 0.14, 0.22),
    ) -> None:
        self.fill_rgb(*color)
        self.ops.append(f"BT /{font} {size} Tf {x:.2f} {y:.2f} Td ({_pdf_escape(value)}) Tj ET")

    def paragraph(
        self,
        value: Any,
        *,
        x: float = MARGIN,
        max_chars: int = 92,
        size: int = 10,
        leading: float = 14,
        color: tuple[float, float, float] = (0.25, 0.32, 0.42),
    ) -> None:
        lines = _wrap(value, max_chars)
        self.ensure_space(len(lines) * leading + 4)
        for line in lines:
            self.text(line, x, self.y, size=size, color=color)
            self.y -= leading

    def section_title(self, value: str) -> None:
        self.ensure_space(28)
        self.y -= 8
        self.text(value, MARGIN, self.y, size=15, font="F2", color=(0.06, 0.10, 0.18))
        self.y -= 10
        self.stroke_rgb(0.84, 0.88, 0.94)
        self.line_width(0.8)
        self.line(MARGIN, self.y, PAGE_W - MARGIN, self.y)
        self.y -= 18

    def finish(self) -> bytes:
        if self.ops:
            self.pages.append(self.ops)

        objects: list[bytes] = []
        objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        page_refs = " ".join(f"{3 + i * 2} 0 R" for i in range(len(self.pages)))
        objects.append(f"<< /Type /Pages /Kids [{page_refs}] /Count {len(self.pages)} >>".encode())

        for idx, page_ops in enumerate(self.pages):
            page_obj = 3 + idx * 2
            content_obj = page_obj + 1
            page = (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_W} {PAGE_H}] "
                f"/Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> "
                f"/F2 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >> >> >> "
                f"/Contents {content_obj} 0 R >>"
            )
            objects.append(page.encode())
            stream = "\n".join(page_ops).encode("latin-1", "replace")
            objects.append(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")

        pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for obj_num, obj in enumerate(objects, start=1):
            offsets.append(len(pdf))
            pdf.extend(f"{obj_num} 0 obj\n".encode())
            pdf.extend(obj)
            pdf.extend(b"\nendobj\n")
        xref_pos = len(pdf)
        pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode())
        pdf.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            pdf.extend(f"{offset:010d} 00000 n \n".encode())
        pdf.extend(
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_pos}\n%%EOF\n".encode()
        )
        return bytes(pdf)


def _extract_shap_bars(fig: Any, limit: int = 6) -> list[tuple[str, float]]:
    try:
        trace = fig.data[0]
        labels = list(trace.y)
        values = [float(v) for v in trace.x]
    except Exception:
        return []
    rows = list(zip(labels, values))
    rows.sort(key=lambda item: abs(item[1]), reverse=True)
    return rows[:limit]


def _draw_kv_table(canvas: _PdfCanvas, rows: list[tuple[str, str]], *, cols: int = 2) -> None:
    card_w = (CONTENT_W - 14) / cols
    card_h = 42
    for idx, (label, value) in enumerate(rows):
        col = idx % cols
        if col == 0:
            canvas.ensure_space(card_h + 12)
        x = MARGIN + col * (card_w + 14)
        y = canvas.y - card_h
        canvas.fill_rgb(1, 1, 1)
        canvas.rect(x, y, card_w, card_h, fill=True)
        canvas.stroke_rgb(0.86, 0.89, 0.94)
        canvas.rect(x, y, card_w, card_h)
        canvas.text(label.upper(), x + 12, y + 25, size=7, font="F2", color=(0.39, 0.45, 0.55))
        canvas.text(value, x + 12, y + 10, size=12, font="F2", color=(0.06, 0.10, 0.18))
        if col == cols - 1 or idx == len(rows) - 1:
            canvas.y -= card_h + 12


def _draw_probability_chart(canvas: _PdfCanvas, probability: float) -> None:
    canvas.ensure_space(82)
    x = MARGIN
    y = canvas.y - 58
    w = CONTENT_W
    h = 18
    canvas.text("Default Probability", x, canvas.y, size=10, font="F2")
    canvas.y -= 18
    canvas.fill_rgb(0.91, 0.94, 0.97)
    canvas.rect(x, y, w, h, fill=True)
    color = (
        (0.72, 0.11, 0.11)
        if probability >= get_config().high_risk_threshold
        else (0.06, 0.50, 0.31)
    )
    canvas.fill_rgb(*color)
    canvas.rect(x, y, max(2, min(w, w * probability)), h, fill=True)
    canvas.text(f"{probability:.1%}", x + w - 48, y + 4, size=10, font="F2", color=(0.06, 0.10, 0.18))
    canvas.y = y - 18


def _draw_shap_chart(canvas: _PdfCanvas, shap_rows: list[tuple[str, float]]) -> None:
    if not shap_rows:
        canvas.paragraph("SHAP chart unavailable for this report.")
        return
    canvas.ensure_space(30 + len(shap_rows) * 30)
    canvas.text("Top SHAP Drivers", MARGIN, canvas.y, size=10, font="F2")
    canvas.y -= 18
    max_abs = max(abs(v) for _, v in shap_rows) or 1.0
    label_w = 135
    mid_x = MARGIN + label_w + 150
    bar_max = 135
    canvas.stroke_rgb(0.78, 0.83, 0.90)
    canvas.line(mid_x, canvas.y + 5, mid_x, canvas.y - (len(shap_rows) * 28) + 8)
    for label, value in shap_rows:
        canvas.text(label, MARGIN, canvas.y - 3, size=9, color=(0.25, 0.32, 0.42))
        bar_w = (abs(value) / max_abs) * bar_max
        if value >= 0:
            canvas.fill_rgb(0.72, 0.11, 0.11)
            canvas.rect(mid_x, canvas.y - 6, bar_w, 10, fill=True)
        else:
            canvas.fill_rgb(0.15, 0.39, 0.92)
            canvas.rect(mid_x - bar_w, canvas.y - 6, bar_w, 10, fill=True)
        canvas.text(f"{value:+.4f}", mid_x + bar_max + 12, canvas.y - 4, size=8, color=(0.39, 0.45, 0.55))
        canvas.y -= 28
    canvas.y -= 8


def build_risk_report_pdf(
    *,
    input_data: dict[str, Any],
    result: dict[str, Any],
    insights: list[dict[str, str]],
    shap_fig: Any | None,
    generated_at: datetime | None = None,
) -> bytes:
    """Build a downloadable applicant risk report PDF."""
    generated_at = generated_at or datetime.now(timezone.utc)
    probability = float(result["probability_score"])
    prediction = str(result["prediction"])
    shap_rows = _extract_shap_bars(shap_fig)

    canvas = _PdfCanvas()
    canvas.fill_rgb(0.06, 0.10, 0.18)
    canvas.rect(0, PAGE_H - 116, PAGE_W, 116, fill=True)
    canvas.text("Fin-Health AI", MARGIN, PAGE_H - 55, size=22, font="F2", color=(1, 1, 1))
    canvas.text("Applicant Risk Report", MARGIN, PAGE_H - 82, size=12, color=(0.78, 0.86, 0.96))
    canvas.text(
        f"Generated {generated_at.strftime('%Y-%m-%d %H:%M UTC')}",
        PAGE_W - 235,
        PAGE_H - 55,
        size=9,
        color=(0.78, 0.86, 0.96),
    )
    canvas.y = PAGE_H - 148

    canvas.section_title("Executive Summary")
    canvas.paragraph(
        f"The model classified this applicant as {prediction} with an estimated default probability of "
        f"{probability:.1%}. This report summarizes applicant attributes, decision signals, SHAP drivers, "
        "and generated financial insights for underwriting review."
    )
    _draw_kv_table(
        canvas,
        [
            ("Risk Category", prediction),
            ("Default Probability", f"{probability:.1%}"),
            ("Credit Score", f"{float(input_data['Credit Score']):.0f}"),
            ("Debt-to-Income", f"{float(input_data['Debt']):.0%}"),
        ],
    )

    canvas.section_title("Applicant Details")
    _draw_kv_table(
        canvas,
        [
            ("Age", f"{float(input_data['Age']):.0f}"),
            ("Annual Income", f"${float(input_data['Income']):,.0f}"),
            ("Loan Amount", f"${float(input_data['Loan']):,.0f}"),
            ("Employment Years", f"{float(input_data['Employment Years']):.0f}"),
        ],
    )

    canvas.section_title("Risk Visualization")
    _draw_probability_chart(canvas, probability)
    _draw_shap_chart(canvas, shap_rows)

    canvas.section_title("SHAP Explanation Summary")
    if shap_rows:
        for label, value in shap_rows[:5]:
            direction = "increases default risk" if value > 0 else "lowers default risk"
            canvas.paragraph(f"{label}: {direction} with SHAP contribution {value:+.4f}.", max_chars=88)
    else:
        canvas.paragraph("SHAP explanation data was unavailable when this report was generated.")

    canvas.section_title("Generated Financial Insights")
    for insight in insights:
        canvas.ensure_space(58)
        canvas.text(insight["title"], MARGIN, canvas.y, size=11, font="F2", color=(0.06, 0.10, 0.18))
        canvas.y -= 14
        canvas.paragraph(insight["body"], max_chars=92)
        canvas.y -= 4

    canvas.section_title("Review Notes")
    canvas.paragraph(
        "This PDF is a decision-support artifact for portfolio and underwriting review. It should be used "
        "alongside policy rules, verification checks, and human credit judgment."
    )
    return canvas.finish()
