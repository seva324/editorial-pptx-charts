#!/usr/bin/env python3
"""F7 · Stacked Rungs — Multi-segment countable stacked ladder chart.

Segments stack vertically inside a single ladder using the 2-3 theme colors,
with a 1-rung breathing gap between segments, inline segment values on the
right side of each block, and bold totals at the top.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

from palette import ThemePalette
from svg_builder import FrameLayout, SvgCanvas, fmt, format_number, rnd


def _choose_unit(max_total: float, max_rungs: int, explicit_unit: float | None) -> float:
    if explicit_unit and explicit_unit > 0:
        return float(explicit_unit)
    if max_total <= max_rungs:
        return 1.0
    raw = max_total / max_rungs
    mag = 10 ** math.floor(math.log10(raw))
    for mult in (1, 2, 2.5, 5, 10):
        cand = mult * mag
        if max_total / cand <= max_rungs:
            return cand
    return 10 * mag


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    items: List[Dict[str, Any]] = spec["data"]
    segments: List[str] = spec.get("segments", [])
    if not items:
        raise ValueError("stacked_rungs requires non-empty 'data' list")

    title = spec.get("title", "Stacked composition, rung by rung")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "STACKED RUNGS")
    prefix = spec.get("value_prefix", "")
    suffix = spec.get("value_suffix", "")
    unit_label = spec.get("unit_label", "")

    n_segs = len(items[0]["segments"])
    if not segments:
        segments = [f"Segment {i+1}" for i in range(n_segs)]

    totals = [sum(max(0.0, float(v)) for v in d["segments"]) for d in items]
    max_total = max(totals) or 1.0
    max_rungs_cap = 34 if layout.mode == "slide" else 24
    unit_val = _choose_unit(max_total, max_rungs_cap, spec.get("unit_value"))

    seg_rungs = [
        [max(1, int(round(max(0.0, float(v)) / unit_val))) if float(v) > 0 else 0 for v in d["segments"]]
        for d in items
    ]
    max_slots = max(sum(r) + max(0, len([x for x in r if x > 0]) - 1) for r in seg_rungs) or 1

    unit_note = spec.get("unit_note")
    if not unit_note:
        u_txt = format_number(unit_val, prefix, suffix)
        if unit_label:
            u_txt = f"{u_txt} {unit_label}".strip()
        unit_note = f"ONE RUNG = {u_txt} · GAP SEPARATES SEGMENTS"

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "stacked-rungs"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    # Inline legend top-right
    legend_g = canvas.add_group(area, "chart-legend")
    leg_y = layout.chart_y + 10.0
    leg_step = 130.0 if layout.mode == "slide" else 96.0
    leg_start_x = layout.chart_right - leg_step * len(segments)
    for si, sname in enumerate(segments):
        lx = leg_start_x + si * leg_step
        scol = palette.series_color(si)
        canvas.add_line(legend_g, lx, leg_y, lx + 20, leg_y, stroke=scol, stroke_width=3.2, stroke_linecap="round")
        canvas.add_text(
            legend_g,
            lx + 28,
            leg_y + 4.5,
            str(sname),
            font_size=13.0 if layout.mode == "slide" else 12.0,
            font_weight=600,
            fill=palette.label,
        )

    n = len(items)
    top_pad = 48.0 if layout.mode == "slide" else 36.0
    bot_pad = 44.0 if layout.mode == "slide" else 34.0
    side_pad = max(48.0, layout.chart_w * 0.08)

    x_left = layout.chart_x + side_pad
    x_right = layout.chart_right - side_pad
    base_y = layout.chart_bottom - bot_pad
    avail_h = max(80.0, base_y - (layout.chart_y + top_pad))
    step = min(12.5 if layout.mode == "slide" else 8.8, avail_h / max(max_slots, 1))

    slot_w = (x_right - x_left) / max(n, 1)
    half_w = min(slot_w * 0.24, 38.0 if layout.mode == "slide" else 22.0)
    stroke_w = max(1.8, min(3.0, step * 0.36))

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

    tot_size = 17.0 if layout.mode == "slide" else 13.5
    seg_val_size = 13.0 if layout.mode == "slide" else 12.0
    cat_size = 14.0 if layout.mode == "slide" else 12.0

    for i, item in enumerate(items):
        name = str(item["label"])
        cx = x_left + (i + 0.5) * slot_w
        grp = canvas.add_group(marks_g, f"stack-{i+1}")
        k_cursor = 0

        for si, cnt in enumerate(seg_rungs[i]):
            if cnt <= 0:
                continue
            scol = palette.series_color(si)
            raw_v = float(item["segments"][si])
            for k in range(cnt):
                y = base_y - (k_cursor + k) * step
                w = half_w + (rnd(k + 1, i * 3 + si + 2) - 0.5) * (half_w * 0.16)
                op = 0.84 + rnd(k + 2, i + si + 4) * 0.16
                canvas.add_line(
                    grp,
                    cx - w,
                    y,
                    cx + w,
                    y,
                    stroke=scol,
                    stroke_width=stroke_w,
                    stroke_opacity=op,
                    stroke_linecap="round",
                )
            mid_y = base_y - (k_cursor + (cnt - 1) / 2.0) * step
            canvas.add_text(
                labels_g,
                cx + half_w + (12.0 if layout.mode == "slide" else 8.0),
                mid_y + seg_val_size * 0.34,
                format_number(raw_v, prefix, suffix),
                font_size=seg_val_size,
                font_weight=700,
                fill=scol,
            )
            k_cursor += cnt + 1  # 1-rung breathing gap

        top_y = base_y - max(k_cursor - 2, 0) * step
        canvas.add_text(
            labels_g,
            cx,
            top_y - (15.0 if layout.mode == "slide" else 11.0),
            format_number(totals[i], prefix, suffix),
            font_size=tot_size,
            font_weight=800,
            fill=palette.ink,
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
