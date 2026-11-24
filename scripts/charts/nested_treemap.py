#!/usr/bin/env python3
"""F13 · Nested Treemap — Pure-static squarified 2-level hierarchical treemap.

Zero ECharts dependency: uses deterministic squarified treemap partitioning in
pure Python. Area is strictly proportional to leaf weight; top-level groups are
distinguished by parent title headers, clean paper gutters, and the 2-3 custom
theme colors (plus calibrated tints when >3 parent groups).
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from palette import ThemePalette, contrast_ratio, mix_hex
from svg_builder import FrameLayout, SvgCanvas, fmt, format_number


Rect = Tuple[float, float, float, float]  # x, y, w, h


def _worst_aspect(row: List[float], side: float) -> float:
    if not row or side <= 0:
        return float("inf")
    s = sum(row)
    rmax = max(row)
    rmin = min(row)
    if rmin <= 0 or s <= 0:
        return float("inf")
    s2 = s * s
    side2 = side * side
    return max((side2 * rmax) / s2, s2 / (side2 * rmin))


def _squarify(values: List[float], x: float, y: float, w: float, h: float) -> List[Rect]:
    """Deterministic Bruls-Huizing-van Wijk squarified treemap layout."""
    total = sum(values)
    if total <= 0 or w <= 0 or h <= 0:
        return [(x, y, 0.0, 0.0) for _ in values]

    area_scale = (w * h) / total
    indexed = sorted(enumerate(values), key=lambda t: t[1], reverse=True)
    scaled = [(i, v * area_scale) for i, v in indexed]
    out: Dict[int, Rect] = {}

    rx, ry, rw, rh = x, y, w, h
    idx = 0
    n = len(scaled)

    while idx < n:
        short = min(rw, rh)
        row_items: List[Tuple[int, float]] = [scaled[idx]]
        idx += 1
        while idx < n:
            cand = [v for _, v in row_items] + [scaled[idx][1]]
            cur = [v for _, v in row_items]
            if _worst_aspect(cand, short) <= _worst_aspect(cur, short):
                row_items.append(scaled[idx])
                idx += 1
            else:
                break

        row_sum = sum(v for _, v in row_items)
        if rw >= rh:
            # Lay out a vertical strip on the left
            strip_w = row_sum / max(rh, 1e-6)
            cy = ry
            for orig_i, val in row_items:
                item_h = val / max(strip_w, 1e-6)
                out[orig_i] = (rx, cy, strip_w, item_h)
                cy += item_h
            rx += strip_w
            rw = max(0.0, rw - strip_w)
        else:
            # Lay out a horizontal strip on the top
            strip_h = row_sum / max(rw, 1e-6)
            cx = rx
            for orig_i, val in row_items:
                item_w = val / max(strip_h, 1e-6)
                out[orig_i] = (cx, ry, item_w, strip_h)
                cx += item_w
            ry += strip_h
            rh = max(0.0, rh - strip_h)

    return [out[i] for i in range(len(values))]


def _text_on_fill(fill_hex: str, palette: ThemePalette) -> str:
    light_txt = "#FFFFFF" if not palette.dark else palette.ink
    dark_txt = palette.ink if not palette.dark else palette.bg
    if contrast_ratio(light_txt, fill_hex) >= 3.2:
        return light_txt
    return dark_txt


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    groups: List[Dict[str, Any]] = spec["data"]
    if not groups:
        raise ValueError("nested_treemap requires non-empty 'data' list of {label, children}")

    title = spec.get("title", "Where the effort went")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "NESTED TREEMAP")
    prefix = spec.get("value_prefix", "")
    suffix = spec.get("value_suffix", "")
    unit_note = spec.get("unit_note", "AREA ∝ WEIGHT · HUE = PARENT GROUP · NESTED TWO-LEVEL HIERARCHY")

    group_totals: List[float] = []
    for g in groups:
        kids = g.get("children", [])
        tot = sum(max(0.0, float(c["value"])) for c in kids)
        group_totals.append(tot)
    grand_total = sum(group_totals) or 1.0

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "nested-treemap"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    pad = 8.0 if layout.mode == "slide" else 4.0
    x0 = layout.chart_x + pad
    y0 = layout.chart_y + pad
    w0 = layout.chart_w - 2 * pad
    h0 = layout.chart_h - 2 * pad

    canvas.add_comment(
        area,
        f"chart-plot-area: object={canvas.chart_id} | "
        f"{fmt(x0)},{fmt(y0)},{fmt(x0 + w0)},{fmt(y0 + h0)}",
    )

    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    parent_rects = _squarify(group_totals, x0, y0, w0, h0)
    outer_gap = 6.0 if layout.mode == "slide" else 4.0
    inner_gap = 3.5 if layout.mode == "slide" else 2.5
    header_h = 30.0 if layout.mode == "slide" else 24.0
    header_size = 13.0 if layout.mode == "slide" else 12.0
    leaf_name_size = 14.5 if layout.mode == "slide" else 12.0
    leaf_val_size = 13.0 if layout.mode == "slide" else 12.0

    for gi, g in enumerate(groups):
        px, py, pw, ph = parent_rects[gi]
        gx = px + outer_gap / 2.0
        gy = py + outer_gap / 2.0
        gw = max(0.0, pw - outer_gap)
        gh = max(0.0, ph - outer_gap)
        if gw < 10 or gh < 10:
            continue

        base_col = palette.series_color(gi)
        grp_node = canvas.add_group(marks_g, f"treemap-group-{gi+1}")

        # Subtle parent frame background
        frame_bg = mix_hex(base_col, palette.bg, 0.88)
        canvas.add_rect(grp_node, gx, gy, gw, gh, fill=frame_bg, rx=6.0)

        # Parent header text
        pct = int(round((group_totals[gi] / grand_total) * 100))
        hdr_txt = f"{g['label']} · {pct}%"
        if gw >= 90 and gh >= header_h + 24:
            canvas.add_text(
                labels_g,
                gx + 10.0,
                gy + header_h * 0.68,
                hdr_txt,
                font_size=header_size,
                font_weight=800,
                fill=base_col,
                letter_spacing=0.6,
            )
            inner_y = gy + header_h
            inner_h = max(0.0, gh - header_h - 4.0)
        else:
            inner_y = gy + 4.0
            inner_h = max(0.0, gh - 8.0)

        inner_x = gx + 4.0
        inner_w = max(0.0, gw - 8.0)

        kids = g.get("children", [])
        k_vals = [max(0.0, float(c["value"])) for c in kids]
        leaf_rects = _squarify(k_vals, inner_x, inner_y, inner_w, inner_h)
        max_k = max(k_vals) or 1.0

        for ki, child in enumerate(kids):
            lx, ly, lw, lh = leaf_rects[ki]
            cx = lx + inner_gap / 2.0
            cy = ly + inner_gap / 2.0
            cw = max(0.0, lw - inner_gap)
            ch = max(0.0, lh - inner_gap)
            if cw < 4 or ch < 4:
                continue

            # Slight lightness step within parent group so sibling tiles read crisply
            rel = 1.0 - (k_vals[ki] / max_k)
            tile_col = mix_hex(base_col, palette.bg, 0.04 + rel * 0.24)
            canvas.add_rect(grp_node, cx, cy, cw, ch, fill=tile_col, rx=4.0)

            txt_col = _text_on_fill(tile_col, palette)
            name = str(child["label"])
            val_s = format_number(k_vals[ki], prefix, suffix)

            if cw >= 78 and ch >= 46:
                canvas.add_text(
                    labels_g,
                    cx + 10.0,
                    cy + leaf_name_size + 8.0,
                    name,
                    font_size=leaf_name_size,
                    font_weight=700,
                    fill=txt_col,
                )
                canvas.add_text(
                    labels_g,
                    cx + 10.0,
                    cy + leaf_name_size + leaf_val_size + 16.0,
                    val_s,
                    font_size=leaf_val_size,
                    font_weight=600,
                    fill=txt_col,
                    fill_opacity=0.86,
                )
            elif cw >= 58 and ch >= 26:
                canvas.add_text(
                    labels_g,
                    cx + 8.0,
                    cy + 18.0,
                    name,
                    font_size=12.0,
                    font_weight=700,
                    fill=txt_col,
                )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
