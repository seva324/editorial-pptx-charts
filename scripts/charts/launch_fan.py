#!/usr/bin/env python3
"""L1 · Launch Fan — Radial fan timeline encoding birth time + current scale.

One spoke per entity fanning across a quadrant arc. Concentric dotted guide
arcs mark time milestones; the large circle sits at the launch period (area
proportional to current scale via sqrt), while small weekly texture dots trace
every period elapsed since launch out to the labeled rim.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

from palette import ThemePalette, mix_hex
from svg_builder import FrameLayout, SvgCanvas, fmt, format_number, pol, rnd


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    items: List[Dict[str, Any]] = list(spec["data"])
    if len(items) < 2:
        raise ValueError("launch_fan requires at least 2 items in 'data'")

    # Sort by launch period so big dots cascade cleanly along a diagonal arc
    if spec.get("sort_by_launch", True):
        items.sort(key=lambda d: float(d["launch"]))

    title = spec.get("title", "Features, fanned out by launch")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "LAUNCH FAN")
    max_period = int(spec.get("max_period", max(int(d["launch"]) for d in items) + 2))
    period_prefix = spec.get("period_prefix", "W")
    guides: List[int] = spec.get("guides") or [
        max(1, int(round(max_period * f))) for f in (0.25, 0.5, 0.75, 1.0)
    ]
    unit_note = spec.get(
        "unit_note",
        "ONE SPOKE = ONE ENTITY · BIG DOT = LAUNCH TIME (AREA ∝ SCALE) · SMALL DOTS = PERIODS SINCE",
    )

    sizes = [max(1.0, float(d["size"])) for d in items]
    max_size = max(sizes) or 1.0
    hero_idx = sizes.index(max_size)

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "launch-fan"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    # Quadrant anchor bottom-left of centered fan block
    fan_r_max = min(layout.chart_h * 0.78, layout.chart_w * 0.42)
    r_inner = fan_r_max * 0.24
    r_span = fan_r_max - r_inner

    # Center fan nicely inside chart area
    cx = layout.chart_x + (layout.chart_w - fan_r_max * 1.15) / 2.0 + fan_r_max * 0.08
    cy = layout.chart_bottom - (26.0 if layout.mode == "slide" else 18.0)

    def r_of(p: float) -> float:
        return r_inner + (p / max(max_period, 1)) * r_span

    ang_start = -84.0
    ang_end = -8.0
    n = len(items)

    def ang_of(i: int) -> float:
        return ang_start + (i / max(n - 1, 1)) * (ang_end - ang_start)

    grid_g = canvas.add_group(area, "chart-grid")
    labels_g = canvas.add_group(area, "chart-labels")
    marks_g = canvas.add_group(area, "chart-marks")

    guide_size = 12.5 if layout.mode == "slide" else 12.0
    for g_val in guides:
        r = r_of(g_val)
        x1, y1 = pol(cx, cy, r, ang_start)
        x2, y2 = pol(cx, cy, r, ang_end)
        canvas.add_path(
            grid_g,
            f"M {fmt(x1)} {fmt(y1)} A {fmt(r)} {fmt(r)} 0 0 1 {fmt(x2)} {fmt(y2)}",
            fill="none",
            stroke=palette.floor,
            stroke_width=1.2,
            stroke_dasharray="3,6",
        )
        lx, ly = pol(cx, cy, r, ang_start - 5.5)
        canvas.add_text(
            labels_g,
            lx,
            ly + guide_size * 0.35,
            f"{period_prefix}{g_val}",
            font_size=guide_size,
            font_weight=600,
            fill=palette.muted,
            text_anchor="end",
        )

    accent_col = palette.c3 if len(palette.colors) >= 3 else palette.c2
    max_dot_r = 16.0 if layout.mode == "slide" else 10.5
    rim_size = 13.0 if layout.mode == "slide" else 12.0

    for i, item in enumerate(items):
        name = str(item["label"])
        launch = int(item["launch"])
        sz = sizes[i]
        ang = ang_of(i)
        is_hero = i == hero_idx

        t = i / max(n - 1, 1)
        col = accent_col if is_hero else mix_hex(palette.c1, palette.c2, t * 0.75)

        spoke_g = canvas.add_group(marks_g, f"spoke-{i+1}")
        sx, sy = pol(cx, cy, r_of(launch), ang)
        ex, ey = pol(cx, cy, r_of(max_period), ang)
        canvas.add_line(spoke_g, sx, sy, ex, ey, stroke=palette.grid, stroke_width=1.1)

        # Weekly continuation dots from launch+1 to max_period
        for p in range(launch + 1, max_period + 1):
            dx, dy = pol(cx, cy, r_of(p), ang)
            sr = (2.0 + rnd(i + 1, p) * 1.8) if layout.mode == "slide" else (1.5 + rnd(i + 1, p) * 1.2)
            canvas.add_circle(spoke_g, dx, dy, sr, fill=col, fill_opacity=0.62)

        # Launch bubble sized by sqrt(size)
        br = max(4.5, math.sqrt(sz / max_size) * max_dot_r)
        canvas.add_circle(spoke_g, sx, sy, br, fill=col)

        # Rim label rotated along spoke
        tx, ty = pol(cx, cy, r_of(max_period) + (16.0 if layout.mode == "slide" else 11.0), ang)
        canvas.add_text(
            labels_g,
            tx,
            ty + rim_size * 0.32,
            name,
            font_size=rim_size,
            font_weight=700 if is_hero else 600,
            fill=col if is_hero else palette.label,
            rotate=(ang, tx, ty),
        )

    # Subtle legend on right side in slide mode showing scale & leader
    if layout.mode == "slide":
        leg_x = cx + fan_r_max * 0.96
        leg_y = layout.chart_y + 42.0
        if leg_x + 210 < layout.chart_right:
            hero_item = items[hero_idx]
            canvas.add_circle(labels_g, leg_x + 8, leg_y, 7.5, fill=accent_col)
            canvas.add_text(
                labels_g,
                leg_x + 24,
                leg_y + 5.0,
                f"最大规模：{hero_item['label']} ({format_number(sizes[hero_idx], spec.get('size_prefix', ''), spec.get('size_suffix', ''))})",
                font_size=13.5,
                font_weight=700,
                fill=accent_col,
            )
            canvas.add_circle(labels_g, leg_x + 8, leg_y + 30.0, 5.5, fill=palette.c1)
            canvas.add_text(
                labels_g,
                leg_x + 24,
                leg_y + 35.0,
                "上线节点（面积 ∝ 当前活跃规模）",
                font_size=13.0,
                font_weight=500,
                fill=palette.label,
            )
            canvas.add_circle(labels_g, leg_x + 8, leg_y + 58.0, 2.8, fill=palette.c1, fill_opacity=0.65)
            canvas.add_text(
                labels_g,
                leg_x + 24,
                leg_y + 63.0,
                "上线后每个周期延续点",
                font_size=13.0,
                font_weight=500,
                fill=palette.muted,
            )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
