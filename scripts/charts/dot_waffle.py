#!/usr/bin/env python3
"""G4 · Dot Waffle — 10x10 unit-dot percentage grid (the editorial pie replacement).

100 solid circles arranged in a crisp 10x10 grid where every dot = 1%, colored
by the 2-3 theme colors + calibrated tints, paired with a high-legibility right
legend showing category names and large bold percentages.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

from palette import ThemePalette
from svg_builder import FrameLayout, SvgCanvas, fmt


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
        raise ValueError("dot_waffle requires non-empty 'data' list")

    title = spec.get("title", "Share out of a hundred")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "DOT WAFFLE")
    unit_note = spec.get("unit_note", "EVERY DOT = 1% · 10 × 10 GRID = 100%")

    raw_vals = [max(0.0, float(d["value"])) for d in items]
    pcts = _normalize_to_100(raw_vals)

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "dot-waffle"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    # Left 10x10 grid + right legend column
    grid_side = min(layout.chart_h * 0.90, layout.chart_w * 0.48)
    cell = grid_side / 10.0
    dot_r = cell * 0.37

    total_block_w = grid_side + (64.0 if layout.mode == "slide" else 34.0) + (300.0 if layout.mode == "slide" else 180.0)
    start_x = layout.chart_x + max(16.0, (layout.chart_w - total_block_w) / 2.0)
    start_y = layout.chart_y + (layout.chart_h - grid_side) / 2.0

    canvas.add_comment(
        area,
        f"chart-plot-area: object={canvas.chart_id} | "
        f"{fmt(start_x)},{fmt(start_y)},{fmt(start_x + grid_side)},{fmt(start_y + grid_side)}",
    )

    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    # 100 dots grouped by category
    cursor = 0
    for gi, pct in enumerate(pcts):
        col = palette.series_color(gi)
        seg_g = canvas.add_group(marks_g, f"waffle-group-{gi+1}")
        for k in range(pct):
            idx = cursor + k
            row = idx // 10
            c = idx % 10
            cx = start_x + (c + 0.5) * cell
            cy = start_y + (row + 0.5) * cell
            canvas.add_circle(seg_g, cx, cy, dot_r, fill=col)
        cursor += pct

    # Right legend column
    leg_x = start_x + grid_side + (64.0 if layout.mode == "slide" else 34.0)
    n_items = len(items)
    leg_step = min(grid_side / max(n_items, 1), 84.0 if layout.mode == "slide" else 56.0)
    leg_top = start_y + (grid_side - leg_step * (n_items - 1)) / 2.0

    swatch_r = 10.0 if layout.mode == "slide" else 7.0
    name_size = 16.0 if layout.mode == "slide" else 13.0
    pct_size = 26.0 if layout.mode == "slide" else 18.0

    for gi, item in enumerate(items):
        col = palette.series_color(gi)
        cy = leg_top + gi * leg_step
        canvas.add_circle(labels_g, leg_x, cy, swatch_r, fill=col)
        canvas.add_text(
            labels_g,
            leg_x + swatch_r + 14.0,
            cy - (3.0 if layout.mode == "slide" else 2.0),
            str(item["label"]),
            font_size=name_size,
            font_weight=600,
            fill=palette.label,
        )
        canvas.add_text(
            labels_g,
            leg_x + swatch_r + 14.0,
            cy + pct_size * 0.92,
            f"{pcts[gi]}%",
            font_size=pct_size,
            font_weight=800,
            fill=col if gi < 3 else palette.ink,
        )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
