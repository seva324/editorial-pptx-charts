#!/usr/bin/env python3
"""F5 · Tick Rows — Horizontal countable-tick queue bar chart.

Each row is a horizontal queue of vertical hairline ticks (1 tick = 1 unit,
dot marker every 5th tick) with bold end values. Ideal for ranked comparisons
and especially strong for Chinese or multi-word category labels.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

from palette import ThemePalette, mix_hex
from svg_builder import FrameLayout, SvgCanvas, estimate_text_width, fmt, format_number, rnd


def _choose_unit(max_val: float, max_ticks: int, explicit_unit: float | None) -> float:
    if explicit_unit and explicit_unit > 0:
        return float(explicit_unit)
    if max_val <= max_ticks:
        return 1.0
    raw = max_val / max_ticks
    mag = 10 ** math.floor(math.log10(raw))
    for mult in (1, 2, 2.5, 5, 10):
        cand = mult * mag
        if max_val / cand <= max_ticks:
            return cand
    return 10 * mag


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    items: List[Dict[str, Any]] = spec["data"]
    if not items:
        raise ValueError("tick_rows requires non-empty 'data' list")

    title = spec.get("title", "Ranked, tick by tick")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "TICK ROWS")
    unit_label = spec.get("unit_label", "")
    prefix = spec.get("value_prefix", "")
    suffix = spec.get("value_suffix", "")
    highlight_idx = spec.get("highlight_index")
    color_mode = spec.get("color_mode", "highlight")

    vals = [max(0.0, float(d["value"])) for d in items]
    max_val = max(vals) or 1.0
    max_ticks_cap = 45 if layout.mode == "slide" else 34
    unit_val = _choose_unit(max_val, max_ticks_cap, spec.get("unit_value"))
    tick_counts = [max(1, int(round(v / unit_val))) if v > 0 else 0 for v in vals]
    max_ticks = max(tick_counts) or 1

    if highlight_idx is None:
        highlight_idx = vals.index(max(vals))

    unit_note = spec.get("unit_note")
    if not unit_note:
        u_txt = format_number(unit_val, prefix, suffix)
        if unit_label:
            u_txt = f"{u_txt} {unit_label}".strip()
        unit_note = f"ONE TICK = {u_txt} · DOT MARKS EVERY FIFTH"

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "tick-rows"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    n = len(items)
    lbl_size = 14.5 if layout.mode == "slide" else 12.0
    max_lbl_px = max(estimate_text_width(str(d["label"]), lbl_size) for d in items)
    left_rail = min(
        layout.chart_w * 0.30,
        max(110.0 if layout.mode == "slide" else 88.0, max_lbl_px + 26.0),
    )
    right_rail = 96.0 if layout.mode == "slide" else 68.0
    x0 = layout.chart_x + left_rail
    x1 = layout.chart_right - right_rail
    avail_w = max(120.0, x1 - x0)
    px = avail_w / max(max_ticks, 1)

    top_pad = 24.0 if layout.mode == "slide" else 16.0
    bot_pad = 18.0 if layout.mode == "slide" else 14.0
    row_h = (layout.chart_h - top_pad - bot_pad) / max(n, 1)
    tick_h_base = min(row_h * 0.42, 26.0 if layout.mode == "slide" else 18.0)
    stroke_w = max(1.6, min(2.8, px * 0.34))

    canvas.add_comment(
        area,
        f"chart-plot-area: object={canvas.chart_id} | "
        f"{fmt(x0)},{fmt(layout.chart_y + top_pad)},{fmt(x1)},{fmt(layout.chart_bottom - bot_pad)}",
    )

    grid_g = canvas.add_group(area, "chart-grid")
    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    lbl_size = 14.5 if layout.mode == "slide" else 12.0
    val_size = 18.0 if layout.mode == "slide" else 14.0
    dot_r = 2.0 if layout.mode == "slide" else 1.5

    for i, item in enumerate(items):
        name = str(item["label"])
        v = vals[i]
        ticks = tick_counts[i]
        cy = layout.chart_y + top_pad + (i + 0.5) * row_h
        base_y = cy + tick_h_base * 0.42
        is_hero = i == highlight_idx

        if color_mode == "categorical":
            col = palette.series_color(i)
        elif color_mode == "ramp":
            t = i / max(n - 1, 1)
            col = mix_hex(palette.c1, palette.c2, t) if len(palette.colors) >= 2 else palette.ramp6[min(i, 5)]
        else:
            col = (palette.c3 if len(palette.colors) >= 3 else palette.c2) if is_hero else palette.c1

        # Category label
        canvas.add_text(
            labels_g,
            x0 - 16.0,
            cy + lbl_size * 0.32,
            name,
            font_size=lbl_size,
            font_weight=700 if is_hero else 600,
            fill=palette.ink if is_hero else palette.label,
            text_anchor="end",
            letter_spacing=0.6,
        )

        # Ledger baseline across full width
        canvas.add_line(
            grid_g,
            x0,
            base_y,
            x1,
            base_y,
            stroke=palette.grid,
            stroke_width=1.0,
        )

        # Ticks
        row_g = canvas.add_group(marks_g, f"row-{i+1}")
        for k in range(ticks):
            tx = x0 + (k + 0.5) * px
            th = tick_h_base * (0.76 + rnd(k + 1, i + 2) * 0.44)
            op = 0.82 + rnd(k + 3, i + 5) * 0.18
            canvas.add_line(
                row_g,
                tx,
                base_y,
                tx,
                base_y - th,
                stroke=col,
                stroke_width=stroke_w,
                stroke_opacity=op,
                stroke_linecap="round",
            )
            if k % 5 == 4:
                canvas.add_circle(
                    row_g,
                    tx,
                    base_y + (8.0 if layout.mode == "slide" else 6.0),
                    dot_r,
                    fill=palette.faint,
                )

        # Value label at end of queue
        end_x = x0 + ticks * px + (16.0 if layout.mode == "slide" else 11.0)
        canvas.add_text(
            labels_g,
            end_x,
            cy + val_size * 0.32,
            format_number(v, prefix, suffix),
            font_size=val_size,
            font_weight=800 if is_hero else 700,
            fill=col if is_hero else palette.ink,
        )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
