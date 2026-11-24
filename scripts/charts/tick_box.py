#!/usr/bin/env python3
"""F15 · Tick Box — Editorial five-number summary box plot with hollow outliers.

Hairline whiskers with crisp end caps, rounded capsule IQR box colored across
the theme palette, high-contrast paper median tick across the box with explicit
right-side median readout, and hollow outlier circles.
"""

from __future__ import annotations

from typing import Any, Dict, List

from palette import ThemePalette, mix_hex
from svg_builder import FrameLayout, SvgCanvas, fmt, format_number, rnd


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    items: List[Dict[str, Any]] = spec["data"]
    if not items:
        raise ValueError("tick_box requires non-empty 'data' list")

    title = spec.get("title", "Distribution summary by group")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "TICK BOX")
    suffix = spec.get("value_suffix", "")
    prefix = spec.get("value_prefix", "")
    highlight_idx = spec.get("highlight_index", 0)
    unit_note = spec.get(
        "unit_note",
        "CAPSULE BOX = IQR (25–75%) · PAPER BAR = MEDIAN · HOLLOW DOT = OUTLIER",
    )

    all_nums: List[float] = []
    for d in items:
        all_nums.extend([float(d["min"]), float(d["q1"]), float(d["median"]), float(d["q3"]), float(d["max"])])
        all_nums.extend([float(o) for o in d.get("outliers", [])])

    y_min = float(spec.get("y_min", min(0.0, min(all_nums))))
    y_max = float(spec.get("y_max", max(all_nums) * 1.08))
    if y_max <= y_min:
        y_max = y_min + 1.0

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "tick-box"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    left_rail = 68.0 if layout.mode == "slide" else 48.0
    right_pad = 54.0 if layout.mode == "slide" else 36.0
    top_pad = 28.0 if layout.mode == "slide" else 20.0
    bot_pad = 44.0 if layout.mode == "slide" else 34.0

    x0 = layout.chart_x + left_rail
    x1 = layout.chart_right - right_pad
    y_top = layout.chart_y + top_pad
    y_bot = layout.chart_bottom - bot_pad

    def map_y(v: float) -> float:
        return y_bot - ((v - y_min) / (y_max - y_min)) * (y_bot - y_top)

    grid_g = canvas.add_group(area, "chart-grid")
    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    # 5 horizontal reference rules
    axis_size = 12.5 if layout.mode == "slide" else 12.0
    for g in range(5):
        v = y_min + (g / 4.0) * (y_max - y_min)
        gy = map_y(v)
        canvas.add_line(grid_g, x0, gy, x1, gy, stroke=palette.grid if g == 0 else palette.quiet, stroke_width=1.2 if g == 0 else 1.0)
        canvas.add_text(
            labels_g,
            x0 - 14.0,
            gy + axis_size * 0.34,
            format_number(v, prefix, suffix, decimals=0),
            font_size=axis_size,
            font_weight=600,
            fill=palette.muted,
            text_anchor="end",
        )

    canvas.add_comment(
        area,
        f"chart-plot-area: object={canvas.chart_id} | "
        f"{fmt(x0)},{fmt(y_top)},{fmt(x1)},{fmt(y_bot)}",
    )

    n = len(items)
    slot_w = (x1 - x0) / max(n, 1)
    box_w = min(slot_w * 0.28, 52.0 if layout.mode == "slide" else 32.0)
    cap_half = box_w * 0.32
    accent_col = palette.c3 if len(palette.colors) >= 3 else palette.c2
    med_size = 15.0 if layout.mode == "slide" else 12.5
    cat_size = 14.0 if layout.mode == "slide" else 12.0

    for i, d in enumerate(items):
        cx = x0 + (i + 0.5) * slot_w
        mn, q1, md, q3, mx = float(d["min"]), float(d["q1"]), float(d["median"]), float(d["q3"]), float(d["max"])
        outs = [float(o) for o in d.get("outliers", [])]
        is_hero = i == highlight_idx

        t = i / max(n - 1, 1)
        col = accent_col if is_hero else (mix_hex(palette.c1, palette.c2, t * 0.7) if len(palette.colors) >= 2 else palette.c1)
        grp = canvas.add_group(marks_g, f"box-{i+1}")

        # Whisker stem & caps
        canvas.add_line(grp, cx, map_y(mn), cx, map_y(mx), stroke=palette.muted, stroke_width=1.6)
        canvas.add_line(grp, cx - cap_half, map_y(mn), cx + cap_half, map_y(mn), stroke=palette.muted, stroke_width=1.8)
        canvas.add_line(grp, cx - cap_half, map_y(mx), cx + cap_half, map_y(mx), stroke=palette.muted, stroke_width=1.8)

        # Capsule IQR box
        y_q3 = map_y(q3)
        y_q1 = map_y(q1)
        bh = max(10.0, y_q1 - y_q3)
        rx = min(box_w * 0.34, bh * 0.45, 14.0)
        canvas.add_rect(grp, cx - box_w / 2.0, y_q3, box_w, bh, fill=col, rx=rx)

        # Paper median tick inside box
        ym = map_y(md)
        canvas.add_line(
            grp,
            cx - box_w / 2.0 + 5.0,
            ym,
            cx + box_w / 2.0 - 5.0,
            ym,
            stroke=palette.bg if not palette.dark else palette.ink,
            stroke_width=3.2 if layout.mode == "slide" else 2.4,
            stroke_linecap="round",
        )
        canvas.add_text(
            labels_g,
            cx + box_w / 2.0 + 10.0,
            ym + med_size * 0.34,
            format_number(md, prefix, suffix, decimals=1),
            font_size=med_size,
            font_weight=800,
            fill=col if is_hero else palette.ink,
        )

        # Hollow outlier dots
        out_r = 4.6 if layout.mode == "slide" else 3.4
        for k, o in enumerate(outs):
            ox = cx + (rnd(k + 1, i + 3) - 0.5) * 14.0
            canvas.add_circle(grp, ox, map_y(o), out_r, fill=palette.bg, stroke=col, stroke_width=1.8)

        # Category label
        canvas.add_text(
            labels_g,
            cx,
            y_bot + (28.0 if layout.mode == "slide" else 22.0),
            str(d["label"]),
            font_size=cat_size,
            font_weight=700 if is_hero else 600,
            fill=palette.ink if is_hero else palette.label,
            text_anchor="middle",
            letter_spacing=0.6,
        )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
