#!/usr/bin/env python3
"""L3 · Barcode Lollipop — 60-90 day full-height calendar barcode + gravity lollipops.

One of Lieflat's signature editorial pieces: every day stands as a full-height
pale calendar hairline ("whether or not anything happened in it"), with a dark
lollipop dot at the day's reading, a short gravity stem hanging below, hollow
circles on weekends, and separated Top-3 peaks highlighted in the accent color.
"""

from __future__ import annotations

from typing import Any, Dict, List

from palette import ThemePalette, mix_hex
from svg_builder import FrameLayout, SvgCanvas, fmt, format_number, rnd


def _pick_separated_peaks(vals: List[float], count: int = 3, min_gap: int = 6) -> List[int]:
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
    if len(points) < 10:
        raise ValueError("barcode_lollipop requires at least 10 daily points in 'data'")

    title = spec.get("title", "Ninety days as a barcode")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "BARCODE LOLLIPOP")
    prefix = spec.get("value_prefix", "")
    suffix = spec.get("value_suffix", "")
    peak_count = int(spec.get("peak_count", 3))
    unit_note = spec.get(
        "unit_note",
        "ONE HAIRLINE = ONE CALENDAR DAY · SOLID = WEEKDAY · HOLLOW = WEEKEND · ACCENT = TOP PEAKS",
    )

    vals = [float(p["value"]) for p in points]
    y_min = float(spec.get("y_min", min(0.0, min(vals) * 0.85)))
    y_max = float(spec.get("y_max", max(vals) * 1.12))
    if y_max <= y_min:
        y_max = y_min + 1.0

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "barcode-lollipop"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    n = len(points)
    pad_l = 22.0 if layout.mode == "slide" else 14.0
    pad_r = 22.0 if layout.mode == "slide" else 14.0
    pad_t = 34.0 if layout.mode == "slide" else 26.0
    pad_b = 42.0 if layout.mode == "slide" else 34.0

    x0 = layout.chart_x + pad_l
    x1 = layout.chart_right - pad_r
    y_top = layout.chart_y + pad_t
    y_bot = layout.chart_bottom - pad_b

    def map_x(i: int) -> float:
        return x0 + (i / max(n - 1, 1)) * (x1 - x0)

    def map_y(v: float) -> float:
        return y_bot - ((v - y_min) / (y_max - y_min)) * (y_bot - y_top)

    grid_g = canvas.add_group(area, "chart-grid")
    # Combine all full-height calendar barcode hairlines into one clean multi-subpath <path>
    # for crisp DrawingML performance & zero PowerPoint clutter!
    bar_segs = [f"M {fmt(map_x(d))} {fmt(y_top)} V {fmt(y_bot)}" for d in range(n)]
    canvas.add_path(
        grid_g,
        " ".join(bar_segs),
        fill="none",
        stroke=palette.quiet,
        stroke_width=1.0,
    )

    canvas.add_comment(
        area,
        f"chart-plot-area: object={canvas.chart_id} | "
        f"{fmt(x0)},{fmt(y_top)},{fmt(x1)},{fmt(y_bot)}",
    )

    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    min_gap = max(5, n // 12)
    peaks = set(_pick_separated_peaks(vals, count=peak_count, min_gap=min_gap))
    accent_col = palette.c3 if len(palette.colors) >= 3 else palette.c2

    dot_r = 3.8 if layout.mode == "slide" else 2.6
    peak_r = 6.8 if layout.mode == "slide" else 4.8
    stem_w = 1.8 if layout.mode == "slide" else 1.3
    peak_size = 14.5 if layout.mode == "slide" else 12.0

    for d, pt in enumerate(points):
        px = map_x(d)
        py = map_y(vals[d])
        weekend = bool(pt.get("weekend", (d % 7 in (5, 6))))
        is_peak = d in peaks
        t = d / max(n - 1, 1)
        col = accent_col if is_peak else (mix_hex(palette.c1, palette.c2, t * 0.45) if len(palette.colors) >= 2 else palette.c1)

        # Gravity stem hanging below dot
        stem_len = (24.0 + rnd(d + 1, 9) * 44.0) if layout.mode == "slide" else (14.0 + rnd(d + 1, 9) * 26.0)
        stem_end = min(y_bot, py + stem_len)
        canvas.add_line(marks_g, px, py, px, stem_end, stroke=col, stroke_width=stem_w if not is_peak else stem_w * 1.35)

        if is_peak:
            canvas.add_circle(marks_g, px, py, peak_r, fill=accent_col)
            canvas.add_text(
                labels_g,
                px,
                py - peak_r - (10.0 if layout.mode == "slide" else 7.0),
                format_number(vals[d], prefix, suffix),
                font_size=peak_size,
                font_weight=800,
                fill=accent_col,
                text_anchor="middle",
            )
        elif weekend:
            canvas.add_circle(marks_g, px, py, dot_r, fill=palette.bg, stroke=col, stroke_width=1.6)
        else:
            canvas.add_circle(marks_g, px, py, dot_r, fill=col)

    # Month / milestone markers along bottom
    ticks = [(i, str(p["tick_label"])) for i, p in enumerate(points) if p.get("tick_label")]
    if not ticks:
        step = max(1, n // 3)
        ticks = [(i, str(points[i].get("label", f"D{i+1}"))) for i in range(0, n, step)]

    axis_size = 12.5 if layout.mode == "slide" else 12.0
    for idx, lbl in ticks:
        anchor = "start" if idx == 0 else ("end" if idx >= n - 2 else "middle")
        canvas.add_text(
            labels_g,
            map_x(idx),
            y_bot + (26.0 if layout.mode == "slide" else 22.0),
            lbl,
            font_size=axis_size,
            font_weight=700,
            fill=palette.muted,
            text_anchor=anchor,
            letter_spacing=1.0,
        )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
