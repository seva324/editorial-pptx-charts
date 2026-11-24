#!/usr/bin/env python3
"""F10 · Dot Heat — Area-encoded editorial dot matrix heatmap.

Dot area is strictly proportional to value (r ~ sqrt(value)). Zero/silent cells
retain a tiny visible dot ("silence stays visible"). The peak cell gets a crisp
dashed accent ring and numeric annotation.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

from palette import ThemePalette
from svg_builder import FrameLayout, SvgCanvas, fmt, format_number


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    rows: List[str] = spec["rows"]
    cols: List[str] = spec["cols"]
    matrix: List[List[float]] = spec["matrix"]
    if not rows or not cols or not matrix:
        raise ValueError("dot_heat requires non-empty 'rows', 'cols', and 'matrix'")

    title = spec.get("title", "Activity heatmap")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "DOT HEAT")
    prefix = spec.get("value_prefix", "")
    suffix = spec.get("value_suffix", "")

    n_rows = len(rows)
    n_cols = len(cols)
    max_val = 0.0
    peak_r, peak_c = 0, 0
    for r in range(n_rows):
        for c in range(n_cols):
            v = max(0.0, float(matrix[r][c]))
            if v > max_val:
                max_val = v
                peak_r, peak_c = r, c

    peak_txt = format_number(max_val, prefix, suffix)
    unit_note = spec.get(
        "unit_note",
        f"DOT AREA = VALUE · DASHED RING = PEAK ({peak_txt}) · TINY DOT = ZERO",
    )

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "dot-heat"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    max_row_len = max(len(str(r)) for r in rows)
    left_rail = min(
        layout.chart_w * 0.22,
        max(84.0 if layout.mode == "slide" else 68.0, max_row_len * (11.5 if layout.mode == "slide" else 9.0)),
    )
    right_pad = 36.0 if layout.mode == "slide" else 20.0
    top_pad = 24.0 if layout.mode == "slide" else 16.0
    bot_pad = 42.0 if layout.mode == "slide" else 34.0

    x0 = layout.chart_x + left_rail
    x1 = layout.chart_right - right_pad
    y0 = layout.chart_y + top_pad
    y1 = layout.chart_bottom - bot_pad

    cell_w = (x1 - x0) / max(n_cols, 1)
    cell_h = (y1 - y0) / max(n_rows, 1)
    max_r = min(cell_w, cell_h) * 0.42

    canvas.add_comment(
        area,
        f"chart-plot-area: object={canvas.chart_id} | "
        f"{fmt(x0)},{fmt(y0)},{fmt(x1)},{fmt(y1)}",
    )

    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    row_lbl_size = 13.5 if layout.mode == "slide" else 12.0
    col_lbl_size = 12.5 if layout.mode == "slide" else 12.0
    accent_col = palette.c3 if len(palette.colors) >= 3 else palette.c2

    for r in range(n_rows):
        cy = y0 + (r + 0.5) * cell_h
        canvas.add_text(
            labels_g,
            x0 - 16.0,
            cy + row_lbl_size * 0.34,
            str(rows[r]),
            font_size=row_lbl_size,
            font_weight=700,
            fill=palette.label,
            text_anchor="end",
            letter_spacing=0.6,
        )
        row_g = canvas.add_group(marks_g, f"heat-row-{r+1}")
        for c in range(n_cols):
            cx = x0 + (c + 0.5) * cell_w
            v = max(0.0, float(matrix[r][c]))
            if v <= 0 or max_val <= 0:
                canvas.add_circle(row_g, cx, cy, 2.0 if layout.mode == "slide" else 1.5, fill=palette.quiet)
                continue

            ratio = v / max_val
            rad = max(2.8, math.sqrt(ratio) * max_r)
            is_peak = r == peak_r and c == peak_c
            fill_col = accent_col if is_peak else palette.ramp_color(ratio * 0.85)
            canvas.add_circle(row_g, cx, cy, rad, fill=fill_col)

            if is_peak:
                canvas.add_circle(
                    row_g,
                    cx,
                    cy,
                    rad + (5.5 if layout.mode == "slide" else 4.0),
                    fill="none",
                    stroke=accent_col,
                    stroke_width=1.8 if layout.mode == "slide" else 1.4,
                    stroke_dasharray="3,3",
                )
                peak_num_only = format_number(max_val, prefix, "")
                if rad >= 15.0:
                    canvas.add_text(
                        labels_g,
                        cx,
                        cy + (13.0 if layout.mode == "slide" else 12.0) * 0.35,
                        peak_num_only,
                        font_size=13.0 if layout.mode == "slide" else 12.0,
                        font_weight=800,
                        fill=palette.bg if not palette.dark else palette.ink,
                        text_anchor="middle",
                    )
                else:
                    canvas.add_text(
                        labels_g,
                        cx,
                        cy - rad - 9.0,
                        peak_num_only,
                        font_size=12.0,
                        font_weight=800,
                        fill=accent_col,
                        text_anchor="middle",
                    )

    # Column labels (skip alternating if crowded)
    col_step = 1 if (n_cols <= 8 or cell_w >= 54) else 2
    for c in range(0, n_cols, col_step):
        cx = x0 + (c + 0.5) * cell_w
        canvas.add_text(
            labels_g,
            cx,
            y1 + (26.0 if layout.mode == "slide" else 22.0),
            str(cols[c]),
            font_size=col_lbl_size,
            font_weight=600,
            fill=palette.muted,
            text_anchor="middle",
        )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
