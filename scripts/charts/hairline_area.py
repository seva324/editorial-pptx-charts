#!/usr/bin/env python3
"""F3 · Hairline Area — Area chart constructed from vertical day-hairlines.

Instead of a flat solid polygon fill, the area is made of individual vertical
hairlines standing from floor to value, topped by a crisp contour line and a
highlighted peak marker in the theme accent color.
"""

from __future__ import annotations

from typing import Any, Dict, List

from palette import ThemePalette, mix_hex
from svg_builder import FrameLayout, SvgCanvas, fmt, format_number, rnd


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    points: List[Dict[str, Any]] = spec["data"]
    if len(points) < 2:
        raise ValueError("hairline_area requires at least 2 points in 'data'")

    title = spec.get("title", "Volume, filled with days")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "HAIRLINE AREA")
    prefix = spec.get("value_prefix", "")
    suffix = spec.get("value_suffix", "")
    unit_note = spec.get("unit_note", "ONE HAIRLINE = ONE PERIOD, FLOOR TO PEAK · ACCENT = MAXIMUM")

    vals = [max(0.0, float(p["value"])) for p in points]
    y_max = float(spec.get("y_max", (max(vals) or 1.0) * 1.14))
    peak_idx = vals.index(max(vals))

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "hairline-area"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    pad_l = 36.0 if layout.mode == "slide" else 22.0
    pad_r = 36.0 if layout.mode == "slide" else 22.0
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
        return y_bot - (v / max(y_max, 1e-6)) * (y_bot - y_top)

    grid_g = canvas.add_group(area, "chart-grid")
    canvas.add_line(grid_g, x0 - 8, y_bot, x1 + 8, y_bot, stroke=palette.grid, stroke_width=1.4)

    canvas.add_comment(
        area,
        f"chart-plot-area: object={canvas.chart_id} | "
        f"{fmt(x0)},{fmt(y_top)},{fmt(x1)},{fmt(y_bot)}",
    )

    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    accent_col = palette.c3 if len(palette.colors) >= 3 else palette.c2
    hair_w = max(1.1, min(2.4, ((x1 - x0) / max(n, 1)) * 0.24))

    # Optional subtle phase tint across 2nd theme color along time
    use_phase = bool(spec.get("phase_color", True)) and len(palette.colors) >= 2

    # Vertical hairlines (the area is made of days, not flat paint)
    for i, v in enumerate(vals):
        px = map_x(i)
        py = map_y(v)
        if i == peak_idx:
            canvas.add_line(
                marks_g,
                px,
                y_bot,
                px,
                py,
                stroke=accent_col,
                stroke_width=max(2.4, hair_w * 1.6),
                stroke_opacity=1.0,
            )
        else:
            if use_phase:
                t = i / max(n - 1, 1)
                col = mix_hex(palette.c1, palette.c2, t * 0.55)
            else:
                col = palette.c1
            op = 0.45 + rnd(i + 1, 7) * 0.40
            canvas.add_line(
                marks_g,
                px,
                y_bot,
                px,
                py,
                stroke=col,
                stroke_width=hair_w,
                stroke_opacity=op,
            )

    # Crisp top contour line
    d_top = "M " + " L ".join(f"{fmt(map_x(i))} {fmt(map_y(v))}" for i, v in enumerate(vals))
    canvas.add_path(
        marks_g,
        d_top,
        fill="none",
        stroke=palette.c1,
        stroke_width=2.6 if layout.mode == "slide" else 2.0,
        stroke_linejoin="round",
        stroke_linecap="round",
    )

    # Peak highlight dot & label
    pk_x = map_x(peak_idx)
    pk_y = map_y(vals[peak_idx])
    canvas.add_circle(
        marks_g,
        pk_x,
        pk_y,
        7.5 if layout.mode == "slide" else 5.5,
        fill=accent_col,
    )
    canvas.add_text(
        labels_g,
        pk_x,
        pk_y - (16.0 if layout.mode == "slide" else 12.0),
        format_number(vals[peak_idx], prefix, suffix),
        font_size=17.0 if layout.mode == "slide" else 13.5,
        font_weight=800,
        fill=accent_col,
        text_anchor="middle",
    )

    # X-axis milestone labels
    explicit_ticks = [i for i, p in enumerate(points) if p.get("tick")]
    if explicit_ticks:
        tick_indices = explicit_ticks
    else:
        step_idx = max(1, (n - 1) // (4 if layout.mode == "slide" else 2))
        tick_indices = sorted(set(list(range(0, n, step_idx)) + [n - 1]))
        if len(tick_indices) >= 2 and (tick_indices[-1] - tick_indices[-2]) < max(2, step_idx * 0.55):
            tick_indices.pop(-2)

    axis_size = 12.5 if layout.mode == "slide" else 12.0
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
