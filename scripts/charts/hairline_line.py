#!/usr/bin/env python3
"""F2 · Hairline Line — Editorial time-series with calendar barcode floor.

Features:
  - Calendar barcode floor (one vertical hairline tick per period)
  - Crisp theme-colored hairline polyline + per-point dots
  - Optional hollow dots for marked periods (e.g. weekends / holidays)
  - Top-N peaks (kept separated so labels never collide) highlighted in accent color
  - Optional secondary comparison series in theme color c2
"""

from __future__ import annotations

from typing import Any, Dict, List

from palette import ThemePalette
from svg_builder import FrameLayout, SvgCanvas, fmt, format_number


def _pick_separated_peaks(vals: List[float], count: int = 2, min_gap: int = 4) -> List[int]:
    order = sorted(range(len(vals)), key=lambda i: vals[i], reverse=True)
    picked: List[int] = []
    for idx in order:
        if all(abs(idx - p) >= min_gap for p in picked):
            picked.append(idx)
        if len(picked) >= count:
            break
    return picked


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    points: List[Dict[str, Any]] = spec["data"]
    if len(points) < 2:
        raise ValueError("hairline_line requires at least 2 points in 'data'")

    title = spec.get("title", "Daily trajectory")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "HAIRLINE LINE")
    prefix = spec.get("value_prefix", "")
    suffix = spec.get("value_suffix", "")
    peak_count = int(spec.get("peak_count", 2))
    unit_note = spec.get("unit_note", "ONE DOT = ONE PERIOD · HOLLOW = MARKED / WEEKEND · ACCENT = PEAK")

    vals = [float(p["value"]) for p in points]
    has_compare = any("compare" in p and p["compare"] is not None for p in points)
    comp_vals = [float(p["compare"]) if p.get("compare") is not None else None for p in points]

    all_nums = list(vals) + [v for v in comp_vals if v is not None]
    y_min = float(spec.get("y_min", min(0.0, min(all_nums))))
    y_max = float(spec.get("y_max", max(all_nums) * 1.12))
    if y_max <= y_min:
        y_max = y_min + 1.0

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "hairline-line"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    pad_l = 42.0 if layout.mode == "slide" else 26.0
    pad_r = 42.0 if layout.mode == "slide" else 26.0
    pad_t = 44.0 if layout.mode == "slide" else 34.0
    pad_b = 46.0 if layout.mode == "slide" else 36.0

    x0 = layout.chart_x + pad_l
    x1 = layout.chart_right - pad_r
    y_top = layout.chart_y + pad_t
    y_bot = layout.chart_bottom - pad_b
    n = len(points)

    def map_x(i: int) -> float:
        return x0 + (i / max(n - 1, 1)) * (x1 - x0)

    def map_y(v: float) -> float:
        return y_bot - ((v - y_min) / (y_max - y_min)) * (y_bot - y_top)

    grid_g = canvas.add_group(area, "chart-grid")
    # Subtle horizontal reference lines (3 guide rules)
    for frac in (0.33, 0.67, 1.0):
        gy = y_bot - frac * (y_bot - y_top)
        canvas.add_line(
            grid_g,
            x0,
            gy,
            x1,
            gy,
            stroke=palette.quiet,
            stroke_width=1.0,
            stroke_dasharray="4,4",
        )

    # Calendar barcode floor
    tick_h = 12.0 if layout.mode == "slide" else 9.0
    for i in range(n):
        tx = map_x(i)
        canvas.add_line(
            grid_g,
            tx,
            y_bot,
            tx,
            y_bot - tick_h,
            stroke=palette.floor,
            stroke_width=1.1,
        )
    canvas.add_line(grid_g, x0 - 10, y_bot, x1 + 10, y_bot, stroke=palette.grid, stroke_width=1.4)

    canvas.add_comment(
        area,
        f"chart-plot-area: object={canvas.chart_id} | "
        f"{fmt(x0)},{fmt(y_top)},{fmt(x1)},{fmt(y_bot)}",
    )

    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    # Optional comparison series (dashed c2 hairline)
    if has_compare:
        comp_pts = [(map_x(i), map_y(v)) for i, v in enumerate(comp_vals) if v is not None]
        if len(comp_pts) >= 2:
            d_comp = "M " + " L ".join(f"{fmt(px)} {fmt(py)}" for px, py in comp_pts)
            canvas.add_path(
                marks_g,
                d_comp,
                fill="none",
                stroke=palette.c2,
                stroke_width=1.8 if layout.mode == "slide" else 1.4,
                stroke_opacity=0.75,
                stroke_dasharray="6,4",
                stroke_linejoin="round",
            )
            for px, py in comp_pts:
                canvas.add_circle(marks_g, px, py, 2.8 if layout.mode == "slide" else 2.1, fill=palette.c2, fill_opacity=0.8)

    # Primary hairline polyline
    d_main = "M " + " L ".join(f"{fmt(map_x(i))} {fmt(map_y(v))}" for i, v in enumerate(vals))
    canvas.add_path(
        marks_g,
        d_main,
        fill="none",
        stroke=palette.c1,
        stroke_width=2.4 if layout.mode == "slide" else 1.8,
        stroke_linejoin="round",
        stroke_linecap="round",
    )

    # Peaks
    min_gap = max(3, n // 6)
    peaks = set(_pick_separated_peaks(vals, count=peak_count, min_gap=min_gap))
    accent_col = palette.c3 if len(palette.colors) >= 3 else palette.c2
    val_size = 16.0 if layout.mode == "slide" else 13.0
    axis_size = 12.5 if layout.mode == "slide" else 12.0

    for i, pt in enumerate(points):
        px = map_x(i)
        py = map_y(vals[i])
        hollow = bool(pt.get("hollow", pt.get("weekend", False)))
        is_peak = i in peaks

        if is_peak:
            # Subtle vertical plumb cue to floor for hero peak
            canvas.add_line(
                marks_g,
                px,
                py + 9.0,
                px,
                y_bot,
                stroke=accent_col,
                stroke_width=1.0,
                stroke_opacity=0.45,
                stroke_dasharray="2,4",
            )
            canvas.add_circle(
                marks_g,
                px,
                py,
                7.2 if layout.mode == "slide" else 5.2,
                fill=accent_col,
            )
            lbl_txt = format_number(vals[i], prefix, suffix)
            canvas.add_text(
                labels_g,
                px,
                py - (16.0 if layout.mode == "slide" else 12.0),
                lbl_txt,
                font_size=val_size,
                font_weight=800,
                fill=accent_col,
                text_anchor="middle",
            )
        elif hollow:
            canvas.add_circle(
                marks_g,
                px,
                py,
                4.2 if layout.mode == "slide" else 3.2,
                fill=palette.bg,
                stroke=palette.c1,
                stroke_width=2.0 if layout.mode == "slide" else 1.5,
            )
        else:
            canvas.add_circle(
                marks_g,
                px,
                py,
                4.0 if layout.mode == "slide" else 3.0,
                fill=palette.c1,
            )

    # X-axis milestone labels (first, middle(s), last, or explicit `tick: true`)
    explicit_ticks = [i for i, p in enumerate(points) if p.get("tick")]
    if explicit_ticks:
        tick_indices = explicit_ticks
    else:
        step_idx = max(1, (n - 1) // (4 if layout.mode == "slide" else 2))
        tick_indices = sorted(set(list(range(0, n, step_idx)) + [n - 1]))
        # Drop penultimate if too close to final label
        if len(tick_indices) >= 2 and (tick_indices[-1] - tick_indices[-2]) < max(2, step_idx * 0.55):
            tick_indices.pop(-2)

    for idx in tick_indices:
        lbl = str(points[idx].get("label", idx + 1))
        anchor = "start" if idx == 0 else ("end" if idx == n - 1 else "middle")
        canvas.add_text(
            labels_g,
            map_x(idx),
            y_bot + (26.0 if layout.mode == "slide" else 22.0),
            lbl,
            font_size=axis_size,
            font_weight=600,
            fill=palette.muted,
            text_anchor=anchor,
            letter_spacing=0.8,
        )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
