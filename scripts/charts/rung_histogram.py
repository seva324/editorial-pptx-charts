#!/usr/bin/env python3
"""F14 · Rung Histogram — Continuous-bin countable rung frequency histogram.

Unlike F1 Rung Bars (discrete categories), histogram bin edges sit strictly
BETWEEN the rung columns on a continuous numeric axis. Includes 5th-unit dots,
highlighted peak bin in accent color, and an optional dashed vertical median
callout flag ("HALF RESOLVED BY HERE").
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

from palette import ThemePalette
from svg_builder import FrameLayout, SvgCanvas, fmt, format_number, rnd


def _choose_unit(max_val: float, max_rungs: int, explicit_unit: float | None) -> float:
    if explicit_unit and explicit_unit > 0:
        return float(explicit_unit)
    if max_val <= max_rungs:
        return 1.0
    raw = max_val / max_rungs
    mag = 10 ** math.floor(math.log10(raw))
    for mult in (1, 2, 2.5, 5, 10):
        cand = mult * mag
        if max_val / cand <= max_rungs:
            return cand
    return 10 * mag


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    bins: List[float] = [max(0.0, float(v)) for v in spec["bins"]]
    edges: List[str] = [str(e) for e in spec["edges"]]
    if not bins or len(edges) != len(bins) + 1:
        raise ValueError("rung_histogram requires 'bins' (length N) and 'edges' (length N+1)")

    title = spec.get("title", "Distribution across continuous bins")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "RUNG HISTOGRAM")
    unit_label = spec.get("unit_label", "")
    median_label = spec.get("median_label", "MEDIAN · 50%")
    show_median = bool(spec.get("show_median", True))

    max_val = max(bins) or 1.0
    max_rungs_cap = 34 if layout.mode == "slide" else 24
    unit_val = _choose_unit(max_val, max_rungs_cap, spec.get("unit_value"))
    rungs = [max(1, int(round(v / unit_val))) if v > 0 else 0 for v in bins]
    max_rungs = max(rungs) or 1

    unit_note = spec.get("unit_note")
    if not unit_note:
        u_txt = format_number(unit_val)
        if unit_label:
            u_txt = f"{u_txt} {unit_label}".strip()
        unit_note = f"ONE RUNG = {u_txt} · CONTINUOUS BIN EDGES · DOT MARKS EVERY FIFTH"

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "rung-histogram"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    n = len(bins)
    pad_l = 44.0 if layout.mode == "slide" else 26.0
    pad_r = 44.0 if layout.mode == "slide" else 26.0
    top_pad = 58.0 if layout.mode == "slide" else 44.0
    bot_pad = 48.0 if layout.mode == "slide" else 38.0

    x0 = layout.chart_x + pad_l
    x1 = layout.chart_right - pad_r
    base_y = layout.chart_bottom - bot_pad
    avail_h = max(80.0, base_y - (layout.chart_y + top_pad))
    step = min(13.0 if layout.mode == "slide" else 9.0, avail_h / max(max_rungs, 1))

    bin_w = (x1 - x0) / max(n, 1)
    half_w = min(bin_w * 0.36, 32.0 if layout.mode == "slide" else 18.0)
    stroke_w = max(1.8, min(3.0, step * 0.36))

    grid_g = canvas.add_group(area, "chart-grid")
    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    # Continuous axis floor + bin-edge ticks
    floor_y = base_y + step * 0.65
    canvas.add_line(grid_g, x0 - 8, floor_y, x1 + 8, floor_y, stroke=palette.grid, stroke_width=1.4)

    edge_stride = 1 if (n <= 8 or bin_w >= 80) else 2
    axis_size = 12.5 if layout.mode == "slide" else 12.0
    for e_idx in range(n + 1):
        ex = x0 + e_idx * bin_w
        major = e_idx % edge_stride == 0
        th = (12.0 if major else 7.0) if layout.mode == "slide" else (9.0 if major else 5.0)
        canvas.add_line(grid_g, ex, floor_y, ex, floor_y + th, stroke=palette.floor, stroke_width=1.1)
        if major:
            canvas.add_text(
                labels_g,
                ex,
                floor_y + (28.0 if layout.mode == "slide" else 23.0),
                edges[e_idx],
                font_size=axis_size,
                font_weight=600,
                fill=palette.muted,
                text_anchor="middle",
            )

    canvas.add_comment(
        area,
        f"chart-plot-area: object={canvas.chart_id} | "
        f"{fmt(x0)},{fmt(layout.chart_y + top_pad)},{fmt(x1)},{fmt(base_y)}",
    )

    peak_idx = bins.index(max(bins))
    accent_col = palette.c3 if len(palette.colors) >= 3 else palette.c2
    dot_r = 1.9 if layout.mode == "slide" else 1.4

    for i, cnt in enumerate(rungs):
        cx = x0 + (i + 0.5) * bin_w
        is_peak = i == peak_idx
        col = accent_col if is_peak else palette.c1
        bin_g = canvas.add_group(marks_g, f"bin-{i+1}")

        for k in range(cnt):
            y = base_y - k * step
            w = half_w + (rnd(k + 1, i + 2) - 0.5) * (half_w * 0.14)
            op = 0.82 + rnd(k + 2, i + 4) * 0.18
            canvas.add_line(
                bin_g,
                cx - w,
                y,
                cx + w,
                y,
                stroke=col,
                stroke_width=stroke_w,
                stroke_opacity=op,
                stroke_linecap="round",
            )
            if k % 5 == 4:
                canvas.add_circle(bin_g, cx + half_w + (7.0 if layout.mode == "slide" else 4.5), y, dot_r, fill=palette.faint)

        if is_peak:
            top_y = base_y - max(cnt - 1, 0) * step
            canvas.add_text(
                labels_g,
                cx,
                top_y - (14.0 if layout.mode == "slide" else 10.0),
                format_number(bins[i], spec.get("value_prefix", ""), spec.get("value_suffix", "")),
                font_size=17.0 if layout.mode == "slide" else 13.5,
                font_weight=800,
                fill=accent_col,
                text_anchor="middle",
            )

    # Dashed median flag (interpolated inside median bin)
    if show_median and sum(bins) > 0:
        half_tot = sum(bins) / 2.0
        acc = 0.0
        mx = x0
        for i, v in enumerate(bins):
            if acc + v >= half_tot:
                frac = (half_tot - acc) / max(v, 1e-6)
                mx = x0 + (i + frac) * bin_w
                break
            acc += v
        flag_top = layout.chart_y + (24.0 if layout.mode == "slide" else 18.0)
        med_col = palette.c2 if len(palette.colors) >= 2 else palette.muted
        canvas.add_line(
            labels_g,
            mx,
            floor_y,
            mx,
            flag_top,
            stroke=med_col,
            stroke_width=1.6,
            stroke_dasharray="4,4",
        )
        go_right = mx < (x0 + x1) * 0.68
        canvas.add_text(
            labels_g,
            mx + (10.0 if go_right else -10.0),
            flag_top + 10.0,
            median_label,
            font_size=13.0 if layout.mode == "slide" else 12.0,
            font_weight=800,
            fill=med_col,
            text_anchor="start" if go_right else "end",
            letter_spacing=0.6,
        )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
