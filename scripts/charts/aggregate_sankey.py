#!/usr/bin/env python3
"""G22 · Aggregate Sankey — Two-column aggregate flow ribbons.

Sources on the left pour into targets on the right via translucent cubic-Bézier
ribbons whose thickness is strictly proportional to volume. Ribbons inherit
their source color from the 2-3 custom theme palette so crossing streams remain
clear and easy to trace in 3 seconds.
"""

from __future__ import annotations

from typing import Any, Dict, List

from palette import ThemePalette
from svg_builder import FrameLayout, SvgCanvas, estimate_text_width, fmt, format_number


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    sources: List[Dict[str, Any]] = spec["sources"]
    targets: List[str] = [str(t) for t in spec["targets"]]
    if not sources or not targets:
        raise ValueError("aggregate_sankey requires non-empty 'sources' and 'targets'")

    title = spec.get("title", "Channels pouring into plans")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "AGGREGATE SANKEY")
    prefix = spec.get("value_prefix", "")
    suffix = spec.get("value_suffix", "")
    unit_note = spec.get(
        "unit_note",
        "RIBBON WIDTH ∝ VOLUME · COLOR = SOURCE CHANNEL · TWO-STAGE AGGREGATE FLOW",
    )

    n_src = len(sources)
    n_dst = len(targets)
    src_totals = [sum(max(0.0, float(v)) for v in s["flows"]) for s in sources]
    dst_totals = [
        sum(max(0.0, float(sources[i]["flows"][j])) for i in range(n_src))
        for j in range(n_dst)
    ]
    grand_total = sum(src_totals) or 1.0

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "aggregate-sankey"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    lbl_size = 14.5 if layout.mode == "slide" else 12.0
    val_size = 16.5 if layout.mode == "slide" else 13.0

    max_src_px = max(
        estimate_text_width(f"{s['label']} · {format_number(src_totals[i], prefix, suffix)}", lbl_size)
        for i, s in enumerate(sources)
    )
    max_dst_px = max(
        max(estimate_text_width(t, lbl_size), estimate_text_width(format_number(dst_totals[j], prefix, suffix), val_size))
        for j, t in enumerate(targets)
    )

    left_rail = min(layout.chart_w * 0.28, max(130.0 if layout.mode == "slide" else 96.0, max_src_px + 28.0))
    right_rail = min(layout.chart_w * 0.24, max(110.0 if layout.mode == "slide" else 84.0, max_dst_px + 28.0))
    bar_w = 16.0 if layout.mode == "slide" else 11.0

    x_left_edge = layout.chart_x + left_rail
    x_right_edge = layout.chart_right - right_rail
    xl = x_left_edge + bar_w
    xr = x_right_edge - bar_w
    mid_x = (xl + xr) / 2.0

    top_pad = 18.0 if layout.mode == "slide" else 12.0
    bot_pad = 18.0 if layout.mode == "slide" else 12.0
    avail_h = max(100.0, layout.chart_h - top_pad - bot_pad)

    gap_l = 16.0 if layout.mode == "slide" else 10.0
    gap_r = 28.0 if layout.mode == "slide" else 18.0
    max_gap_total = max(gap_l * max(n_src - 1, 0), gap_r * max(n_dst - 1, 0))
    scale = max(0.2, (avail_h - max_gap_total) / grand_total)

    src_h_tot = grand_total * scale + gap_l * max(n_src - 1, 0)
    dst_h_tot = grand_total * scale + gap_r * max(n_dst - 1, 0)
    y_start_l = layout.chart_y + top_pad + (avail_h - src_h_tot) / 2.0
    y_start_r = layout.chart_y + top_pad + (avail_h - dst_h_tot) / 2.0

    sy: List[float] = []
    cur = y_start_l
    for t in src_totals:
        sy.append(cur)
        cur += t * scale + gap_l

    dy: List[float] = []
    cur = y_start_r
    for t in dst_totals:
        dy.append(cur)
        cur += t * scale + gap_r

    ribbons_g = canvas.add_group(area, "chart-ribbons")
    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    # 1. Translucent Bézier ribbons
    sy_cur = list(sy)
    dy_cur = list(dy)
    for i, s in enumerate(sources):
        col = palette.series_color(i)
        for j in range(n_dst):
            v = max(0.0, float(s["flows"][j]))
            if v <= 0:
                continue
            h = v * scale
            sa, sb = sy_cur[i], sy_cur[i] + h
            da, db = dy_cur[j], dy_cur[j] + h
            sy_cur[i] = sb
            dy_cur[j] = db
            d = (
                f"M {fmt(xl)} {fmt(sa)} "
                f"C {fmt(mid_x)} {fmt(sa)} {fmt(mid_x)} {fmt(da)} {fmt(xr)} {fmt(da)} "
                f"L {fmt(xr)} {fmt(db)} "
                f"C {fmt(mid_x)} {fmt(db)} {fmt(mid_x)} {fmt(sb)} {fmt(xl)} {fmt(sb)} Z"
            )
            canvas.add_path(ribbons_g, d, fill=col, fill_opacity=0.44)

    # 2. Left source capsule bars + labels
    for i, s in enumerate(sources):
        col = palette.series_color(i)
        bh = max(4.0, src_totals[i] * scale)
        rx = min(bar_w * 0.42, bh * 0.45)
        canvas.add_rect(marks_g, x_left_edge, sy[i], bar_w, bh, fill=col, rx=rx)
        canvas.add_text(
            labels_g,
            x_left_edge - 14.0,
            sy[i] + bh / 2.0 + lbl_size * 0.34,
            f"{s['label']} · {format_number(src_totals[i], prefix, suffix)}",
            font_size=lbl_size,
            font_weight=700,
            fill=col if i < 3 else palette.label,
            text_anchor="end",
        )

    # 3. Right target capsule bars + stacked name/value labels
    for j, tname in enumerate(targets):
        bh = max(4.0, dst_totals[j] * scale)
        rx = min(bar_w * 0.42, bh * 0.45)
        canvas.add_rect(marks_g, xr, dy[j], bar_w, bh, fill=palette.ink, fill_opacity=0.88, rx=rx)
        mid_y = dy[j] + bh / 2.0
        canvas.add_text(
            labels_g,
            x_right_edge + 14.0,
            mid_y - 3.0,
            tname,
            font_size=lbl_size,
            font_weight=700,
            fill=palette.label,
        )
        canvas.add_text(
            labels_g,
            x_right_edge + 14.0,
            mid_y + val_size + 2.0,
            format_number(dst_totals[j], prefix, suffix),
            font_size=val_size,
            font_weight=800,
            fill=palette.ink,
        )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
