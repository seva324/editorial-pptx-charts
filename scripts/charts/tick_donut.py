#!/usr/bin/env python3
"""F4 · Tick Donut — 100-tick clock-dial editorial composition chart.

100 radial hairline ticks around a ring (1 tick = 1%), segmented by the 2-3
theme colors + calibrated tints. Every 10th tick has an inner dot marker.
Center shows the headline total & unit; outside labels connect via dotted radial
hairlines.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

from palette import ThemePalette
from svg_builder import D2R, FrameLayout, SvgCanvas, fmt, format_number, pol, rnd


def _normalize_to_100(values: List[float]) -> List[int]:
    total = sum(values)
    if total <= 0:
        return [0] * len(values)
    raw = [v / total * 100.0 for v in values]
    floors = [int(math.floor(r)) for r in raw]
    rem = 100 - sum(floors)
    order = sorted(range(len(raw)), key=lambda i: raw[i] - floors[i], reverse=True)
    for idx in order[:rem]:
        floors[idx] += 1
    return floors


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    items: List[Dict[str, Any]] = spec["data"]
    if not items:
        raise ValueError("tick_donut requires non-empty 'data' list")

    title = spec.get("title", "Composition around the dial")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "TICK DONUT")
    center_value = spec.get("center_value", "100%")
    center_label = spec.get("center_label", "TICKS · ONE = 1%")
    unit_note = spec.get(
        "unit_note",
        "TWELVE O'CLOCK IS ZERO · DOT MARKS EVERY TENTH · READS CLOCKWISE",
    )

    raw_vals = [max(0.0, float(d["value"])) for d in items]
    pcts = _normalize_to_100(raw_vals)

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "tick-donut"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    cx = layout.chart_x + layout.chart_w / 2.0
    cy = layout.chart_y + layout.chart_h / 2.0
    max_r = min(layout.chart_w * 0.25, layout.chart_h * 0.36)
    r0 = max_r * 0.72
    tick_min = max_r * 0.16
    tick_var = max_r * 0.10
    stroke_w = 2.2 if layout.mode == "slide" else 1.7

    canvas.add_comment(
        area,
        f"chart-plot-area: object={canvas.chart_id} | donut | "
        f"center: {fmt(cx)},{fmt(cy)} | outer-radius: {fmt(r0 + tick_min + tick_var)} | inner-radius: {fmt(r0)}",
    )

    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    lbl_size = 14.5 if layout.mode == "slide" else 12.0
    center_num_size = 44.0 if layout.mode == "slide" else 28.0
    center_sub_size = 12.5 if layout.mode == "slide" else 12.0
    dot_r = 2.0 if layout.mode == "slide" else 1.5

    k0 = 0
    for si, item in enumerate(items):
        name = str(item["label"])
        v_pct = pcts[si]
        col = palette.series_color(si)
        seg_g = canvas.add_group(marks_g, f"segment-{si+1}")

        for k in range(v_pct):
            idx = k0 + k
            ang = idx * 3.6 - 90.0
            tlen = tick_min + rnd(idx + 1, si + 2) * tick_var
            x1, y1 = pol(cx, cy, r0, ang)
            x2, y2 = pol(cx, cy, r0 + tlen, ang)
            canvas.add_line(
                seg_g,
                x1,
                y1,
                x2,
                y2,
                stroke=col,
                stroke_width=stroke_w,
                stroke_linecap="round",
            )
            if idx % 10 == 0:
                dx, dy = pol(cx, cy, r0 - (10.0 if layout.mode == "slide" else 7.0), ang)
                canvas.add_circle(seg_g, dx, dy, dot_r, fill=palette.faint)

        # Callout line & segment label at mid-angle
        if v_pct > 0:
            mid = (k0 + v_pct / 2.0) * 3.6 - 90.0
            gx, gy = pol(cx, cy, r0 + tick_min + tick_var + 8.0, mid)
            lx, ly = pol(cx, cy, r0 + tick_min + tick_var + (46.0 if layout.mode == "slide" else 30.0), mid)
            canvas.add_line(
                labels_g,
                gx,
                gy,
                lx,
                ly,
                stroke=palette.floor,
                stroke_width=1.2,
                stroke_dasharray="2,4",
            )
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
            ty = ly + lbl_size * 0.32
            disp_val = item.get("display_value", f"{v_pct}%")
            canvas.add_text(
                labels_g,
                tx,
                ty,
                f"{name} · {disp_val}",
                font_size=lbl_size,
                font_weight=700,
                fill=col,
                text_anchor=anchor,
                letter_spacing=0.6,
            )
        k0 += v_pct

    # Center KPI
    canvas.add_text(
        labels_g,
        cx,
        cy + center_num_size * 0.10,
        str(center_value),
        font_size=center_num_size,
        font_weight=800,
        fill=palette.ink,
        text_anchor="middle",
    )
    canvas.add_text(
        labels_g,
        cx,
        cy + center_num_size * 0.10 + center_sub_size * 1.9,
        str(center_label),
        font_size=center_sub_size,
        font_weight=600,
        fill=palette.muted,
        text_anchor="middle",
        letter_spacing=1.0,
    )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
