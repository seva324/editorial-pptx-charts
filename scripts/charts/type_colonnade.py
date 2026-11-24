#!/usr/bin/env python3
"""L-EX3 · Type Colonnade — Many-to-one ownership hairline bundle (GitHub homepage classic).

Left column lists individual items; smooth cubic Bézier hairlines hand every
item across to its owning group on the right. Right-side hub circles scale by
area (`sqrt(count)`) and sort descending so organizational pile-ups reveal
themselves at a glance.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

from palette import ThemePalette
from svg_builder import FrameLayout, SvgCanvas, estimate_text_width, fmt


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    items: List[Dict[str, Any]] = spec["items"]
    if not items:
        raise ValueError("type_colonnade requires non-empty 'items' list of {label, owner}")

    title = spec.get("title", "Items mapped to their owners")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "TYPE COLONNADE")
    unit_note = spec.get(
        "unit_note",
        "ONE HAIRLINE = ONE ITEM → OWNER · RIGHT CIRCLE AREA ∝ COUNT · ACCENT = LARGEST OWNER",
    )

    # Aggregate owners and sort descending by count
    owner_counts: Dict[str, int] = {}
    for it in items:
        ow = str(it["owner"])
        owner_counts[ow] = owner_counts.get(ow, 0) + 1

    explicit_order: List[str] = spec.get("owner_order") or sorted(
        owner_counts.keys(), key=lambda k: (-owner_counts[k], k)
    )
    owners = [(ow, owner_counts.get(ow, 0)) for ow in explicit_order if owner_counts.get(ow, 0) > 0]
    owner_idx_map = {ow: i for i, (ow, _) in enumerate(owners)}
    max_cnt = max(c for _, c in owners) or 1

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "type-colonnade"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    item_lbl_size = 12.0
    owner_lbl_size = 14.5 if layout.mode == "slide" else 12.0

    max_item_px = max(estimate_text_width(str(it["label"]), item_lbl_size) for it in items)
    max_owner_px = max(estimate_text_width(f"{ow} · {cnt}", owner_lbl_size) for ow, cnt in owners)

    left_text_edge = layout.chart_x + min(layout.chart_w * 0.25, max(110.0, max_item_px + 12.0))
    right_node_x = layout.chart_right - min(layout.chart_w * 0.28, max(140.0, max_owner_px + 44.0))
    x_start = left_text_edge + 14.0

    top_pad = 16.0 if layout.mode == "slide" else 12.0
    bot_pad = 16.0 if layout.mode == "slide" else 12.0
    y_top = layout.chart_y + top_pad
    y_bot = layout.chart_bottom - bot_pad

    n_items = len(items)
    n_owners = len(owners)

    def item_y(i: int) -> float:
        return y_top + (i / max(n_items - 1, 1)) * (y_bot - y_top) if n_items > 1 else (y_top + y_bot) / 2.0

    def owner_y(j: int) -> float:
        return y_top + 14.0 + (j / max(n_owners - 1, 1)) * (y_bot - y_top - 28.0) if n_owners > 1 else (y_top + y_bot) / 2.0

    threads_g = canvas.add_group(area, "chart-threads")
    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    accent_col = palette.c3 if len(palette.colors) >= 3 else palette.c2
    max_r = 20.0 if layout.mode == "slide" else 13.5

    def owner_color(oi: int) -> str:
        if oi == 0:
            return accent_col
        if oi <= 2:
            return palette.c1
        return palette.c2 if len(palette.colors) >= 2 else palette.muted

    # 1. Draw Bézier ownership threads + left item labels
    # Skip alternate labels only if item spacing < 13.5px to prevent vertical text overlap
    item_gap = (y_bot - y_top) / max(n_items - 1, 1)
    lbl_stride = 1 if item_gap >= 14.0 else 2
    cx_mid_l = x_start + (right_node_x - x_start) * 0.46
    cx_mid_r = x_start + (right_node_x - x_start) * 0.56

    for i, it in enumerate(items):
        oy_idx = owner_idx_map[str(it["owner"])]
        y1 = item_y(i)
        y2 = owner_y(oy_idx)
        col = owner_color(oy_idx)
        is_top = oy_idx == 0

        d = f"M {fmt(x_start)} {fmt(y1)} C {fmt(cx_mid_l)} {fmt(y1)} {fmt(cx_mid_r)} {fmt(y2)} {fmt(right_node_x)} {fmt(y2)}"
        canvas.add_path(
            threads_g,
            d,
            fill="none",
            stroke=col,
            stroke_width=1.5 if is_top else 1.1,
            stroke_opacity=0.58 if is_top else 0.34,
        )
        canvas.add_circle(marks_g, x_start, y1, 2.2 if is_top else 1.6, fill=col, fill_opacity=0.85)

        if i % lbl_stride == 0:
            canvas.add_text(
                labels_g,
                left_text_edge,
                y1 + item_lbl_size * 0.34,
                str(it["label"]),
                font_size=item_lbl_size,
                font_weight=600 if is_top else 500,
                fill=palette.label if is_top else palette.muted,
                text_anchor="end",
            )

    # 2. Draw right owner hub nodes + bold counts
    for oi, (ow, cnt) in enumerate(owners):
        cy = owner_y(oi)
        col = owner_color(oi)
        rad = max(5.0, math.sqrt(cnt / max_cnt) * max_r)
        is_top = oi == 0

        canvas.add_circle(marks_g, right_node_x, cy, rad, fill=col)
        canvas.add_text(
            labels_g,
            right_node_x + max_r + 14.0,
            cy + owner_lbl_size * 0.34,
            f"{ow} · {cnt}",
            font_size=owner_lbl_size,
            font_weight=800 if is_top else 700,
            fill=col if is_top else palette.ink,
            letter_spacing=0.6,
        )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
