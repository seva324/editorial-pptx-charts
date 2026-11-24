#!/usr/bin/env python3
"""L17 · Calendar Heat — Full-year 52 weeks × 7 days dot-area contribution wall.

Every day of the year is present: silent days show a tiny quiet dot, active
days scale by area (`sqrt(value)`) across the theme ordinal ramp, months mark
the top rim, and the busiest day gets a dashed accent ring + curved editorial
marginalia callout.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

from palette import ThemePalette
from svg_builder import FrameLayout, SvgCanvas, fmt, format_number


MONTHS_DEFAULT = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
DAYS_LABELS = [(0, "MON"), (2, "WED"), (4, "FRI"), (6, "SUN")]


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    # Accept either 52x7 `weeks` matrix or flat `days` list (364-366 values)
    if "weeks" in spec:
        weeks: List[List[float]] = spec["weeks"]
    elif "days" in spec:
        flat = [max(0.0, float(v)) for v in spec["days"]]
        weeks = []
        for w in range(0, len(flat), 7):
            chunk = flat[w : w + 7]
            while len(chunk) < 7:
                chunk.append(0.0)
            weeks.append(chunk)
    else:
        raise ValueError("calendar_heat requires 'weeks' (52x7) or 'days' (364+) in spec")

    n_weeks = len(weeks)
    title = spec.get("title", "A year of activity, day by day")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "CALENDAR HEAT")
    months: List[str] = spec.get("months", MONTHS_DEFAULT)
    peak_note_tpl = spec.get("peak_note", "busiest day — {value}")
    prefix = spec.get("value_prefix", "")
    suffix = spec.get("value_suffix", "")
    unit_note = spec.get(
        "unit_note",
        "ONE DOT = ONE DAY · DOT AREA ∝ COUNT · TINY DOT = QUIET DAY · DASHED RING = PEAK",
    )

    max_val = 0.0
    pw, pd = 0, 0
    for w in range(n_weeks):
        for d in range(min(7, len(weeks[w]))):
            v = max(0.0, float(weeks[w][d]))
            if v > max_val:
                max_val = v
                pw, pd = w, d

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "calendar-heat"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    left_rail = 64.0 if layout.mode == "slide" else 48.0
    right_pad = 18.0 if layout.mode == "slide" else 12.0
    avail_w = layout.chart_w - left_rail - right_pad
    pitch = min(avail_w / max(n_weeks - 1, 1), 21.5 if layout.mode == "slide" else 11.5)
    grid_w = pitch * max(n_weeks - 1, 1)
    grid_h = pitch * 6.0

    x0 = layout.chart_x + left_rail + (avail_w - grid_w) / 2.0
    # Leave space above for month labels and below for marginalia callout
    y0 = layout.chart_y + (layout.chart_h - grid_h) * 0.42
    max_r = pitch * 0.43

    grid_g = canvas.add_group(area, "chart-grid")
    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    lbl_size = 12.5 if layout.mode == "slide" else 12.0

    # Weekday labels on left
    for d_idx, d_lbl in DAYS_LABELS:
        canvas.add_text(
            labels_g,
            x0 - 16.0,
            y0 + d_idx * pitch + lbl_size * 0.34,
            d_lbl,
            font_size=lbl_size,
            font_weight=700,
            fill=palette.muted,
            text_anchor="end",
            letter_spacing=0.6,
        )

    # Month ticks along top rim
    n_months = len(months)
    month_step = 1 if layout.mode == "slide" else 2
    for m_idx in range(0, n_months, month_step):
        mx = x0 + int(round(m_idx * n_weeks / max(n_months, 1))) * pitch
        canvas.add_text(
            labels_g,
            mx,
            y0 - (24.0 if layout.mode == "slide" else 18.0),
            str(months[m_idx]),
            font_size=lbl_size,
            font_weight=700,
            fill=palette.muted,
            letter_spacing=0.8,
        )
        canvas.add_line(grid_g, mx, y0 - 16.0, mx, y0 - 8.0, stroke=palette.floor, stroke_width=1.1)

    accent_col = palette.c3 if len(palette.colors) >= 3 else palette.c2

    # 52 x 7 day dots
    for w in range(n_weeks):
        for d in range(min(7, len(weeks[w]))):
            cx = x0 + w * pitch
            cy = y0 + d * pitch
            v = max(0.0, float(weeks[w][d]))
            if v <= 0 or max_val <= 0:
                canvas.add_circle(marks_g, cx, cy, 1.5 if layout.mode == "slide" else 1.1, fill=palette.quiet)
                continue
            ratio = v / max_val
            rad = max(2.2, math.sqrt(ratio) * max_r)
            is_peak = w == pw and d == pd
            col = accent_col if is_peak else palette.ramp_color(ratio * 0.85)
            canvas.add_circle(marks_g, cx, cy, rad, fill=col)

    # Peak dashed ring + curved marginalia leader below the grid
    px = x0 + pw * pitch
    py = y0 + pd * pitch
    pr = max(2.2, max_r)
    canvas.add_circle(
        marks_g,
        px,
        py,
        pr + (4.5 if layout.mode == "slide" else 3.2),
        fill="none",
        stroke=accent_col,
        stroke_width=1.8 if layout.mode == "slide" else 1.3,
        stroke_dasharray="3,3",
    )

    note_y = y0 + grid_h + (56.0 if layout.mode == "slide" else 42.0)
    peak_txt = format_number(max_val, prefix, suffix)
    callout_text = peak_note_tpl.format(value=peak_txt)
    go_right = pw < n_weeks * 0.62
    dx_dir = 1.0 if go_right else -1.0
    end_x = px + dx_dir * (76.0 if layout.mode == "slide" else 44.0)

    canvas.add_path(
        labels_g,
        f"M {fmt(px)} {fmt(py + pr + 6.0)} C {fmt(px)} {fmt(note_y)} {fmt(px + dx_dir * 32.0)} {fmt(note_y)} {fmt(end_x)} {fmt(note_y)}",
        fill="none",
        stroke=accent_col,
        stroke_width=1.3,
        stroke_opacity=0.85,
    )
    canvas.add_text(
        labels_g,
        end_x + dx_dir * 10.0,
        note_y + 4.5,
        callout_text,
        font_size=13.5 if layout.mode == "slide" else 12.0,
        font_weight=700,
        font_style="italic",
        fill=accent_col,
        text_anchor="start" if go_right else "end",
    )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
