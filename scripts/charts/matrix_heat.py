#!/usr/bin/env python3
"""G20 · Matrix Heat (Glance) — Rounded-tile direct-read numeric heatmap matrix.

Fast-read Glance sibling to L4 Arc Matrix: large rounded tiles shaded smoothly
along the custom theme lightness ramp, with every cell displaying its bold
figure right inside in automatic WCAG-contrasted text.
"""

from __future__ import annotations

from typing import Any, Dict, List

from palette import ThemePalette, contrast_ratio
from svg_builder import FrameLayout, SvgCanvas, estimate_text_width, fmt, format_number


def _text_on_fill(fill_hex: str, palette: ThemePalette) -> str:
    light_txt = "#FFFFFF" if not palette.dark else palette.ink
    dark_txt = palette.ink if not palette.dark else palette.bg
    if contrast_ratio(light_txt, fill_hex) >= 3.4:
        return light_txt
    return dark_txt


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    rows: List[str] = spec["rows"]
    cols: List[str] = spec["cols"]
    matrix: List[List[float]] = spec["matrix"]
    if not rows or not cols or not matrix:
        raise ValueError("matrix_heat requires non-empty 'rows', 'cols', and 'matrix'")

    title = spec.get("title", "Adoption runs hot on newer versions")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "MATRIX HEAT")
    prefix = spec.get("value_prefix", "")
    suffix = spec.get("value_suffix", "")
    highlight_peak = bool(spec.get("highlight_peak", True))
    unit_note = spec.get(
        "unit_note",
        "SHADE = VALUE INTENSITY · DIRECT NUMBER IN EVERY CELL · ACCENT = MAXIMUM",
    )

    n_rows = len(rows)
    n_cols = len(cols)
    flat = [float(matrix[r][c]) for r in range(n_rows) for c in range(n_cols)]
    v_min = float(spec.get("v_min", min(flat)))
    v_max = float(spec.get("v_max", max(flat)))
    if v_max <= v_min:
        v_max = v_min + 1.0

    peak_val = max(flat)
    peak_rc = (0, 0)
    for r in range(n_rows):
        for c in range(n_cols):
            if float(matrix[r][c]) == peak_val:
                peak_rc = (r, c)
                break

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "matrix-heat"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    row_lbl_size = 14.5 if layout.mode == "slide" else 12.0
    col_lbl_size = 13.5 if layout.mode == "slide" else 12.0
    max_row_px = max(estimate_text_width(str(r), row_lbl_size) for r in rows)
    left_rail = min(layout.chart_w * 0.22, max(88.0 if layout.mode == "slide" else 66.0, max_row_px + 24.0))
    right_pad = 32.0 if layout.mode == "slide" else 16.0
    top_pad = 40.0 if layout.mode == "slide" else 30.0
    bot_pad = 16.0 if layout.mode == "slide" else 10.0

    avail_w = layout.chart_w - left_rail - right_pad
    avail_h = layout.chart_h - top_pad - bot_pad
    gap = 10.0 if layout.mode == "slide" else 6.0

    cell_w = min((avail_w - gap * (n_cols - 1)) / max(n_cols, 1), 132.0 if layout.mode == "slide" else 72.0)
    cell_h = min((avail_h - gap * (n_rows - 1)) / max(n_rows, 1), 74.0 if layout.mode == "slide" else 48.0)
    grid_w = cell_w * n_cols + gap * (n_cols - 1)
    grid_h = cell_h * n_rows + gap * (n_rows - 1)

    x0 = layout.chart_x + left_rail + (avail_w - grid_w) / 2.0
    y0 = layout.chart_y + top_pad + (avail_h - grid_h) / 2.0

    canvas.add_comment(
        area,
        f"chart-plot-area: object={canvas.chart_id} | "
        f"{fmt(x0)},{fmt(y0)},{fmt(x0 + grid_w)},{fmt(y0 + grid_h)}",
    )

    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    accent_col = palette.c3 if len(palette.colors) >= 3 else palette.c2
    val_size = 18.0 if layout.mode == "slide" else 13.5
    rx = min(14.0 if layout.mode == "slide" else 8.0, cell_h * 0.25)

    # Column headers
    for c, cname in enumerate(cols):
        cx = x0 + c * (cell_w + gap) + cell_w / 2.0
        canvas.add_text(
            labels_g,
            cx,
            y0 - (14.0 if layout.mode == "slide" else 10.0),
            str(cname),
            font_size=col_lbl_size,
            font_weight=700,
            fill=palette.muted,
            text_anchor="middle",
            letter_spacing=0.6,
        )

    for r, rname in enumerate(rows):
        ry = y0 + r * (cell_h + gap)
        canvas.add_text(
            labels_g,
            x0 - 16.0,
            ry + cell_h / 2.0 + row_lbl_size * 0.34,
            str(rname),
            font_size=row_lbl_size,
            font_weight=700,
            fill=palette.label,
            text_anchor="end",
        )
        row_g = canvas.add_group(marks_g, f"heat-row-{r+1}")
        for c in range(n_cols):
            val = float(matrix[r][c])
            norm = (val - v_min) / (v_max - v_min)
            is_peak = highlight_peak and (r, c) == peak_rc
            fill_col = accent_col if is_peak else palette.ramp_color(norm * 0.85)
            cx = x0 + c * (cell_w + gap)
            canvas.add_rect(row_g, cx, ry, cell_w, cell_h, fill=fill_col, rx=rx)

            txt_col = _text_on_fill(fill_col, palette)
            canvas.add_text(
                labels_g,
                cx + cell_w / 2.0,
                ry + cell_h / 2.0 + val_size * 0.35,
                format_number(val, prefix, suffix, decimals=0),
                font_size=val_size,
                font_weight=800,
                fill=txt_col,
                text_anchor="middle",
            )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
