#!/usr/bin/env python3
"""F11 · Tick Gauge — 210° countable-tick progress dial (1 tick = 1% of target).

100 radial hairline ticks sweep across a 210° arc from left to right. Earned
ticks are inked and taller in the theme color ramp; remaining ticks stay short
and quiet. An accent tip bead marks the current level; 25/50/75/100 milestones
and a bold center figure anchor the readout.
"""

from __future__ import annotations

from typing import Any, Dict

from palette import ThemePalette, mix_hex
from svg_builder import FrameLayout, SvgCanvas, fmt, pol, rnd


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    value = max(0.0, min(100.0, float(spec["value"])))
    earned = int(round(value))
    remaining = max(0, 100 - earned)

    title = spec.get("title", "Progress toward target")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "TICK GAUGE")
    value_text = spec.get("value_text", f"{earned}%")
    sub_text = spec.get("sub_text", f"{remaining} TICKS TO GO")
    target_note = spec.get("target_note", "")
    unit_note = spec.get("unit_note", "ONE TICK = 1% OF TARGET · INKED = EARNED · READS LEFT TO RIGHT")

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "tick-gauge"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    cx = layout.chart_x + layout.chart_w / 2.0
    # Center sits lower because the 210° arc opens downward
    cy = layout.chart_y + layout.chart_h * 0.66
    r0 = min(layout.chart_w * 0.30, layout.chart_h * 0.52)
    tick_inked_min = r0 * 0.14
    tick_inked_var = r0 * 0.06
    tick_rem_min = r0 * 0.055
    tick_rem_var = r0 * 0.025

    a0 = -195.0
    sweep = 210.0

    canvas.add_comment(
        area,
        f"chart-plot-area: object={canvas.chart_id} | donut | "
        f"center: {fmt(cx)},{fmt(cy)} | outer-radius: {fmt(r0 + tick_inked_min + tick_inked_var)} | inner-radius: {fmt(r0)}",
    )

    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    accent_col = palette.c3 if len(palette.colors) >= 3 else palette.c2
    stroke_inked = 2.6 if layout.mode == "slide" else 1.9
    stroke_rem = 1.4 if layout.mode == "slide" else 1.1

    # 100 ticks
    for k in range(100):
        ang = a0 + (k / 99.0) * sweep
        is_inked = k < earned
        if is_inked:
            tlen = tick_inked_min + rnd(k + 1, 3) * tick_inked_var
            frac = k / max(earned, 1)
            col = mix_hex(palette.c2, palette.c1, frac) if len(palette.colors) >= 2 else palette.c1
            x1, y1 = pol(cx, cy, r0, ang)
            x2, y2 = pol(cx, cy, r0 + tlen, ang)
            canvas.add_line(marks_g, x1, y1, x2, y2, stroke=col, stroke_width=stroke_inked, stroke_linecap="round")
        else:
            tlen = tick_rem_min + rnd(k + 1, 7) * tick_rem_var
            x1, y1 = pol(cx, cy, r0, ang)
            x2, y2 = pol(cx, cy, r0 + tlen, ang)
            canvas.add_line(marks_g, x1, y1, x2, y2, stroke=palette.floor, stroke_width=stroke_rem, stroke_linecap="round")

    # Milestones 0 / 25 / 50 / 75 / 100
    ms_size = 12.5 if layout.mode == "slide" else 12.0
    for m in (0, 25, 50, 75, 100):
        ang = a0 + (m / 100.0) * sweep
        dx, dy = pol(cx, cy, r0 - (14.0 if layout.mode == "slide" else 10.0), ang)
        tx, ty = pol(cx, cy, r0 - (34.0 if layout.mode == "slide" else 24.0), ang)
        canvas.add_circle(marks_g, dx, dy, 2.2 if layout.mode == "slide" else 1.6, fill=palette.faint)
        canvas.add_text(
            labels_g,
            tx,
            ty + ms_size * 0.35,
            str(m),
            font_size=ms_size,
            font_weight=600,
            fill=palette.muted,
            text_anchor="middle",
        )

    # Accent pointer bead at earned tip
    if earned > 0:
        ang_tip = a0 + ((min(earned, 100) - 1) / 99.0) * sweep
        bx, by = pol(cx, cy, r0 + tick_inked_min + tick_inked_var + (12.0 if layout.mode == "slide" else 8.0), ang_tip)
        canvas.add_circle(marks_g, bx, by, 6.5 if layout.mode == "slide" else 4.8, fill=accent_col)

    # Center bold KPI
    big_size = 64.0 if layout.mode == "slide" else 40.0
    sub_size = 15.0 if layout.mode == "slide" else 12.5
    canvas.add_text(
        labels_g,
        cx,
        cy - (6.0 if layout.mode == "slide" else 4.0),
        str(value_text),
        font_size=big_size,
        font_weight=800,
        fill=palette.ink,
        text_anchor="middle",
    )
    canvas.add_text(
        labels_g,
        cx,
        cy + (26.0 if layout.mode == "slide" else 20.0),
        str(sub_text),
        font_size=sub_size,
        font_weight=700,
        fill=accent_col,
        text_anchor="middle",
        letter_spacing=1.2,
    )
    if target_note:
        canvas.add_text(
            labels_g,
            cx,
            cy + (52.0 if layout.mode == "slide" else 38.0),
            str(target_note),
            font_size=13.5 if layout.mode == "slide" else 12.0,
            font_weight=500,
            fill=palette.muted,
            text_anchor="middle",
        )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
