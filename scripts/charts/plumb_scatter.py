#!/usr/bin/env python3
"""F8 · Plumb Scatter — 2D editorial scatter with vertical plumb lines to floor.

Every dot drops a delicate hairline plumb line down to a calibrated barcode
floor so the reader reads X at the floor and Y by height. Best and worst (or
explicitly highlighted) points are enlarged and labeled cleanly in theme colors.
"""

from __future__ import annotations

from typing import Any, Dict, List

from palette import ThemePalette
from svg_builder import FrameLayout, SvgCanvas, fmt, format_number


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    points: List[Dict[str, Any]] = spec["data"]
    if len(points) < 2:
        raise ValueError("plumb_scatter requires at least 2 points in 'data'")

    title = spec.get("title", "Two dimensions, plumbed to the floor")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "PLUMB SCATTER")
    x_left_lbl = spec.get("x_left_label", "LOW")
    x_right_lbl = spec.get("x_right_label", "HIGH")
    y_axis_lbl = spec.get("y_label", "HIGHER ↑")
    y_suffix = spec.get("y_suffix", "")
    unit_note = spec.get("unit_note", "EVERY DOT HANGS A PLUMB LINE · READ X AT THE FLOOR · ACCENT = EXTREMES")

    xs = [float(p["x"]) for p in points]
    ys = [float(p["y"]) for p in points]

    x_min = float(spec.get("x_min", min(xs) - (max(xs) - min(xs) or 1.0) * 0.08))
    x_max = float(spec.get("x_max", max(xs) + (max(xs) - min(xs) or 1.0) * 0.08))
    y_min = float(spec.get("y_min", min(ys) - (max(ys) - min(ys) or 1.0) * 0.16))
    y_max = float(spec.get("y_max", max(ys) + (max(ys) - min(ys) or 1.0) * 0.14))
    if x_max <= x_min:
        x_max = x_min + 1.0
    if y_max <= y_min:
        y_max = y_min + 1.0

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "plumb-scatter"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    pad_l = 64.0 if layout.mode == "slide" else 44.0
    pad_r = 44.0 if layout.mode == "slide" else 28.0
    pad_t = 40.0 if layout.mode == "slide" else 30.0
    pad_b = 46.0 if layout.mode == "slide" else 36.0

    x0 = layout.chart_x + pad_l
    x1 = layout.chart_right - pad_r
    y_top = layout.chart_y + pad_t
    y_bot = layout.chart_bottom - pad_b

    def map_x(v: float) -> float:
        return x0 + ((v - x_min) / (x_max - x_min)) * (x1 - x0)

    def map_y(v: float) -> float:
        return y_bot - ((v - y_min) / (y_max - y_min)) * (y_bot - y_top)

    grid_g = canvas.add_group(area, "chart-grid")
    # Horizontal subtle guides
    for frac in (0.33, 0.67, 1.0):
        gy = y_bot - frac * (y_bot - y_top)
        canvas.add_line(grid_g, x0, gy, x1, gy, stroke=palette.quiet, stroke_width=1.0, stroke_dasharray="4,4")

    # Barcode floor (20 intervals, longer tick every 5th)
    n_ticks = 20
    for g in range(n_ticks + 1):
        gx = x0 + (g / n_ticks) * (x1 - x0)
        th = (13.0 if g % 5 == 0 else 7.0) if layout.mode == "slide" else (9.0 if g % 5 == 0 else 5.0)
        canvas.add_line(grid_g, gx, y_bot, gx, y_bot - th, stroke=palette.floor, stroke_width=1.1)
    canvas.add_line(grid_g, x0 - 10, y_bot, x1 + 10, y_bot, stroke=palette.grid, stroke_width=1.4)

    canvas.add_comment(
        area,
        f"chart-plot-area: object={canvas.chart_id} | "
        f"{fmt(x0)},{fmt(y_top)},{fmt(x1)},{fmt(y_bot)}",
    )

    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    # Identify best & worst (or user-flagged) points
    best_i = ys.index(max(ys))
    worst_i = ys.index(min(ys))
    accent_col = palette.c3 if len(palette.colors) >= 3 else palette.c2
    low_col = palette.c2

    dot_r = 5.5 if layout.mode == "slide" else 4.0
    hero_r = 9.0 if layout.mode == "slide" else 6.5
    lbl_size = 14.0 if layout.mode == "slide" else 12.0

    # Track labeled points to avoid collisions
    labeled_positions: List[tuple[float, float]] = []

    for i, pt in enumerate(points):
        px = map_x(xs[i])
        py = map_y(ys[i])
        name = str(pt["label"])
        is_best = i == best_i
        is_worst = i == worst_i
        is_flagged = bool(pt.get("highlight", False))
        is_hero = is_best or is_worst or is_flagged

        if is_best or is_flagged:
            col = accent_col
        elif is_worst:
            col = low_col
        else:
            col = palette.c1

        # Vertical plumb line to floor
        canvas.add_line(
            marks_g,
            px,
            y_bot,
            px,
            py,
            stroke=col if is_hero else palette.floor,
            stroke_width=1.6 if is_hero else 1.1,
            stroke_opacity=0.65 if is_hero else 0.72,
        )
        # Floor foot tick accent
        canvas.add_circle(marks_g, px, y_bot, 2.2 if is_hero else 1.5, fill=col if is_hero else palette.faint)

        # Dot
        rad = hero_r if is_hero else dot_r
        canvas.add_circle(marks_g, px, py, rad, fill=col)

        if is_hero:
            val_txt = f"{name} · {format_number(ys[i], '', y_suffix)}"
            ly = py - rad - (11.0 if layout.mode == "slide" else 8.0)
            if ly < layout.chart_y + 18.0:
                ly = py + rad + lbl_size + 6.0
            canvas.add_text(
                labels_g,
                px,
                ly,
                val_txt,
                font_size=lbl_size,
                font_weight=800,
                fill=col,
                text_anchor="middle",
            )
            labeled_positions.append((px, ly))
        elif spec.get("show_all_labels", True):
            # Subtle muted label if clear of hero labels
            ly = py - rad - 8.0
            if all(abs(px - lx) > 76 or abs(ly - oy) > 22 for lx, oy in labeled_positions):
                canvas.add_text(
                    labels_g,
                    px,
                    ly,
                    name,
                    font_size=12.0,
                    font_weight=600,
                    fill=palette.muted,
                    text_anchor="middle",
                )
                labeled_positions.append((px, ly))

    # Axis labels
    axis_size = 12.5 if layout.mode == "slide" else 12.0
    canvas.add_text(labels_g, x0, y_bot + 28.0, x_left_lbl, font_size=axis_size, font_weight=600, fill=palette.muted, letter_spacing=0.8)
    canvas.add_text(labels_g, x1, y_bot + 28.0, x_right_lbl, font_size=axis_size, font_weight=600, fill=palette.muted, text_anchor="end", letter_spacing=0.8)

    # Vertical Y-axis cue safely inside chart bounds
    yx = layout.chart_x + 22.0
    yy = y_top + 12.0
    canvas.add_text(
        labels_g,
        yx,
        yy,
        y_axis_lbl,
        font_size=axis_size,
        font_weight=600,
        fill=palette.muted,
        text_anchor="end",
        rotate=(-90.0, yx, yy),
    )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
