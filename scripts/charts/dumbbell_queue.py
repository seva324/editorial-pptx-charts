#!/usr/bin/env python3
"""F12 · Dumbbell Queue — Before/after comparison with countable change beads.

Hollow dot = before, solid primary/accent dot = after, and beads strung along
the track between them encode the exact countable change (1 bead = 1 unit saved
or gained). Clean horizontal ledger tracks prevent any crossing slope lines.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

from palette import ThemePalette
from svg_builder import FrameLayout, SvgCanvas, estimate_text_width, fmt, format_number, rnd


def _choose_bead_unit(max_delta: float, max_beads: int, explicit_unit: float | None) -> float:
    if explicit_unit and explicit_unit > 0:
        return float(explicit_unit)
    if max_delta <= max_beads:
        return 1.0
    raw = max_delta / max_beads
    mag = 10 ** math.floor(math.log10(raw))
    for mult in (1, 2, 2.5, 5, 10):
        cand = mult * mag
        if max_delta / cand <= max_beads:
            return cand
    return 10 * mag


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    items: List[Dict[str, Any]] = spec["data"]
    if not items:
        raise ValueError("dumbbell_queue requires non-empty 'data' list")

    title = spec.get("title", "Before and after, bead by bead")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "DUMBBELL QUEUE")
    before_label = spec.get("before_label", "Before")
    after_label = spec.get("after_label", "After")
    left_axis_hint = spec.get("left_hint", "")
    right_axis_hint = spec.get("right_hint", "")
    prefix = spec.get("value_prefix", "")
    suffix = spec.get("value_suffix", "")
    unit_label = spec.get("unit_label", "")

    all_vals = [float(d["before"]) for d in items] + [float(d["after"]) for d in items]
    lo = float(spec.get("x_min", min(all_vals) * 0.85 if min(all_vals) > 0 else min(all_vals) * 1.1))
    hi = float(spec.get("x_max", max(all_vals) * 1.08))
    if hi <= lo:
        hi = lo + 1.0

    deltas = [abs(float(d["after"]) - float(d["before"])) for d in items]
    max_delta = max(deltas) or 1.0
    bead_unit = _choose_bead_unit(max_delta, 18 if layout.mode == "slide" else 12, spec.get("unit_value"))

    unit_note = spec.get("unit_note")
    if not unit_note:
        u_txt = format_number(bead_unit, prefix, suffix)
        if unit_label:
            u_txt = f"{u_txt} {unit_label}".strip()
        unit_note = f"HOLLOW = {before_label} · SOLID = {after_label} · ONE BEAD = {u_txt} CHANGE"

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "dumbbell-queue"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    n = len(items)
    lbl_size = 14.5 if layout.mode == "slide" else 12.0
    max_lbl_px = max(estimate_text_width(str(d["label"]), lbl_size) for d in items)
    left_rail = min(
        layout.chart_w * 0.30,
        max(120.0 if layout.mode == "slide" else 92.0, max_lbl_px + 26.0),
    )
    right_pad = 64.0 if layout.mode == "slide" else 42.0
    left_val_pad = 54.0 if layout.mode == "slide" else 38.0
    x_label_edge = layout.chart_x + left_rail
    x0 = x_label_edge + left_val_pad
    x1 = layout.chart_right - right_pad

    top_pad = 36.0 if layout.mode == "slide" else 28.0
    bot_pad = 38.0 if layout.mode == "slide" else 30.0
    row_h = (layout.chart_h - top_pad - bot_pad) / max(n, 1)

    def map_x(v: float) -> float:
        return x0 + ((v - lo) / (hi - lo)) * (x1 - x0)

    canvas.add_comment(
        area,
        f"chart-plot-area: object={canvas.chart_id} | "
        f"{fmt(x0)},{fmt(layout.chart_y + top_pad)},{fmt(x1)},{fmt(layout.chart_bottom - bot_pad)}",
    )

    grid_g = canvas.add_group(area, "chart-grid")
    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    lbl_size = 14.5 if layout.mode == "slide" else 12.0
    val_b_size = 13.5 if layout.mode == "slide" else 12.0
    val_a_size = 16.0 if layout.mode == "slide" else 13.0
    dot_r = 8.0 if layout.mode == "slide" else 5.8
    bead_r_base = 3.2 if layout.mode == "slide" else 2.2

    before_col = palette.c2
    after_col = palette.c1
    bead_col = palette.c3 if len(palette.colors) >= 3 else palette.c2

    for i, item in enumerate(items):
        name = str(item["label"])
        vb = float(item["before"])
        va = float(item["after"])
        cy = layout.chart_y + top_pad + (i + 0.5) * row_h
        xb = map_x(vb)
        xa = map_x(va)

        # Row label & subtle ledger track
        canvas.add_text(
            labels_g,
            x_label_edge - 14.0,
            cy + lbl_size * 0.32,
            name,
            font_size=lbl_size,
            font_weight=600,
            fill=palette.label,
            text_anchor="end",
            letter_spacing=0.6,
        )
        canvas.add_line(grid_g, x_label_edge, cy, x1 + 6, cy, stroke=palette.grid, stroke_width=1.1)

        row_g = canvas.add_group(marks_g, f"dumbbell-{i+1}")
        # Connecting colored track segment between before & after
        canvas.add_line(
            row_g,
            min(xa, xb),
            cy,
            max(xa, xb),
            cy,
            stroke=bead_col,
            stroke_width=1.6,
            stroke_opacity=0.35,
        )

        # Countable beads strung between dots
        n_beads = max(0, int(round(abs(va - vb) / bead_unit)))
        span = abs(xa - xb)
        inner_margin = dot_r + 5.0
        if n_beads > 0 and span > inner_margin * 2:
            left_x = min(xa, xb) + inner_margin
            right_x = max(xa, xb) - inner_margin
            for k in range(n_beads):
                t = (k + 0.5) / n_beads
                bx = left_x + t * (right_x - left_x)
                by = cy + (rnd(k + 1, i + 3) - 0.5) * (4.0 if layout.mode == "slide" else 2.6)
                br = bead_r_base * (0.8 + rnd(k + 2, i + 4) * 0.45)
                canvas.add_circle(row_g, bx, by, br, fill=bead_col, fill_opacity=0.86)

        # Before dot (hollow)
        canvas.add_circle(
            row_g,
            xb,
            cy,
            dot_r,
            fill=palette.bg,
            stroke=before_col,
            stroke_width=2.6 if layout.mode == "slide" else 2.0,
        )
        # After dot (solid)
        canvas.add_circle(row_g, xa, cy, dot_r + 0.6, fill=after_col)

        # Smart non-overlapping value labels
        if xa <= xb:
            # Moved left (e.g. faster / lower)
            canvas.add_text(
                labels_g,
                xb + dot_r + 8.0,
                cy + val_b_size * 0.34,
                format_number(vb, prefix, suffix),
                font_size=val_b_size,
                font_weight=600,
                fill=before_col,
                text_anchor="start",
            )
            canvas.add_text(
                labels_g,
                xa - dot_r - 8.0,
                cy + val_a_size * 0.34,
                format_number(va, prefix, suffix),
                font_size=val_a_size,
                font_weight=800,
                fill=after_col,
                text_anchor="end",
            )
        else:
            # Moved right (e.g. growth / higher)
            canvas.add_text(
                labels_g,
                xb - dot_r - 8.0,
                cy + val_b_size * 0.34,
                format_number(vb, prefix, suffix),
                font_size=val_b_size,
                font_weight=600,
                fill=before_col,
                text_anchor="end",
            )
            canvas.add_text(
                labels_g,
                xa + dot_r + 8.0,
                cy + val_a_size * 0.34,
                format_number(va, prefix, suffix),
                font_size=val_a_size,
                font_weight=800,
                fill=after_col,
                text_anchor="start",
            )

    # Bottom directional hints
    hint_y = layout.chart_bottom - 8.0
    if left_axis_hint:
        canvas.add_text(labels_g, x0, hint_y, left_axis_hint, font_size=12.0, font_weight=600, fill=palette.faint, letter_spacing=0.8)
    if right_axis_hint:
        canvas.add_text(labels_g, x1, hint_y, right_axis_hint, font_size=12.0, font_weight=600, fill=palette.faint, text_anchor="end", letter_spacing=0.8)

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
