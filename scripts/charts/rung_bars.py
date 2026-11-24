#!/usr/bin/env python3
"""F1 · Rung Bars — Vertical countable-rung editorial bar chart.

Every horizontal rung represents one real data unit (auto-scaled cleanly when
values are large, with an honest unit note). Every 5th rung gets a subtle dot
marker on the right margin. Uses the 2-3 theme-color palette: leader/hero bar
highlighted in primary/accent or ordered along the custom theme ramp.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

from palette import ThemePalette, mix_hex
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
        raise ValueError("rung_bars requires non-empty 'data' list")

    title = spec.get("title", "Comparison, rung by rung")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "RUNG BARS")
    unit_label = spec.get("unit_label", "")
    prefix = spec.get("value_prefix", "")
    suffix = spec.get("value_suffix", "")
    highlight_idx = spec.get("highlight_index")
    color_mode = spec.get("color_mode", "highlight")  # "highlight" | "ramp" | "categorical"

    vals = [max(0.0, float(d["value"])) for d in items]
    max_val = max(vals) or 1.0
    max_rungs_cap = 38 if layout.mode == "slide" else 28
    unit_val = _choose_unit(max_val, max_rungs_cap, spec.get("unit_value"))
    rung_counts = [max(1, int(round(v / unit_val))) if v > 0 else 0 for v in vals]
    max_rungs = max(rung_counts) or 1

    if highlight_idx is None:
        highlight_idx = vals.index(max(vals))

    unit_note = spec.get("unit_note")
    if not unit_note:
        u_txt = format_number(unit_val, prefix, suffix)
        if unit_label:
            u_txt = f"{u_txt} {unit_label}".strip()
        unit_note = f"ONE RUNG = {u_txt} · DOT MARKS EVERY FIFTH"

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "rung-bars"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    # Plot coordinates
    n = len(items)
    top_pad = 38.0 if layout.mode == "slide" else 30.0
    bot_pad = 42.0 if layout.mode == "slide" else 34.0
    side_pad = max(36.0, layout.chart_w * 0.06)

    x_left = layout.chart_x + side_pad
    x_right = layout.chart_right - side_pad
    base_y = layout.chart_bottom - bot_pad
    avail_h = max(80.0, (base_y - (layout.chart_y + top_pad)))
    step = min(13.0 if layout.mode == "slide" else 9.0, avail_h / max(max_rungs, 1))

    slot_w = (x_right - x_left) / max(n, 1)
    half_w = min(slot_w * 0.30, 44.0 if layout.mode == "slide" else 26.0)
    stroke_w = max(1.8, min(3.2, step * 0.36))

    # Baseline floor
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

    val_size = 17.0 if layout.mode == "slide" else 13.5
    cat_size = 13.5 if layout.mode == "slide" else 12.0
    dot_r = 2.0 if layout.mode == "slide" else 1.5

    for i, item in enumerate(items):
        name = str(item["label"])
        v = vals[i]
        rungs = rung_counts[i]
        cx = x_left + (i + 0.5) * slot_w
        is_hero = i == highlight_idx

        if color_mode == "categorical":
            col = palette.series_color(i)
        elif color_mode == "ramp":
            t = i / max(n - 1, 1)
            col = mix_hex(palette.c1, palette.c2, t) if len(palette.colors) >= 2 else palette.ramp6[min(i, 5)]
        else:
            # Default: highlight hero in accent (c3 when 3 colors else c2), others in c1
            col = (palette.c3 if len(palette.colors) >= 3 else palette.c2) if is_hero else palette.c1

        bar_g = canvas.add_group(marks_g, f"bar-{i+1}")
        for k in range(rungs):
            y = base_y - k * step
            jitter = (rnd(k + 1, i + 2) - 0.5) * (half_w * 0.16)
            w = half_w + jitter
            op = 0.82 + rnd(k + 2, i + 4) * 0.18
            canvas.add_line(
                bar_g,
                cx - w,
                y,
                cx + w,
                y,
                stroke=col,
                stroke_width=stroke_w,
                stroke_opacity=op,
                stroke_linecap="round",
            )
            if k % 5 == 4:
                canvas.add_circle(
                    bar_g,
                    cx + half_w + (10.0 if layout.mode == "slide" else 6.5),
                    y,
                    dot_r,
                    fill=palette.faint,
                )

        top_y = base_y - max(rungs - 1, 0) * step
        canvas.add_text(
            labels_g,
            cx,
            top_y - (14.0 if layout.mode == "slide" else 10.0),
            format_number(v, prefix, suffix),
            font_size=val_size,
            font_weight=800 if is_hero else 700,
            fill=col if is_hero else palette.ink,
            text_anchor="middle",
        )
        canvas.add_text(
            labels_g,
            cx,
            base_y + (28.0 if layout.mode == "slide" else 22.0),
            name,
            font_size=cat_size,
            font_weight=700 if is_hero else 600,
            fill=palette.ink if is_hero else palette.label,
            text_anchor="middle",
            letter_spacing=0.8,
        )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
