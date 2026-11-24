#!/usr/bin/env python3
"""L20 · Parallel Coordinates — Multi-dimensional editorial hairline bundle.

One smooth cubic-Bézier hairline per entity crossing 3-6 vertical dimension
axes. Axis caps show domain min/max; the overall leader (or explicitly flagged
hero entity) stands bold in the accent color with a right-side callout, while
peers recede in delicate theme hairlines.
"""

from __future__ import annotations

from typing import Any, Dict, List

from palette import ThemePalette
from svg_builder import FrameLayout, SvgCanvas, estimate_text_width, fmt, format_number, rnd


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    dims: List[Dict[str, Any]] = spec["dimensions"]
    items: List[Dict[str, Any]] = spec["data"]
    if len(dims) < 3 or len(items) < 2:
        raise ValueError("parallel_coords requires >= 3 dimensions and >= 2 data items")

    title = spec.get("title", "Entities across multiple dimensions")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "PARALLEL COORDS")
    unit_note = spec.get(
        "unit_note",
        "ONE HAIRLINE = ONE ENTITY ACROSS DIMENSIONS · ACCENT = OVERALL LEADER",
    )

    n_dims = len(dims)
    # Determine hero item (explicit `highlight: true` or highest normalized sum on non-neutral dims)
    hero_idx = next((i for i, d in enumerate(items) if d.get("highlight")), None)
    if hero_idx is None:
        best_score = -1e9
        hero_idx = 0
        for i, item in enumerate(items):
            sc = 0.0
            for di, dim in enumerate(dims):
                if dim.get("neutral"):
                    continue
                lo, hi = float(dim["min"]), float(dim["max"])
                val = float(item["values"][di])
                norm = (val - lo) / max(hi - lo, 1e-6)
                if dim.get("invert"):
                    norm = 1.0 - norm
                sc += norm
            if sc > best_score:
                best_score = sc
                hero_idx = i

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "parallel-coords"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    hero_lbl = str(items[hero_idx]["label"])
    hero_lbl_size = 15.0 if layout.mode == "slide" else 12.5
    right_reserve = max(110.0 if layout.mode == "slide" else 76.0, estimate_text_width(hero_lbl, hero_lbl_size) + 34.0)
    left_pad = 60.0 if layout.mode == "slide" else 36.0
    top_pad = 58.0 if layout.mode == "slide" else 46.0
    bot_pad = 34.0 if layout.mode == "slide" else 26.0

    x0 = layout.chart_x + left_pad
    x1 = layout.chart_right - right_reserve
    y_top = layout.chart_y + top_pad
    y_bot = layout.chart_bottom - bot_pad

    ax_xs = [x0 + (di / max(n_dims - 1, 1)) * (x1 - x0) for di in range(n_dims)]

    def map_y(di: int, v: float) -> float:
        lo, hi = float(dims[di]["min"]), float(dims[di]["max"])
        norm = (v - lo) / max(hi - lo, 1e-6)
        norm = max(0.0, min(1.0, norm))
        return y_bot - norm * (y_bot - y_top)

    grid_g = canvas.add_group(area, "chart-grid")
    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    dim_lbl_size = 13.5 if layout.mode == "slide" else 12.0
    cap_size = 12.0

    # Vertical axes + cap ticks + min/max labels
    for di, dim in enumerate(dims):
        ax = ax_xs[di]
        canvas.add_line(grid_g, ax, y_top - 10, ax, y_bot + 10, stroke=palette.floor, stroke_width=1.5)
        canvas.add_line(grid_g, ax - 7, y_top - 10, ax + 7, y_top - 10, stroke=palette.floor, stroke_width=1.5)
        canvas.add_line(grid_g, ax - 7, y_bot + 10, ax + 7, y_bot + 10, stroke=palette.floor, stroke_width=1.5)

        canvas.add_text(
            labels_g,
            ax,
            y_top - (26.0 if layout.mode == "slide" else 20.0),
            str(dim["label"]),
            font_size=dim_lbl_size,
            font_weight=800,
            fill=palette.label,
            text_anchor="middle",
            letter_spacing=0.8,
        )
        canvas.add_text(
            labels_g,
            ax + 12.0,
            y_top - 4.0,
            format_number(float(dim["max"])),
            font_size=cap_size,
            font_weight=600,
            fill=palette.faint,
        )
        canvas.add_text(
            labels_g,
            ax + 12.0,
            y_bot + 14.0,
            format_number(float(dim["min"])),
            font_size=cap_size,
            font_weight=600,
            fill=palette.faint,
        )

    accent_col = palette.c3 if len(palette.colors) >= 3 else palette.c2
    secondary_highlight = next((i for i, d in enumerate(items) if d.get("secondary")), None)

    # Draw peer lines first, then secondary, then hero on top
    draw_order = [i for i in range(len(items)) if i != hero_idx and i != secondary_highlight]
    if secondary_highlight is not None and secondary_highlight != hero_idx:
        draw_order.append(secondary_highlight)
    draw_order.append(hero_idx)

    for i in draw_order:
        item = items[i]
        ys = [map_y(di, float(item["values"][di])) for di in range(n_dims)]
        is_hero = i == hero_idx
        is_sec = i == secondary_highlight

        d_parts = [f"M {fmt(ax_xs[0])} {fmt(ys[0])}"]
        for k in range(n_dims - 1):
            mx = (ax_xs[k] + ax_xs[k + 1]) / 2.0
            d_parts.append(
                f"C {fmt(mx)} {fmt(ys[k])} {fmt(mx)} {fmt(ys[k + 1])} {fmt(ax_xs[k + 1])} {fmt(ys[k + 1])}"
            )
        path_d = " ".join(d_parts)

        if is_hero:
            col = accent_col
            sw = 3.2 if layout.mode == "slide" else 2.4
            op = 1.0
            dr = 5.5 if layout.mode == "slide" else 4.0
        elif is_sec:
            col = palette.c2
            sw = 2.4 if layout.mode == "slide" else 1.8
            op = 0.90
            dr = 4.2 if layout.mode == "slide" else 3.2
        else:
            col = palette.c1
            sw = 1.2 if layout.mode == "slide" else 0.95
            op = 0.34 + rnd(i + 1, 5) * 0.24
            dr = 2.6 if layout.mode == "slide" else 2.0

        canvas.add_path(marks_g, path_d, fill="none", stroke=col, stroke_width=sw, stroke_opacity=op)
        for di, py in enumerate(ys):
            canvas.add_circle(marks_g, ax_xs[di], py, dr, fill=col, fill_opacity=min(1.0, op + 0.15))

        if is_hero or is_sec:
            canvas.add_text(
                labels_g,
                ax_xs[-1] + 16.0,
                ys[-1] + hero_lbl_size * 0.34,
                str(item["label"]),
                font_size=hero_lbl_size if is_hero else (13.5 if layout.mode == "slide" else 12.0),
                font_weight=800 if is_hero else 700,
                fill=col,
            )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
