#!/usr/bin/env python3
"""L-EX4 · Radial Convergence — Outer rim records bundled inward to theme hubs (GitHub homepage classic).

Individual records stand around the outer rim; curved quadratic Bézier hairlines
pull each record inward to the theme hub that claimed it. Hub circles sit on an
inner ring sized by `sqrt(count)`, colored with the 2-3 custom theme colors,
with bold theme + count labels outside each sector.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

from palette import ThemePalette
from svg_builder import D2R, FrameLayout, SvgCanvas, fmt, pol


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    themes: List[Dict[str, Any]] = spec["themes"]
    if len(themes) < 2:
        raise ValueError("radial_convergence requires at least 2 themes in 'themes'")

    title = spec.get("title", "Requests pull toward core themes")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "RADIAL CONVERGENCE")
    unit_note = spec.get(
        "unit_note",
        "ONE RIM DOT = ONE RECORD · CURVES BUNDLE INTO CLAIMING THEME · HUB AREA ∝ COUNT",
    )

    # Flatten rim records grouped by theme so bundles read cleanly without spaghetti crossing
    counts = [len(t.get("items", [])) or int(t.get("count", 0)) for t in themes]
    total_records = sum(counts)
    if total_records <= 0:
        raise ValueError("radial_convergence requires positive item counts")
    max_cnt = max(counts) or 1

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "radial-convergence"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    cx = layout.chart_x + layout.chart_w / 2.0
    cy = layout.chart_y + layout.chart_h / 2.0
    r_rim = min(layout.chart_w * 0.29, layout.chart_h * 0.39)
    r_hub = r_rim * 0.32
    r_ctrl = r_rim * 0.62
    r_label = r_rim + (38.0 if layout.mode == "slide" else 26.0)

    grid_g = canvas.add_group(area, "chart-grid")
    threads_g = canvas.add_group(area, "chart-threads")
    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    # Subtle outer rim reference circle
    canvas.add_circle(
        grid_g,
        cx,
        cy,
        r_rim,
        fill="none",
        stroke=palette.quiet,
        stroke_width=1.0,
        stroke_dasharray="2,5",
    )

    max_hub_r = 16.0 if layout.mode == "slide" else 11.0
    rim_dot_r = 3.0 if layout.mode == "slide" else 2.2
    lbl_size = 14.5 if layout.mode == "slide" else 12.0

    # Distribute angles around full 360° starting at 12 o'clock (-90°)
    cursor = 0
    for ti, theme in enumerate(themes):
        cnt = counts[ti]
        if cnt <= 0:
            continue
        col = palette.series_color(ti)
        start_idx = cursor
        end_idx = cursor + cnt - 1
        mid_ang = ((start_idx + end_idx) / 2.0 / total_records) * 360.0 - 90.0

        hx, hy = pol(cx, cy, r_hub, mid_ang)
        hub_r = max(6.0, math.sqrt(cnt / max_cnt) * max_hub_r)

        bundle_g = canvas.add_group(threads_g, f"bundle-{ti+1}")
        for k in range(cnt):
            rec_idx = cursor + k
            ang = (rec_idx / total_records) * 360.0 - 90.0
            rx, ry = pol(cx, cy, r_rim, ang)
            # Pull control point slightly toward theme mid-angle for graceful bundling
            ctrl_ang = ang * 0.45 + mid_ang * 0.55
            qx, qy = pol(cx, cy, r_ctrl, ctrl_ang)
            canvas.add_path(
                bundle_g,
                f"M {fmt(rx)} {fmt(ry)} Q {fmt(qx)} {fmt(qy)} {fmt(hx)} {fmt(hy)}",
                fill="none",
                stroke=col,
                stroke_width=1.25 if layout.mode == "slide" else 0.95,
                stroke_opacity=0.45,
            )
            canvas.add_circle(marks_g, rx, ry, rim_dot_r, fill=col, fill_opacity=0.88)

        # Theme hub node on top of incoming curves
        canvas.add_circle(marks_g, hx, hy, hub_r, fill=col)

        # Sector label outside rim with short dotted leader
        gx, gy = pol(cx, cy, r_rim + 8.0, mid_ang)
        lx, ly = pol(cx, cy, r_label, mid_ang)
        canvas.add_line(labels_g, gx, gy, lx, ly, stroke=palette.floor, stroke_width=1.1, stroke_dasharray="2,3")

        cos_a = math.cos(mid_ang * D2R)
        if cos_a > 0.25:
            anchor = "start"
            tx = lx + 8.0
        elif cos_a < -0.25:
            anchor = "end"
            tx = lx - 8.0
        else:
            anchor = "middle"
            tx = lx
        ty = ly + (lbl_size * 0.35 if abs(math.sin(mid_ang * D2R)) < 0.85 else (14.0 if math.sin(mid_ang * D2R) > 0 else -6.0))

        canvas.add_text(
            labels_g,
            tx,
            ty,
            f"{theme['label']} · {cnt}",
            font_size=lbl_size,
            font_weight=800,
            fill=col if ti < 3 else palette.ink,
            text_anchor=anchor,
            letter_spacing=0.6,
        )
        cursor += cnt

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
