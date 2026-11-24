#!/usr/bin/env python3
"""L15 · Ballot Tally — Multi-select 100-respondent hairline tick rows.

Built specifically for multi-select survey percentages (each item independently
0-100%, sum may exceed 100%). Every option is a row of 100 vertical hairline
ticks representing 100 respondents standing in line; those who picked it stand
taller and inked in the theme color, with dot markers every 10th respondent.
"""

from __future__ import annotations

from typing import Any, Dict, List

from palette import ThemePalette
from svg_builder import FrameLayout, SvgCanvas, fmt, rnd


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    items: List[Dict[str, Any]] = spec["data"]
    if not items:
        raise ValueError("ballot_tally requires non-empty 'data' list")

    title = spec.get("title", "What respondents chose, tick by tick")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "BALLOT TALLY")
    highlight_idx = spec.get("highlight_index")
    unit_note = spec.get(
        "unit_note",
        "ONE TICK = ONE RESPONDENT IN 100 · INKED = PICKED IT · DOT MARKS EVERY TENTH",
    )

    vals = [max(0, min(100, int(round(float(d["value"]))))) for d in items]
    if highlight_idx is None:
        highlight_idx = vals.index(max(vals))

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "ballot-tally"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    n = len(items)
    pad_l = 24.0 if layout.mode == "slide" else 14.0
    pad_r = 24.0 if layout.mode == "slide" else 14.0
    top_pad = 34.0 if layout.mode == "slide" else 24.0
    bot_pad = 16.0 if layout.mode == "slide" else 12.0

    x0 = layout.chart_x + pad_l
    x1 = layout.chart_right - pad_r
    row_span = x1 - x0
    step_x = row_span / 99.0
    row_h = (layout.chart_h - top_pad - bot_pad) / max(n, 1)

    grid_g = canvas.add_group(area, "chart-grid")
    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    accent_col = palette.c3 if len(palette.colors) >= 3 else palette.c2
    lbl_size = 14.5 if layout.mode == "slide" else 12.0
    val_size = 20.0 if layout.mode == "slide" else 14.5
    inked_h_base = min(row_h * 0.34, 30.0 if layout.mode == "slide" else 20.0)
    unpicked_h_base = inked_h_base * 0.35
    dot_r = 2.0 if layout.mode == "slide" else 1.5

    for i, item in enumerate(items):
        v = vals[i]
        base_y = layout.chart_y + top_pad + (i + 0.68) * row_h
        is_hero = i == highlight_idx
        col = accent_col if is_hero else palette.c1

        # Option title above ticks
        canvas.add_text(
            labels_g,
            x0,
            base_y - inked_h_base - (14.0 if layout.mode == "slide" else 10.0),
            str(item["label"]),
            font_size=lbl_size,
            font_weight=700 if is_hero else 600,
            fill=palette.ink if is_hero else palette.label,
            letter_spacing=0.6,
        )

        # Full 100-person baseline
        canvas.add_line(grid_g, x0, base_y, x1, base_y, stroke=palette.grid, stroke_width=1.0)

        # Combine unpicked ticks into one clean multi-subpath path, and inked ticks into a second path
        inked_segs: List[str] = []
        quiet_segs: List[str] = []
        row_g = canvas.add_group(marks_g, f"ballot-{i+1}")

        for k in range(100):
            tx = x0 + k * step_x
            if k < v:
                h = inked_h_base * (0.76 + rnd(k + 1, i + 2) * 0.36)
                inked_segs.append(f"M {fmt(tx)} {fmt(base_y)} V {fmt(base_y - h)}")
            else:
                h = unpicked_h_base * (0.78 + rnd(k + 1, i + 5) * 0.44)
                quiet_segs.append(f"M {fmt(tx)} {fmt(base_y)} V {fmt(base_y - h)}")
            if k % 10 == 0:
                canvas.add_circle(row_g, tx, base_y + (8.0 if layout.mode == "slide" else 6.0), dot_r, fill=palette.faint)

        if quiet_segs:
            canvas.add_path(
                row_g,
                " ".join(quiet_segs),
                fill="none",
                stroke=palette.floor,
                stroke_width=1.2 if layout.mode == "slide" else 0.9,
            )
        if inked_segs:
            canvas.add_path(
                row_g,
                " ".join(inked_segs),
                fill="none",
                stroke=col,
                stroke_width=2.2 if layout.mode == "slide" else 1.5,
                stroke_linecap="round",
            )

        # Value readout neatly positioned after the last inked tick (or inside right if near 100)
        val_x = x0 + min(92, max(v, 1)) * step_x + (14.0 if layout.mode == "slide" else 10.0)
        anchor = "start"
        if v >= 88:
            val_x = x1
            anchor = "end"
        canvas.add_text(
            labels_g,
            val_x,
            base_y - inked_h_base * 0.42,
            f"{v}%",
            font_size=val_size,
            font_weight=800,
            fill=col,
            text_anchor=anchor,
        )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
