#!/usr/bin/env python3
"""G21 · Rank Strip — Static printable filmstrip of rank evolution over time.

Avoids messy crossing bump-chart spaghetti lines: one row per entity (sorted by
final rank so the winner lands on top), one rounded square tile per period
carrying the exact rank number (#1 wears the accent color, lower ranks step
smoothly down the theme ramp), plus net climb/drop flags (▲ / ▼ / —) at row end.
"""

from __future__ import annotations

from typing import Any, Dict, List

from palette import ThemePalette, contrast_ratio
from svg_builder import FrameLayout, SvgCanvas, estimate_text_width, fmt


def _text_on_fill(fill_hex: str, palette: ThemePalette) -> str:
    light_txt = "#FFFFFF" if not palette.dark else palette.ink
    dark_txt = palette.ink if not palette.dark else palette.bg
    if contrast_ratio(light_txt, fill_hex) >= 3.4:
        return light_txt
    return dark_txt


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    periods: List[str] = [str(p) for p in spec["periods"]]
    items: List[Dict[str, Any]] = list(spec["data"])
    if not periods or not items:
        raise ValueError("rank_strip requires non-empty 'periods' and 'data'")

    # Sort by final rank ascending (#1 at top) unless disabled
    if spec.get("sort_by_final_rank", True):
        items.sort(key=lambda d: int(d["ranks"][-1]))

    title = spec.get("title", "Ranking evolution across periods")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "RANK STRIP")
    unit_note = spec.get(
        "unit_note",
        "CELL = RANK THAT PERIOD · #1 WEARS ACCENT · RIGHT = NET CLIMB / DROP",
    )

    n_rows = len(items)
    n_cols = len(periods)
    max_rank = max(int(r) for d in items for r in d["ranks"])

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "rank-strip"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    row_lbl_size = 15.0 if layout.mode == "slide" else 12.5
    col_lbl_size = 13.5 if layout.mode == "slide" else 12.0
    max_row_px = max(estimate_text_width(str(d["label"]), row_lbl_size) for d in items)
    left_rail = min(layout.chart_w * 0.26, max(110.0 if layout.mode == "slide" else 82.0, max_row_px + 24.0))
    right_rail = 92.0 if layout.mode == "slide" else 64.0
    top_pad = 40.0 if layout.mode == "slide" else 30.0
    bot_pad = 16.0 if layout.mode == "slide" else 10.0

    avail_w = layout.chart_w - left_rail - right_rail
    avail_h = layout.chart_h - top_pad - bot_pad
    gap_x = 14.0 if layout.mode == "slide" else 8.0
    gap_y = 14.0 if layout.mode == "slide" else 8.0

    cell = min(
        (avail_w - gap_x * (n_cols - 1)) / max(n_cols, 1),
        (avail_h - gap_y * (n_rows - 1)) / max(n_rows, 1),
        68.0 if layout.mode == "slide" else 44.0,
    )
    grid_w = cell * n_cols + gap_x * (n_cols - 1)
    grid_h = cell * n_rows + gap_y * (n_rows - 1)

    x0 = layout.chart_x + left_rail + (avail_w - grid_w) / 2.0
    y0 = layout.chart_y + top_pad + (avail_h - grid_h) / 2.0

    canvas.add_comment(
        area,
        f"chart-plot-area: object={canvas.chart_id} | "
        f"{fmt(x0)},{fmt(y0)},{fmt(x0 + grid_w)},{fmt(y0 + grid_h)}",
    )

    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    accent_col = palette.c3 if len(palette.colors) >= 3 else palette.c2
    num_size = 18.0 if layout.mode == "slide" else 13.5
    delta_size = 15.0 if layout.mode == "slide" else 12.5
    rx = min(14.0 if layout.mode == "slide" else 8.0, cell * 0.25)

    # Period column headers
    for c, pname in enumerate(periods):
        cx = x0 + c * (cell + gap_x) + cell / 2.0
        canvas.add_text(
            labels_g,
            cx,
            y0 - (14.0 if layout.mode == "slide" else 10.0),
            pname,
            font_size=col_lbl_size,
            font_weight=700,
            fill=palette.muted,
            text_anchor="middle",
            letter_spacing=0.8,
        )

    for i, item in enumerate(items):
        ranks = [int(r) for r in item["ranks"]]
        ry = y0 + i * (cell + gap_y)
        is_winner = ranks[-1] == 1

        canvas.add_text(
            labels_g,
            x0 - 18.0,
            ry + cell / 2.0 + row_lbl_size * 0.34,
            str(item["label"]),
            font_size=row_lbl_size,
            font_weight=800 if is_winner else 600,
            fill=palette.ink if is_winner else palette.label,
            text_anchor="end",
        )

        row_g = canvas.add_group(marks_g, f"strip-row-{i+1}")
        for q, rk in enumerate(ranks):
            cx = x0 + q * (cell + gap_x)
            if rk == 1:
                fill_col = accent_col
            else:
                # Higher rank (smaller number) = darker theme tone
                norm = 1.0 - (rk - 1) / max(max_rank - 1, 1)
                fill_col = palette.ramp_color(norm * 0.78)
            canvas.add_rect(
                row_g,
                cx,
                ry,
                cell,
                cell,
                fill=fill_col,
                stroke=palette.grid,
                stroke_width=0.8,
                rx=rx,
            )
            txt_col = _text_on_fill(fill_col, palette)
            canvas.add_text(
                labels_g,
                cx + cell / 2.0,
                ry + cell / 2.0 + num_size * 0.35,
                str(rk),
                font_size=num_size,
                font_weight=800,
                fill=txt_col,
                text_anchor="middle",
            )

        # Arrival delta flag at right end of row
        delta = ranks[0] - ranks[-1]
        if delta > 0:
            flag_txt = f"▲ {delta}"
            flag_col = accent_col if is_winner else palette.c1
        elif delta < 0:
            flag_txt = f"▼ {-delta}"
            flag_col = palette.c2 if len(palette.colors) >= 2 else palette.muted
        else:
            flag_txt = "—"
            flag_col = palette.faint

        canvas.add_text(
            labels_g,
            x0 + grid_w + 18.0,
            ry + cell / 2.0 + delta_size * 0.34,
            flag_txt,
            font_size=delta_size,
            font_weight=800,
            fill=flag_col,
        )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
