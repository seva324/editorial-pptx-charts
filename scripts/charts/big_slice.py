#!/usr/bin/env python3
"""G13 · Big Slice — Dual-encoding variable-radius pie (angle = share, radius = intensity).

Every slice sweeps an angle proportional to its share of the total (360°) while
extending radially according to a second metric (intensity/depth), framed by
concentric dotted reference rings and crisp paper gaps between slices.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

from palette import ThemePalette
from svg_builder import D2R, FrameLayout, SvgCanvas, fmt, format_number, pol


def _sector_path(cx: float, cy: float, r_in: float, r_out: float, a0: float, a1: float) -> str:
    large = 1 if (a1 - a0) > 180.0 else 0
    x1, y1 = pol(cx, cy, r_out, a0)
    x2, y2 = pol(cx, cy, r_out, a1)
    x3, y3 = pol(cx, cy, r_in, a1)
    x4, y4 = pol(cx, cy, r_in, a0)
    return (
        f"M {fmt(x1)} {fmt(y1)} "
        f"A {fmt(r_out)} {fmt(r_out)} 0 {large} 1 {fmt(x2)} {fmt(y2)} "
        f"L {fmt(x3)} {fmt(y3)} "
        f"A {fmt(r_in)} {fmt(r_in)} 0 {large} 0 {fmt(x4)} {fmt(y4)} Z"
    )


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    items: List[Dict[str, Any]] = spec["data"]
    if len(items) < 2:
        raise ValueError("big_slice requires at least 2 items with {label, share, radius}")

    title = spec.get("title", "Big slice, deep engagement")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "BIG SLICE")
    radius_suffix = spec.get("radius_suffix", "")
    rings: List[float] = spec.get("rings") or []
    unit_note = spec.get(
        "unit_note",
        "ANGLE = SHARE (360° TOTAL) · RADIUS = INTENSITY · DOTTED RINGS = SCALE GUIDES",
    )

    shares = [max(0.0, float(d["share"])) for d in items]
    radii = [max(0.0, float(d["radius"])) for d in items]
    tot_share = sum(shares) or 1.0
    max_rad_val = float(spec.get("max_radius", max(radii + rings) * 1.05 if (radii or rings) else 1.0)) or 1.0

    if not rings:
        step = max_rad_val / 3.0
        rings = [round(step), round(step * 2), round(step * 3)]

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "big-slice"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    cx = layout.chart_x + layout.chart_w / 2.0
    cy = layout.chart_y + layout.chart_h * 0.49
    r_max = min(layout.chart_w * 0.25, layout.chart_h * 0.355)
    r_inner = r_max * 0.14

    def map_r(v: float) -> float:
        return r_inner + (max(0.0, v) / max_rad_val) * (r_max - r_inner)

    grid_g = canvas.add_group(area, "chart-grid")
    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    # Concentric dotted scale rings + labels at 12 o'clock
    ring_lbl_size = 12.0
    for rv in rings:
        rr = map_r(rv)
        canvas.add_circle(
            grid_g,
            cx,
            cy,
            rr,
            fill="none",
            stroke=palette.floor,
            stroke_width=1.1,
            stroke_dasharray="3,5",
        )
        canvas.add_text(
            labels_g,
            cx + 6.0,
            cy - rr - 4.0,
            format_number(rv, "", radius_suffix, decimals=0),
            font_size=ring_lbl_size,
            font_weight=600,
            fill=palette.faint,
        )

    # Slices with crisp paper divider gaps
    gap_deg = 2.4
    ang_cursor = -90.0
    lbl_size = 14.5 if layout.mode == "slide" else 12.0
    sub_size = 12.5 if layout.mode == "slide" else 12.0

    for i, item in enumerate(items):
        sweep = (shares[i] / tot_share) * 360.0
        a0 = ang_cursor + gap_deg / 2.0
        a1 = ang_cursor + max(gap_deg + 1.0, sweep) - gap_deg / 2.0
        mid = (a0 + a1) / 2.0
        r_out = map_r(radii[i])
        col = palette.series_color(i)

        d = _sector_path(cx, cy, r_inner, r_out, a0, a1)
        canvas.add_path(
            marks_g,
            d,
            fill=col,
            fill_opacity=0.90,
            stroke=palette.bg,
            stroke_width=2.0,
            stroke_linejoin="round",
        )

        # Callout line & dual-value label outside max ring
        gx, gy = pol(cx, cy, r_out + 6.0, mid)
        lx, ly = pol(cx, cy, r_max + (34.0 if layout.mode == "slide" else 22.0), mid)
        canvas.add_line(labels_g, gx, gy, lx, ly, stroke=palette.floor, stroke_width=1.1, stroke_dasharray="2,3")

        cos_a = math.cos(mid * D2R)
        if cos_a > 0.25:
            anchor = "start"
            tx = lx + 8.0
        elif cos_a < -0.25:
            anchor = "end"
            tx = lx - 8.0
        else:
            anchor = "middle"
            tx = lx

        pct_s = f"{int(round((shares[i] / tot_share) * 100))}%"
        rad_s = format_number(radii[i], "", radius_suffix, decimals=0)
        canvas.add_text(
            labels_g,
            tx,
            ly - 2.0,
            str(item["label"]),
            font_size=lbl_size,
            font_weight=800,
            fill=col if i < 3 else palette.ink,
            text_anchor=anchor,
        )
        canvas.add_text(
            labels_g,
            tx,
            ly + sub_size + 3.0,
            f"{pct_s} · {rad_s}",
            font_size=sub_size,
            font_weight=600,
            fill=palette.muted,
            text_anchor=anchor,
        )
        ang_cursor += sweep

    # Center clean punch hole
    canvas.add_circle(marks_g, cx, cy, r_inner * 0.72, fill=palette.bg)

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
