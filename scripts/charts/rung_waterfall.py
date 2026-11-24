#!/usr/bin/env python3
"""F9 · Rung Waterfall — Step-by-step countable rung bridge / P&L waterfall.

Totals (start / end / subtotal) and positive additions use solid rungs;
negative deductions use dashed hollow-style rungs in the secondary/accent color;
dashed horizontal hand-off hairlines connect consecutive columns.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

from palette import ThemePalette
from svg_builder import FrameLayout, SvgCanvas, fmt, format_number, rnd


def _choose_unit(max_val: float, max_rungs: int, explicit_unit: float | None) -> float:
    if explicit_unit and explicit_unit > 0:
        return float(explicit_unit)
    if max_val <= max_rungs:
        return 1.0
    raw = max_val / max_rungs
    mag = 10 ** math.floor(math.log10(raw))
    for mult in (1, 2, 2.5, 5, 10):
        cand = mult * mag
        if max_val / cand <= max_rungs:
            return cand
    return 10 * mag


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    items: List[Dict[str, Any]] = spec["data"]
    if len(items) < 2:
        raise ValueError("rung_waterfall requires at least 2 steps in 'data'")

    title = spec.get("title", "From gross to net, step by step")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "RUNG WATERFALL")
    prefix = spec.get("value_prefix", "")
    suffix = spec.get("value_suffix", "")
    unit_label = spec.get("unit_label", "")

    # Compute running bridge intervals: (name, value, lo, hi, kind)
    # kind in {"start", "total", "add", "sub"}
    rows: List[Tuple[str, float, float, float, str]] = []
    running = 0.0
    for idx, d in enumerate(items):
        name = str(d["label"])
        kind = str(d.get("kind", "")).lower()
        v = float(d.get("value", 0.0))
        if kind == "total" or (not kind and idx == len(items) - 1 and d.get("is_total")):
            tot = v if "value" in d and d["value"] is not None else running
            rows.append((name, tot, 0.0, tot, "total"))
            running = tot
        elif kind == "start" or (idx == 0 and kind not in ("add", "sub")):
            rows.append((name, v, 0.0, v, "start"))
            running = v
        else:
            nxt = running + v
            lo, hi = min(running, nxt), max(running, nxt)
            rows.append((name, v, lo, hi, "add" if v >= 0 else "sub"))
            running = nxt

    max_hi = max(r[3] for r in rows) or 1.0
    max_rungs_cap = 40 if layout.mode == "slide" else 28
    unit_val = _choose_unit(max_hi, max_rungs_cap, spec.get("unit_value"))
    max_units = max(1, int(math.ceil(max_hi / unit_val)))

    unit_note = spec.get("unit_note")
    if not unit_note:
        u_txt = format_number(unit_val, prefix, suffix)
        if unit_label:
            u_txt = f"{u_txt} {unit_label}".strip()
        unit_note = f"SOLID RUNGS ADD / TOTAL · DASHED RUNGS DEDUCT · ONE RUNG = {u_txt}"

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "rung-waterfall"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    n = len(rows)
    top_pad = 44.0 if layout.mode == "slide" else 34.0
    bot_pad = 46.0 if layout.mode == "slide" else 36.0
    side_pad = max(40.0, layout.chart_w * 0.06)

    x_left = layout.chart_x + side_pad
    x_right = layout.chart_right - side_pad
    base_y = layout.chart_bottom - bot_pad
    avail_h = max(80.0, base_y - (layout.chart_y + top_pad))
    step = min(12.0 if layout.mode == "slide" else 8.5, avail_h / max(max_units, 1))

    slot_w = (x_right - x_left) / max(n, 1)
    half_w = min(slot_w * 0.28, 42.0 if layout.mode == "slide" else 24.0)
    stroke_w = max(1.8, min(3.0, step * 0.36))

    def y_of_unit(u: float) -> float:
        return base_y - u * step

    grid_g = canvas.add_group(area, "chart-grid")
    canvas.add_line(
        grid_g,
        layout.chart_x + 8,
        base_y + step * 0.65,
        layout.chart_right - 8,
        base_y + step * 0.65,
        stroke=palette.grid,
        stroke_width=1.4,
    )
    canvas.add_comment(
        area,
        f"chart-plot-area: object={canvas.chart_id} | "
        f"{fmt(x_left)},{fmt(layout.chart_y + top_pad)},{fmt(x_right)},{fmt(base_y)}",
    )

    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    start_col = palette.c1
    add_col = palette.c2
    sub_col = palette.c3 if len(palette.colors) >= 3 else palette.c2
    total_col = palette.c1

    val_size = 16.5 if layout.mode == "slide" else 13.0
    cat_size = 13.5 if layout.mode == "slide" else 12.0

    for i, (name, v, lo, hi, kind) in enumerate(rows):
        cx = x_left + (i + 0.5) * slot_w
        u_lo = int(round(lo / unit_val))
        u_hi = int(round(hi / unit_val))
        count = max(1, u_hi - u_lo) if abs(hi - lo) > 1e-6 else 0

        if kind == "sub":
            col = sub_col
        elif kind == "add":
            col = add_col
        elif kind == "total":
            col = total_col
        else:
            col = start_col

        col_g = canvas.add_group(marks_g, f"step-{i+1}")
        for k in range(count):
            y = y_of_unit(u_lo + k)
            w = half_w + (rnd(k + 1, i + 2) - 0.5) * (half_w * 0.14)
            if kind == "sub":
                canvas.add_line(
                    col_g,
                    cx - w,
                    y,
                    cx + w,
                    y,
                    stroke=col,
                    stroke_width=stroke_w,
                    stroke_opacity=0.82,
                    stroke_dasharray="5,4" if layout.mode == "slide" else "3,3",
                )
            else:
                op = 0.84 + rnd(k + 2, i + 4) * 0.16
                canvas.add_line(
                    col_g,
                    cx - w,
                    y,
                    cx + w,
                    y,
                    stroke=col,
                    stroke_width=stroke_w,
                    stroke_opacity=op,
                    stroke_linecap="round",
                )

        # Horizontal dashed connector to next column
        if i < n - 1:
            nx = x_left + (i + 1.5) * slot_w
            end_lvl = hi if kind in ("start", "total", "add") else lo
            hy = y_of_unit(end_lvl / unit_val)
            canvas.add_line(
                grid_g,
                cx + half_w + 6.0,
                hy,
                nx - half_w - 6.0,
                hy,
                stroke=palette.floor,
                stroke_width=1.2,
                stroke_dasharray="3,4",
            )

        # Value label above bar
        top_y = y_of_unit(u_hi)
        if kind == "sub":
            v_str = "−" + format_number(abs(v), prefix, suffix)
        elif kind == "add":
            v_str = "+" + format_number(abs(v), prefix, suffix)
        else:
            v_str = format_number(v, prefix, suffix)

        canvas.add_text(
            labels_g,
            cx,
            top_y - (13.0 if layout.mode == "slide" else 10.0),
            v_str,
            font_size=val_size,
            font_weight=800 if kind in ("start", "total") else 700,
            fill=col if kind in ("sub", "add") else palette.ink,
            text_anchor="middle",
        )
        canvas.add_text(
            labels_g,
            cx,
            base_y + (28.0 if layout.mode == "slide" else 22.0),
            name,
            font_size=cat_size,
            font_weight=700 if kind in ("start", "total") else 600,
            fill=palette.ink if kind in ("start", "total") else palette.label,
            text_anchor="middle",
            letter_spacing=0.6,
        )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
