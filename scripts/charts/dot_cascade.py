#!/usr/bin/env python3
"""L2 · Dot Cascade — Diagonal ascending unit-dot stacked ranking chart.

One of Lieflat's signature Lupi Editorial forms: categories climb a subtle
dotted diagonal baseline, each stacking countable unit dots topped by a bold
terminal bead and number. Works beautifully on BOTH dark cards (`dark: true`)
and light slides.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

from palette import ThemePalette, mix_hex
from svg_builder import FrameLayout, SvgCanvas, fmt, format_number


def _choose_unit(max_val: float, max_dots: int, explicit_unit: float | None) -> float:
    if explicit_unit and explicit_unit > 0:
        return float(explicit_unit)
    if max_val <= max_dots:
        return 1.0
    raw = max_val / max_dots
    mag = 10 ** math.floor(math.log10(raw))
    for mult in (1, 2, 2.5, 5, 10):
        cand = mult * mag
        if max_val / cand <= max_dots:
            return cand
    return 10 * mag


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    items: List[Dict[str, Any]] = list(spec["data"])
    if not items:
        raise ValueError("dot_cascade requires non-empty 'data' list")

    # Sort ascending by default so the cascade climbs naturally left-to-right
    if spec.get("sort_ascending", True):
        items.sort(key=lambda d: float(d["value"]))

    title = spec.get("title", "Stacked and ranked")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "DOT CASCADE")
    prefix = spec.get("value_prefix", "")
    suffix = spec.get("value_suffix", "")
    unit_label = spec.get("unit_label", "")

    vals = [max(0.0, float(d["value"])) for d in items]
    max_val = max(vals) or 1.0
    max_dots_cap = 16 if layout.mode == "slide" else 13
    unit_val = _choose_unit(max_val, max_dots_cap, spec.get("unit_value"))
    dot_counts = [max(1, int(math.ceil(v / unit_val))) if v > 0 else 0 for v in vals]
    max_dots = max(dot_counts) or 1

    unit_note = spec.get("unit_note")
    if not unit_note:
        u_txt = format_number(unit_val, prefix, suffix)
        if unit_label:
            u_txt = f"{u_txt} {unit_label}".strip()
        unit_note = f"ONE DOT = {u_txt} · SORTED ASCENDING · ACCENT = PEAK"

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "dot-cascade"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    n = len(items)
    pad_l = 44.0 if layout.mode == "slide" else 28.0
    pad_r = 44.0 if layout.mode == "slide" else 28.0
    pad_t = 44.0 if layout.mode == "slide" else 34.0
    pad_b = 96.0 if layout.mode == "slide" else 76.0  # room for vertical rotated category labels

    x0 = layout.chart_x + pad_l
    x1 = layout.chart_right - pad_r
    base_low = layout.chart_bottom - pad_b
    rise = min(layout.chart_h * 0.24, 115.0 if layout.mode == "slide" else 68.0)
    base_high = base_low - rise

    def col_x(i: int) -> float:
        return x0 + (i / max(n - 1, 1)) * (x1 - x0) if n > 1 else (x0 + x1) / 2.0

    def base_y(i: int) -> float:
        return base_low - (i / max(n - 1, 1)) * (base_low - base_high) if n > 1 else base_low

    avail_stack = max(60.0, (base_high - (layout.chart_y + pad_t)))
    dot_step = min(17.0 if layout.mode == "slide" else 12.5, avail_stack / max(max_dots, 1))
    small_r = min(dot_step * 0.30, 4.2 if layout.mode == "slide" else 3.0)
    top_r = min(dot_step * 0.50, 7.6 if layout.mode == "slide" else 5.4)

    grid_g = canvas.add_group(area, "chart-grid")
    # Dotted diagonal baseline
    canvas.add_line(
        grid_g,
        col_x(0) - 16,
        base_y(0) + 8,
        col_x(n - 1) + 16,
        base_y(n - 1) + 8,
        stroke=palette.floor,
        stroke_width=1.6,
        stroke_dasharray="3,5",
    )

    canvas.add_comment(
        area,
        f"chart-plot-area: object={canvas.chart_id} | "
        f"{fmt(x0)},{fmt(layout.chart_y + pad_t)},{fmt(x1)},{fmt(base_low)}",
    )

    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    hero_idx = vals.index(max(vals))
    accent_col = palette.c3 if len(palette.colors) >= 3 else palette.c2
    val_size = 14.5 if layout.mode == "slide" else 12.0
    cat_size = 12.5 if layout.mode == "slide" else 12.0

    for i, item in enumerate(items):
        name = str(item["label"])
        v = vals[i]
        cnt = dot_counts[i]
        bx = col_x(i)
        by = base_y(i)
        is_hero = i == hero_idx

        t = i / max(n - 1, 1)
        if is_hero:
            top_col = accent_col
            body_col = mix_hex(accent_col, palette.bg, 0.32)
        else:
            top_col = palette.ramp5[min(3, int(t * 3.8))] if palette.dark else mix_hex(palette.c2, palette.c1, t)
            body_col = mix_hex(top_col, palette.bg, 0.36)

        col_g = canvas.add_group(marks_g, f"cascade-{i+1}")
        first_y = by - 14.0
        for k in range(max(0, cnt - 1)):
            cy = first_y - k * dot_step
            canvas.add_circle(col_g, bx, cy, small_r, fill=body_col, fill_opacity=0.88)

        top_y = first_y - max(0, cnt - 1) * dot_step
        canvas.add_circle(col_g, bx, top_y, top_r, fill=top_col)

        # Value label above top dot
        canvas.add_text(
            labels_g,
            bx,
            top_y - top_r - (9.0 if layout.mode == "slide" else 7.0),
            format_number(v, prefix, suffix),
            font_size=val_size,
            font_weight=800 if is_hero else 700,
            fill=accent_col if is_hero else palette.ink,
            text_anchor="middle",
        )

        # Rotated category label below diagonal baseline
        ly = by + 22.0
        canvas.add_text(
            labels_g,
            bx + cat_size * 0.32,
            ly,
            name,
            font_size=cat_size,
            font_weight=700 if is_hero else 600,
            fill=palette.ink if is_hero else palette.muted,
            text_anchor="end",
            rotate=(-90.0, bx + cat_size * 0.32, ly),
        )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
