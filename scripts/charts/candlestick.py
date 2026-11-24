#!/usr/bin/env python3
"""F17 · Candlestick — Editorial OHLC capsule candlestick chart.

Thin hairline wicks mark each period's full high-low reach; rounded capsule
bodies encode open-to-close: hollow (bg fill + primary stroke) = closed up,
solid accent/secondary fill = closed down. Period high and low extremes are
annotated directly above/below their wicks, grounded by a week-tick floor.
"""

from __future__ import annotations

from typing import Any, Dict, List

from palette import ThemePalette
from svg_builder import FrameLayout, SvgCanvas, fmt, format_number


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    days: List[Dict[str, Any]] = spec["data"]
    if len(days) < 3:
        raise ValueError("candlestick requires at least 3 OHLC records in 'data'")

    title = spec.get("title", "Price trajectory, candle by candle")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "CANDLESTICK")
    prefix = spec.get("value_prefix", "$")
    suffix = spec.get("value_suffix", "")
    ticks: List[Dict[str, Any]] = spec.get("ticks", [])
    unit_note = spec.get(
        "unit_note",
        "HOLLOW CAPSULE = CLOSED UP · SOLID CAPSULE = CLOSED DOWN · HAIRLINE WICK = DAY HIGH–LOW",
    )

    lows = [float(d["low"]) for d in days]
    highs = [float(d["high"]) for d in days]
    v_min = min(lows)
    v_max = max(highs)
    pad_v = (v_max - v_min or 1.0) * 0.10
    y_lo = float(spec.get("y_min", v_min - pad_v))
    y_hi = float(spec.get("y_max", v_max + pad_v))
    if y_hi <= y_lo:
        y_hi = y_lo + 1.0

    hi_idx = highs.index(max(highs))
    lo_idx = lows.index(min(lows))

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "candlestick"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    left_rail = 74.0 if layout.mode == "slide" else 52.0
    right_pad = 30.0 if layout.mode == "slide" else 18.0
    top_pad = 34.0 if layout.mode == "slide" else 26.0
    bot_pad = 50.0 if layout.mode == "slide" else 38.0

    x0 = layout.chart_x + left_rail
    x1 = layout.chart_right - right_pad
    y_top = layout.chart_y + top_pad
    y_bot = layout.chart_bottom - bot_pad

    n = len(days)
    slot_w = (x1 - x0) / max(n, 1)
    body_w = min(slot_w * 0.56, 18.0 if layout.mode == "slide" else 10.5)

    def map_x(i: int) -> float:
        return x0 + (i + 0.5) * slot_w

    def map_y(v: float) -> float:
        return y_bot - ((v - y_lo) / (y_hi - y_lo)) * (y_bot - y_top)

    grid_g = canvas.add_group(area, "chart-grid")
    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    axis_size = 12.5 if layout.mode == "slide" else 12.0
    for g in range(5):
        v = y_lo + (g / 4.0) * (y_hi - y_lo)
        gy = map_y(v)
        canvas.add_line(grid_g, x0 - 6, gy, x1 + 6, gy, stroke=palette.quiet, stroke_width=1.0)
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

    up_col = palette.c1
    down_col = palette.c3 if len(palette.colors) >= 3 else palette.c2
    ext_size = 14.0 if layout.mode == "slide" else 12.0

    for i, d in enumerate(days):
        o, c, h, l = float(d["open"]), float(d["close"]), float(d["high"]), float(d["low"])
        cx = map_x(i)
        is_up = c >= o
        col = up_col if is_up else down_col

        # Full-reach hairline wick
        canvas.add_line(marks_g, cx, map_y(h), cx, map_y(l), stroke=col, stroke_width=1.5 if layout.mode == "slide" else 1.1)

        # Rounded capsule body
        yt = map_y(max(o, c))
        yb = map_y(min(o, c))
        bh = max(4.0, yb - yt)
        rx = min(body_w * 0.45, bh * 0.45, 5.0)
        if is_up:
            canvas.add_rect(
                marks_g,
                cx - body_w / 2.0,
                yt,
                body_w,
                bh,
                fill=palette.bg,
                stroke=up_col,
                stroke_width=2.0 if layout.mode == "slide" else 1.5,
                rx=rx,
            )
        else:
            canvas.add_rect(marks_g, cx - body_w / 2.0, yt, body_w, bh, fill=down_col, rx=rx)

        if i == hi_idx:
            canvas.add_text(
                labels_g,
                cx,
                map_y(h) - (10.0 if layout.mode == "slide" else 7.0),
                format_number(h, prefix, suffix, decimals=1),
                font_size=ext_size,
                font_weight=800,
                fill=up_col,
                text_anchor="middle",
            )
        if i == lo_idx:
            canvas.add_text(
                labels_g,
                cx,
                map_y(l) + (18.0 if layout.mode == "slide" else 14.0),
                format_number(l, prefix, suffix, decimals=1),
                font_size=ext_size,
                font_weight=800,
                fill=down_col,
                text_anchor="middle",
            )

    # Week-tick floor
    floor_y = y_bot + (14.0 if layout.mode == "slide" else 10.0)
    canvas.add_line(grid_g, x0 - 6, floor_y, x1 + 6, floor_y, stroke=palette.grid, stroke_width=1.2)
    t_segs = []
    for i in range(n):
        tx = map_x(i)
        th = (9.0 if i % 5 == 0 else 4.5) if layout.mode == "slide" else (6.5 if i % 5 == 0 else 3.5)
        t_segs.append(f"M {fmt(tx)} {fmt(floor_y)} V {fmt(floor_y - th)}")
    canvas.add_path(grid_g, " ".join(t_segs), fill="none", stroke=palette.floor, stroke_width=1.0)

    if not ticks:
        step = max(1, n // 6)
        ticks = [{"index": i, "label": str(days[i].get("label", f"W{i // 5 + 1}"))} for i in range(0, n, step)]
    for tk in ticks:
        idx = max(0, min(n - 1, int(tk["index"])))
        canvas.add_text(
            labels_g,
            map_x(idx),
            floor_y + (22.0 if layout.mode == "slide" else 18.0),
            str(tk["label"]),
            font_size=axis_size,
            font_weight=600,
            fill=palette.muted,
            text_anchor="middle",
            letter_spacing=0.6,
        )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
