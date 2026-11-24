#!/usr/bin/env python3
"""F6 · Paired Rungs — Side-by-side countable dual-ladder comparison chart.

Two rung ladders per category (e.g. Last Year vs This Year, Plan vs Actual):
secondary theme color on the left, primary theme color on the right, with clear
delta/value readouts above each ladder.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

from palette import ThemePalette
from svg_builder import FrameLayout, SvgCanvas, fmt, format_number, rnd


def _choose_unit(max_val: float, max_rungs: int, explicit_unit: float | None) -> float:
    if explicit_unit and explicit_unit > 0:
        return float(explicit_unit)
    if max_val <= max_rungs:
        return 1.0
    raw = max_val / max_rungs
    mag = 10 ** math.floor(math.log10(raw))
    for mult in (1, 2, 2.5, 5, 10):
        cand = mult * mag
        if max_val / cand <= max_rungs:
            return cand
    return 10 * mag


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    items: List[Dict[str, Any]] = spec["data"]
    if not items:
        raise ValueError("paired_rungs requires non-empty 'data' list")

    title = spec.get("title", "This period against last")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "PAIRED RUNGS")
    series_names = spec.get("series_names", ["Before", "After"])
    prefix = spec.get("value_prefix", "")
    suffix = spec.get("value_suffix", "")
    unit_label = spec.get("unit_label", "")

    a_vals = [max(0.0, float(d["a"])) for d in items]
    b_vals = [max(0.0, float(d["b"])) for d in items]
    max_val = max(a_vals + b_vals) or 1.0
    max_rungs_cap = 36 if layout.mode == "slide" else 26
    unit_val = _choose_unit(max_val, max_rungs_cap, spec.get("unit_value"))

    a_rungs = [max(1, int(round(v / unit_val))) if v > 0 else 0 for v in a_vals]
    b_rungs = [max(1, int(round(v / unit_val))) if v > 0 else 0 for v in b_vals]
    max_rungs = max(a_rungs + b_rungs) or 1

    unit_note = spec.get("unit_note")
    if not unit_note:
        u_txt = format_number(unit_val, prefix, suffix)
        if unit_label:
            u_txt = f"{u_txt} {unit_label}".strip()
        unit_note = f"LEFT = {series_names[0]} · RIGHT = {series_names[1]} · ONE RUNG = {u_txt}"

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "paired-rungs"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    n = len(items)
    top_pad = 44.0 if layout.mode == "slide" else 34.0
    bot_pad = 44.0 if layout.mode == "slide" else 34.0
    side_pad = max(36.0, layout.chart_w * 0.05)

    x_left = layout.chart_x + side_pad
    x_right = layout.chart_right - side_pad
    base_y = layout.chart_bottom - bot_pad
    avail_h = max(80.0, base_y - (layout.chart_y + top_pad))
    step = min(13.0 if layout.mode == "slide" else 9.0, avail_h / max(max_rungs, 1))

    slot_w = (x_right - x_left) / max(n, 1)
    half_w = min(slot_w * 0.18, 30.0 if layout.mode == "slide" else 18.0)
    pair_offset = half_w + (10.0 if layout.mode == "slide" else 6.0)
    stroke_w = max(1.8, min(3.0, step * 0.36))

    # Inline legend top-right of chart area
    legend_g = canvas.add_group(area, "chart-legend")
    leg_y = layout.chart_y + 10.0
    leg_x = layout.chart_right - (240.0 if layout.mode == "slide" else 185.0)
    col_a = palette.c2
    col_b = palette.c1

    canvas.add_line(legend_g, leg_x, leg_y, leg_x + 22, leg_y, stroke=col_a, stroke_width=3.2, stroke_linecap="round")
    canvas.add_text(legend_g, leg_x + 30, leg_y + 4.5, str(series_names[0]), font_size=13.0 if layout.mode == "slide" else 12.0, font_weight=600, fill=palette.label)
    leg_x2 = leg_x + (120.0 if layout.mode == "slide" else 92.0)
    canvas.add_line(legend_g, leg_x2, leg_y, leg_x2 + 22, leg_y, stroke=col_b, stroke_width=3.2, stroke_linecap="round")
    canvas.add_text(legend_g, leg_x2 + 30, leg_y + 4.5, str(series_names[1]), font_size=13.0 if layout.mode == "slide" else 12.0, font_weight=700, fill=palette.ink)

    grid_g = canvas.add_group(area, "chart-grid")
    canvas.add_line(
        grid_g,
        layout.chart_x + 8,
        base_y + step * 0.65,
        layout.chart_right - 8,
        base_y + step * 0.65,
        stroke=palette.grid,
        stroke_width=1.4,
    )
    canvas.add_comment(
        area,
        f"chart-plot-area: object={canvas.chart_id} | "
        f"{fmt(x_left)},{fmt(layout.chart_y + top_pad)},{fmt(x_right)},{fmt(base_y)}",
    )

    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    val_a_size = 13.5 if layout.mode == "slide" else 12.0
    val_b_size = 16.0 if layout.mode == "slide" else 13.0
    cat_size = 13.5 if layout.mode == "slide" else 12.0

    for i, item in enumerate(items):
        name = str(item["label"])
        cx = x_left + (i + 0.5) * slot_w
        xa = cx - pair_offset
        xb = cx + pair_offset
        grp = canvas.add_group(marks_g, f"pair-{i+1}")

        # Left ladder (series A)
        for k in range(a_rungs[i]):
            y = base_y - k * step
            w = half_w + (rnd(k + 1, i + 2) - 0.5) * (half_w * 0.16)
            op = 0.72 + rnd(k + 2, i + 3) * 0.22
            canvas.add_line(grp, xa - w, y, xa + w, y, stroke=col_a, stroke_width=stroke_w, stroke_opacity=op, stroke_linecap="round")

        # Right ladder (series B)
        for k in range(b_rungs[i]):
            y = base_y - k * step
            w = half_w + (rnd(k + 1, i + 7) - 0.5) * (half_w * 0.16)
            op = 0.84 + rnd(k + 2, i + 8) * 0.16
            canvas.add_line(grp, xb - w, y, xb + w, y, stroke=col_b, stroke_width=stroke_w, stroke_opacity=op, stroke_linecap="round")

        top_a = base_y - max(a_rungs[i] - 1, 0) * step
        top_b = base_y - max(b_rungs[i] - 1, 0) * step

        canvas.add_text(
            labels_g,
            xa,
            top_a - (12.0 if layout.mode == "slide" else 9.0),
            format_number(a_vals[i], prefix, suffix),
            font_size=val_a_size,
            font_weight=600,
            fill=col_a,
            text_anchor="middle",
        )
        canvas.add_text(
            labels_g,
            xb,
            top_b - (13.0 if layout.mode == "slide" else 10.0),
            format_number(b_vals[i], prefix, suffix),
            font_size=val_b_size,
            font_weight=800,
            fill=col_b,
            text_anchor="middle",
        )
        canvas.add_text(
            labels_g,
            cx,
            base_y + (28.0 if layout.mode == "slide" else 22.0),
            name,
            font_size=cat_size,
            font_weight=700,
            fill=palette.label,
            text_anchor="middle",
            letter_spacing=0.8,
        )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
