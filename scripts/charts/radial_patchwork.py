#!/usr/bin/env python3
"""L-EX1 · Radial Patchwork — 24-hour overlaid wedge density dial (GitHub homepage classic).

Each event is drawn as a translucent radial wedge: angle encodes time of day
(00 at 12 o'clock, 06 at 3 o'clock, 12 at 6 o'clock, 18 at 9 o'clock), radius
encodes magnitude/reach, and translucency lets ink accumulate naturally where
events pile up. Flagged events (e.g. incidents/anomalies) receive crisp solid
accent outlines.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

from palette import ThemePalette
from svg_builder import FrameLayout, SvgCanvas, fmt, pol


def _wedge_path(cx: float, cy: float, r_in: float, r_out: float, a0: float, a1: float) -> str:
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
    events: List[Dict[str, Any]] = spec["data"]
    if not events:
        raise ValueError("radial_patchwork requires non-empty 'data' list")

    title = spec.get("title", "A quarter of events, overlaid by hour")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "RADIAL PATCHWORK")
    period_hours = float(spec.get("period", 24.0))
    clock_labels: List[str] = spec.get("clock_labels", ["00", "06", "12", "18"])
    flagged_legend = spec.get("flagged_legend", "OUTLINED = FLAGGED / INCIDENT")
    unit_note = spec.get(
        "unit_note",
        f"EACH WEDGE = ONE EVENT · ANGLE = TIME · REACH = MAGNITUDE · {flagged_legend}",
    )

    reaches = [max(0.1, float(e["reach"])) for e in events]
    max_reach = float(spec.get("max_reach", max(reaches))) or 1.0

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "radial-patchwork"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    cx = layout.chart_x + layout.chart_w / 2.0
    cy = layout.chart_y + layout.chart_h / 2.0
    r_dial = min(layout.chart_w, layout.chart_h) * 0.41
    r_inner = r_dial * 0.11
    r_max_wedge = r_dial * 0.90

    grid_g = canvas.add_group(area, "chart-grid")
    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    # Subtle dial rim + 24 hour ticks + concentric reference ring
    canvas.add_circle(grid_g, cx, cy, r_dial, fill="none", stroke=palette.grid, stroke_width=1.0)
    canvas.add_circle(
        grid_g,
        cx,
        cy,
        r_dial * 0.55,
        fill="none",
        stroke=palette.quiet,
        stroke_width=1.0,
        stroke_dasharray="3,5",
    )

    tick_segs: List[str] = []
    for h in range(24):
        ang = (h / 24.0) * 360.0 - 90.0
        major = h % 6 == 0
        t_in = r_dial - (10.0 if major else 5.0)
        x1, y1 = pol(cx, cy, t_in, ang)
        x2, y2 = pol(cx, cy, r_dial, ang)
        tick_segs.append(f"M {fmt(x1)} {fmt(y1)} L {fmt(x2)} {fmt(y2)}")
    canvas.add_path(grid_g, " ".join(tick_segs), fill="none", stroke=palette.floor, stroke_width=1.2)

    # 4 cardinal clock labels
    clk_size = 13.5 if layout.mode == "slide" else 12.0
    cardinals = [
        (0.0, -90.0, "middle", 0.0, -14.0),
        (1.0, 0.0, "start", 14.0, clk_size * 0.35),
        (2.0, 90.0, "middle", 0.0, 22.0),
        (3.0, 180.0, "end", -14.0, clk_size * 0.35),
    ]
    for idx, ang, anchor, dx, dy in cardinals:
        i = int(idx)
        if i < len(clock_labels):
            px, py = pol(cx, cy, r_dial, ang)
            canvas.add_text(
                labels_g,
                px + dx,
                py + dy,
                str(clock_labels[i]),
                font_size=clk_size,
                font_weight=700,
                fill=palette.muted,
                text_anchor=anchor,
                letter_spacing=0.8,
            )

    accent_col = palette.c3 if len(palette.colors) >= 3 else palette.c2

    # 1. Draw ordinary overlaid translucent wedges first (opacity encodes density!)
    normal_events = [e for e in events if not e.get("flagged")]
    flagged_events = [e for e in events if e.get("flagged")]

    for idx, ev in enumerate(normal_events):
        hr = float(ev["hour"]) % period_hours
        reach = max(0.1, float(ev["reach"]))
        span_deg = float(ev.get("span_deg", 14.0))
        ang_mid = (hr / period_hours) * 360.0 - 90.0
        r_out = r_inner + math.sqrt(reach / max_reach) * (r_max_wedge - r_inner)
        col = palette.c2 if ev.get("series") == 2 else palette.c1
        d = _wedge_path(cx, cy, r_inner, r_out, ang_mid - span_deg / 2.0, ang_mid + span_deg / 2.0)
        canvas.add_path(marks_g, d, fill=col, fill_opacity=0.17)

    # 2. Draw flagged/incident wedges on top with crisp solid accent outlines
    for idx, ev in enumerate(flagged_events):
        hr = float(ev["hour"]) % period_hours
        reach = max(0.1, float(ev["reach"]))
        span_deg = float(ev.get("span_deg", 15.0))
        ang_mid = (hr / period_hours) * 360.0 - 90.0
        r_out = r_inner + math.sqrt(reach / max_reach) * (r_max_wedge - r_inner)
        d = _wedge_path(cx, cy, r_inner, r_out, ang_mid - span_deg / 2.0, ang_mid + span_deg / 2.0)
        canvas.add_path(
            marks_g,
            d,
            fill=accent_col,
            fill_opacity=0.22,
            stroke=accent_col,
            stroke_width=2.2 if layout.mode == "slide" else 1.6,
            stroke_linejoin="round",
        )

    # Center anchor dot
    canvas.add_circle(marks_g, cx, cy, 5.5 if layout.mode == "slide" else 4.0, fill=palette.ink)

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
