#!/usr/bin/env python3
"""G10 · Diverging Bar — Glance fast-read positive/negative capsule bar chart.

Clean central dashed zero-axis; positive gains stretch right in primary theme
color (c1), negative losses stretch left in secondary/accent theme color (c2 or c3),
with bold signed values at the outer capsule tips.
"""

from __future__ import annotations

from typing import Any, Dict, List

from palette import ThemePalette
from svg_builder import FrameLayout, SvgCanvas, estimate_text_width, fmt, format_number


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    items: List[Dict[str, Any]] = spec["data"]
    if not items:
        raise ValueError("diverging_bar requires non-empty 'data' list")

    title = spec.get("title", "Where we gained, where we lost")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "DIVERGING BAR")
    prefix = spec.get("value_prefix", "")
    suffix = spec.get("value_suffix", "")
    pos_label = spec.get("pos_label", "GAIN")
    neg_label = spec.get("neg_label", "LOSS")
    unit_note = spec.get("unit_note", f"LEFT = {neg_label} · RIGHT = {pos_label} · ZERO AXIS CENTERED")

    vals = [float(d["value"]) for d in items]
    max_abs = max(abs(v) for v in vals) or 1.0

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "diverging-bar"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    n = len(items)
    lbl_size = 15.0 if layout.mode == "slide" else 12.5
    max_lbl_px = max(estimate_text_width(str(d["label"]), lbl_size) for d in items)
    left_rail = min(
        layout.chart_w * 0.28,
        max(120.0 if layout.mode == "slide" else 92.0, max_lbl_px + 22.0),
    )
    val_margin = 76.0 if layout.mode == "slide" else 56.0
    plot_l = layout.chart_x + left_rail + val_margin * 0.6
    plot_r = layout.chart_right - val_margin * 0.8
    zero_x = (plot_l + plot_r) / 2.0
    half_span = (plot_r - plot_l) / 2.0

    top_pad = 30.0 if layout.mode == "slide" else 22.0
    bot_pad = 22.0 if layout.mode == "slide" else 16.0
    row_h = (layout.chart_h - top_pad - bot_pad) / max(n, 1)
    bar_h = min(row_h * 0.56, 30.0 if layout.mode == "slide" else 20.0)
    bar_r = bar_h / 2.0

    grid_g = canvas.add_group(area, "chart-grid")
    # Vertical subtle grid ticks at -100%, -50%, +50%, +100%
    for frac in (-1.0, -0.5, 0.5, 1.0):
        gx = zero_x + frac * half_span
        canvas.add_line(
            grid_g,
            gx,
            layout.chart_y + top_pad - 6,
            gx,
            layout.chart_bottom - bot_pad + 6,
            stroke=palette.quiet,
            stroke_width=1.0,
        )
    # Zero axis dashed rule
    canvas.add_line(
        grid_g,
        zero_x,
        layout.chart_y + top_pad - 10,
        zero_x,
        layout.chart_bottom - bot_pad + 10,
        stroke=palette.muted,
        stroke_width=1.6,
        stroke_dasharray="4,4",
    )

    canvas.add_comment(
        area,
        f"chart-plot-area: object={canvas.chart_id} | "
        f"{fmt(plot_l)},{fmt(layout.chart_y + top_pad)},{fmt(plot_r)},{fmt(layout.chart_bottom - bot_pad)}",
    )

    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    pos_col = palette.pos
    neg_col = palette.c3 if len(palette.colors) >= 3 else palette.neg
    lbl_size = 15.0 if layout.mode == "slide" else 12.5
    val_size = 16.0 if layout.mode == "slide" else 13.0

    for i, item in enumerate(items):
        name = str(item["label"])
        v = vals[i]
        cy = layout.chart_y + top_pad + (i + 0.5) * row_h
        w = max(bar_r, (abs(v) / max_abs) * half_span)
        is_pos = v >= 0
        col = pos_col if is_pos else neg_col

        # Category label on left rail
        canvas.add_text(
            labels_g,
            layout.chart_x + left_rail - 12.0,
            cy + lbl_size * 0.34,
            name,
            font_size=lbl_size,
            font_weight=600,
            fill=palette.label,
            text_anchor="end",
        )

        # Rounded capsule bar (flat on zero-axis side via clean path)
        y_top = cy - bar_h / 2.0
        y_bot = cy + bar_h / 2.0
        r = min(bar_r, w * 0.49)
        if is_pos:
            x_end = zero_x + w
            d = (
                f"M {fmt(zero_x)} {fmt(y_top)} "
                f"L {fmt(x_end - r)} {fmt(y_top)} "
                f"A {fmt(r)} {fmt(r)} 0 0 1 {fmt(x_end - r)} {fmt(y_bot)} "
                f"L {fmt(zero_x)} {fmt(y_bot)} Z"
            )
            val_x = x_end + 12.0
            val_anchor = "start"
            val_str = "+" + format_number(v, prefix, suffix) if v > 0 else format_number(0, prefix, suffix)
        else:
            x_end = zero_x - w
            d = (
                f"M {fmt(zero_x)} {fmt(y_top)} "
                f"L {fmt(x_end + r)} {fmt(y_top)} "
                f"A {fmt(r)} {fmt(r)} 0 0 0 {fmt(x_end + r)} {fmt(y_bot)} "
                f"L {fmt(zero_x)} {fmt(y_bot)} Z"
            )
            val_x = x_end - 12.0
            val_anchor = "end"
            val_str = "−" + format_number(abs(v), prefix, suffix)

        canvas.add_path(marks_g, d, fill=col)
        canvas.add_text(
            labels_g,
            val_x,
            cy + val_size * 0.34,
            val_str,
            font_size=val_size,
            font_weight=800,
            fill=col,
            text_anchor=val_anchor,
        )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
