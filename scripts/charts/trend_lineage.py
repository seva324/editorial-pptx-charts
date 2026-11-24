#!/usr/bin/env python3
"""L-EX2 · Trend Lineage — Vertical lifecycle timeline (GitHub homepage classic).

Years flow top-to-bottom across delicate horizontal rules. Each column tracks
one feature/initiative: solid circle = shipped/launched, hollow circle =
reworked/pivoted, solid vertical stem = active years, dashed stem = dormant
years, and a terminal anchor dot at the bottom marks entities still alive today.
"""

from __future__ import annotations

from typing import Any, Dict, List

from palette import ThemePalette
from svg_builder import FrameLayout, SvgCanvas, fmt


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    items: List[Dict[str, Any]] = spec["data"]
    if not items:
        raise ValueError("trend_lineage requires non-empty 'data' list")

    title = spec.get("title", "Features rise, evolve, and endure")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "TREND LINEAGE")

    all_years: List[int] = []
    for it in items:
        for ev in it.get("events", []):
            all_years.append(int(ev["year"]))
        if it.get("end_year"):
            all_years.append(int(it["end_year"]))
    y_start = int(spec.get("start_year", min(all_years)))
    y_end = int(spec.get("end_year", max(all_years)))
    if y_end <= y_start:
        y_end = y_start + 1

    unit_note = spec.get(
        "unit_note",
        "SOLID DOT = SHIPPED · HOLLOW DOT = REWORKED · DASHED = DORMANT · BOTTOM DOT = STILL ACTIVE",
    )

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "trend-lineage"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    left_rail = 76.0 if layout.mode == "slide" else 56.0
    right_pad = 36.0 if layout.mode == "slide" else 22.0
    top_pad = 24.0 if layout.mode == "slide" else 18.0
    bot_pad = 92.0 if layout.mode == "slide" else 74.0  # room for angled bottom names

    x0 = layout.chart_x + left_rail
    x1 = layout.chart_right - right_pad
    y_top = layout.chart_y + top_pad
    y_bot = layout.chart_bottom - bot_pad

    def map_y(yr: float) -> float:
        return y_top + ((yr - y_start) / (y_end - y_start)) * (y_bot - y_top)

    n = len(items)
    slot_w = (x1 - x0) / max(n, 1)

    grid_g = canvas.add_group(area, "chart-grid")
    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    # Horizontal year grid lines
    yr_step = 2 if (y_end - y_start) >= 6 else 1
    yr_size = 12.5 if layout.mode == "slide" else 12.0
    yr_ticks = list(range(y_start, y_end + 1, yr_step))
    if y_end not in yr_ticks:
        yr_ticks.append(y_end)

    for yr in yr_ticks:
        gy = map_y(yr)
        canvas.add_line(grid_g, x0 - 12.0, gy, x1 + 8.0, gy, stroke=palette.grid, stroke_width=1.1)
        canvas.add_text(
            labels_g,
            x0 - 20.0,
            gy + yr_size * 0.35,
            str(yr),
            font_size=yr_size,
            font_weight=600,
            fill=palette.muted,
            text_anchor="end",
        )

    accent_col = palette.c3 if len(palette.colors) >= 3 else palette.c2
    node_r = 9.0 if layout.mode == "slide" else 6.5
    cat_size = 13.0 if layout.mode == "slide" else 12.0

    for i, item in enumerate(items):
        cx = x0 + (i + 0.5) * slot_w
        events = sorted(item.get("events", []), key=lambda e: float(e["year"]))
        if not events:
            continue
        alive = bool(item.get("alive", True))
        is_hero = bool(item.get("highlight", False))
        col = accent_col if is_hero else (palette.c1 if alive else palette.c2)

        col_g = canvas.add_group(marks_g, f"lineage-{i+1}")

        # Draw segments between consecutive events
        for k in range(len(events) - 1):
            y1 = map_y(float(events[k]["year"]))
            y2 = map_y(float(events[k + 1]["year"]))
            dormant = bool(events[k].get("dormant_after", False))
            canvas.add_line(
                col_g,
                cx,
                y1,
                cx,
                y2,
                stroke=col if not dormant else palette.floor,
                stroke_width=2.0 if (is_hero and not dormant) else 1.5,
                stroke_dasharray="4,4" if dormant else None,
            )

        # If still alive, run vertical line down to y_end + terminal anchor dot
        last_y = map_y(float(events[-1]["year"]))
        if alive:
            canvas.add_line(
                col_g,
                cx,
                last_y,
                cx,
                y_bot + 14.0,
                stroke=col,
                stroke_width=2.0 if is_hero else 1.5,
            )
            canvas.add_circle(col_g, cx, y_bot + 14.0, 4.2 if layout.mode == "slide" else 3.2, fill=col)
        else:
            # Small retired stop dot slightly below final event
            canvas.add_circle(col_g, cx, last_y + node_r + 10.0, 2.4, fill=palette.faint)

        # Draw event milestone nodes on top of stems
        for ev in events:
            ey = map_y(float(ev["year"]))
            kind = str(ev.get("kind", "shipped")).lower()
            if kind in ("reworked", "pivot", "hollow"):
                canvas.add_circle(
                    col_g,
                    cx,
                    ey,
                    node_r,
                    fill=palette.bg,
                    stroke=col,
                    stroke_width=2.6 if layout.mode == "slide" else 2.0,
                )
            else:
                canvas.add_circle(col_g, cx, ey, node_r, fill=col)

        # Tilted label below bottom rail
        ly = y_bot + (34.0 if layout.mode == "slide" else 28.0)
        canvas.add_text(
            labels_g,
            cx + 4.0,
            ly,
            str(item["label"]),
            font_size=cat_size,
            font_weight=700 if (alive or is_hero) else 500,
            fill=(col if is_hero else (palette.ink if alive else palette.faint)),
            text_anchor="end",
            rotate=(-40.0, cx + 4.0, ly),
        )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
