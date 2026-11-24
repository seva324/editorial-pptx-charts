#!/usr/bin/env python3
"""L4 · Arc Matrix — Horizon-bowed bubble matrix (category x category + volume).

Each row gently arches like a horizon line; bubble area is strictly proportional
to volume (`sqrt(v)`), true zeros remain visible as tiny silent dots, and the
top-N cells are accented and directly labeled.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

from palette import ThemePalette
from svg_builder import FrameLayout, SvgCanvas, estimate_text_width, fmt, format_number


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    rows: List[str] = spec["rows"]
    cols: List[str] = spec["cols"]
    matrix: List[List[float]] = spec["matrix"]
    if not rows or not cols or not matrix:
        raise ValueError("arc_matrix requires non-empty 'rows', 'cols', and 'matrix'")

    title = spec.get("title", "Products across markets, bowed like horizons")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "ARC MATRIX")
    top_n = int(spec.get("top_n", 4))
    prefix = spec.get("value_prefix", "")
    suffix = spec.get("value_suffix", "")
    unit_note = spec.get(
        "unit_note",
        "BUBBLE AREA ∝ VALUE · TINY DOT = ABSENCE · ACCENT = TOP CELLS",
    )

    n_rows = len(rows)
    n_cols = len(cols)
    all_cells: List[Tuple[float, int, int]] = []
    max_val = 0.0
    for r in range(n_rows):
        for c in range(n_cols):
            v = max(0.0, float(matrix[r][c]))
            if v > max_val:
                max_val = v
            if v > 0:
                all_cells.append((v, r, c))
    all_cells.sort(key=lambda t: t[0], reverse=True)
    # Keep top-N spaced so labels don't collide on adjacent cells
    top_set = set()
    for _v, r, c in all_cells:
        if all(abs(r - tr) + abs(c - tc) >= 2 for tr, tc in top_set):
            top_set.add((r, c))
        if len(top_set) >= top_n:
            break

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "arc-matrix"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    row_lbl_size = 13.5 if layout.mode == "slide" else 12.0
    col_lbl_size = 12.5 if layout.mode == "slide" else 12.0
    max_row_px = max(estimate_text_width(str(r), row_lbl_size) for r in rows)
    left_rail = min(layout.chart_w * 0.22, max(96.0 if layout.mode == "slide" else 74.0, max_row_px + 22.0))
    right_pad = 36.0 if layout.mode == "slide" else 20.0

    bow = 26.0 if layout.mode == "slide" else 16.0
    top_pad = 98.0 if layout.mode == "slide" else 74.0
    bot_pad = 22.0 if layout.mode == "slide" else 16.0

    x0 = layout.chart_x + left_rail
    x1 = layout.chart_right - right_pad
    y0 = layout.chart_y + top_pad
    y1 = layout.chart_bottom - bot_pad

    col_step = (x1 - x0) / max(n_cols - 1, 1)
    row_step = (y1 - y0) / max(n_rows - 1, 1)
    max_r = min(col_step * 0.36, row_step * 0.42, 19.0 if layout.mode == "slide" else 13.0)

    def col_x(j: int) -> float:
        return x0 + j * col_step if n_cols > 1 else (x0 + x1) / 2.0

    def arc_dy(j: int) -> float:
        return -bow * math.sin(math.pi * j / max(n_cols - 1, 1)) if n_cols > 1 else 0.0

    def row_y(i: int) -> float:
        return y0 + i * row_step if n_rows > 1 else (y0 + y1) / 2.0

    grid_g = canvas.add_group(area, "chart-grid")
    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    accent_col = palette.c3 if len(palette.colors) >= 3 else palette.c2
    val_size = 12.5 if layout.mode == "slide" else 12.0

    # Column header labels tilted along top horizon arc
    for j, cname in enumerate(cols):
        cx = col_x(j)
        cy = row_y(0) + arc_dy(j) - (30.0 if layout.mode == "slide" else 22.0)
        canvas.add_text(
            labels_g,
            cx,
            cy,
            str(cname),
            font_size=col_lbl_size,
            font_weight=700,
            fill=palette.muted,
            letter_spacing=0.6,
            rotate=(-45.0, cx, cy),
        )

    for i, rname in enumerate(rows):
        ry = row_y(i)
        # Bowed horizon path
        pts_d = "M " + " L ".join(f"{fmt(col_x(j))} {fmt(ry + arc_dy(j))}" for j in range(n_cols))
        canvas.add_path(grid_g, pts_d, fill="none", stroke=palette.grid, stroke_width=1.2)

        canvas.add_text(
            labels_g,
            x0 - 18.0,
            ry + row_lbl_size * 0.34,
            str(rname),
            font_size=row_lbl_size,
            font_weight=600,
            fill=palette.label,
            text_anchor="end",
        )

        row_g = canvas.add_group(marks_g, f"arc-row-{i+1}")
        for j in range(n_cols):
            cx = col_x(j)
            cy = ry + arc_dy(j)
            v = max(0.0, float(matrix[i][j]))
            if v <= 0 or max_val <= 0:
                canvas.add_circle(row_g, cx, cy, 2.0 if layout.mode == "slide" else 1.5, fill=palette.quiet)
                continue

            ratio = v / max_val
            rad = max(3.0, math.sqrt(ratio) * max_r)
            is_top = (i, j) in top_set
            fill_col = accent_col if is_top else palette.ramp_color(ratio * 0.88)
            canvas.add_circle(row_g, cx, cy, rad, fill=fill_col)

            if is_top:
                v_txt = format_number(v, prefix, suffix)
                if rad >= 13.5 and len(v_txt) <= 3:
                    canvas.add_text(
                        labels_g,
                        cx,
                        cy + val_size * 0.35,
                        v_txt,
                        font_size=val_size,
                        font_weight=800,
                        fill=palette.bg if not palette.dark else palette.ink,
                        text_anchor="middle",
                    )
                else:
                    canvas.add_text(
                        labels_g,
                        cx,
                        cy - rad - 5.0,
                        v_txt,
                        font_size=val_size,
                        font_weight=800,
                        fill=accent_col,
                        text_anchor="middle",
                    )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
