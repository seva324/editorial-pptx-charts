#!/usr/bin/env python3
"""L13 · Hourglass Stream — Poured barcode funnel with trickling Bézier threads.

Each stage is a centered horizontal barcode strip whose width is proportional
to headcount/volume. Delicate cubic Bézier threads pour down from one stage
to the next, conversion percentages sit cleanly in the left margin, and stage
names + bold figures tie to the right edge via hairline leaders.
"""

from __future__ import annotations

from typing import Any, Dict, List

from palette import ThemePalette, mix_hex
from svg_builder import FrameLayout, SvgCanvas, fmt, format_number, rnd


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    stages: List[Dict[str, Any]] = spec["data"]
    if len(stages) < 2:
        raise ValueError("hourglass_stream requires at least 2 stages in 'data'")

    title = spec.get("title", "The funnel, poured")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "HOURGLASS STREAM")
    prefix = spec.get("value_prefix", "")
    suffix = spec.get("value_suffix", "")
    conv_caption = spec.get("conversion_caption", "GET THROUGH")
    unit_note = spec.get(
        "unit_note",
        "STRIP WIDTH ∝ VOLUME AT STAGE · LEFT = STEP CONVERSION · FINAL STAGE HIGHLIGHTED",
    )

    counts = [max(0.0, float(s["value"])) for s in stages]
    max_count = max(counts) or 1.0

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "hourglass-stream"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    n = len(stages)
    left_margin = 160.0 if layout.mode == "slide" else 104.0
    right_margin = 230.0 if layout.mode == "slide" else 148.0
    max_strip_w = max(180.0, layout.chart_w - left_margin - right_margin)
    cx = layout.chart_x + left_margin + max_strip_w / 2.0
    right_label_x = layout.chart_x + left_margin + max_strip_w + (34.0 if layout.mode == "slide" else 18.0)

    top_pad = 28.0 if layout.mode == "slide" else 22.0
    bot_pad = 26.0 if layout.mode == "slide" else 20.0
    row_step = (layout.chart_h - top_pad - bot_pad) / max(n - 1, 1)

    def stage_y(k: int) -> float:
        return layout.chart_y + top_pad + k * row_step

    def half_w(val: float) -> float:
        return max(12.0, (val / max_count) * (max_strip_w / 2.0))

    threads_g = canvas.add_group(area, "chart-threads")
    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    accent_col = palette.c3 if len(palette.colors) >= 3 else palette.c2
    strip_h = 12.0 if layout.mode == "slide" else 8.5
    max_ticks_top = 86 if layout.mode == "slide" else 56
    threads_per_gap = 28 if layout.mode == "slide" else 20

    # 1. Draw trickling Bézier streams first (behind strips)
    for k in range(n - 1):
        y1 = stage_y(k) + strip_h + 2.0
        y2 = stage_y(k + 1) - strip_h - 2.0
        hw1 = half_w(counts[k]) * 0.94
        hw2 = half_w(counts[k + 1]) * 0.94
        t_col = mix_hex(palette.c1, palette.c2, k / max(n - 2, 1)) if len(palette.colors) >= 2 else palette.c1
        mid_span = (y2 - y1) * 0.45

        flow_g = canvas.add_group(threads_g, f"flow-{k+1}")
        for t in range(threads_per_gap):
            xt = cx + (rnd(t + 1, k * 7 + 1) - 0.5) * 2.0 * hw1
            xb = cx + (rnd(t + 3, k * 7 + 5) - 0.5) * 2.0 * hw2
            d = f"M {fmt(xt)} {fmt(y1)} C {fmt(xt)} {fmt(y1 + mid_span)} {fmt(xb)} {fmt(y2 - mid_span)} {fmt(xb)} {fmt(y2)}"
            canvas.add_path(
                flow_g,
                d,
                fill="none",
                stroke=t_col,
                stroke_width=1.0 if layout.mode == "slide" else 0.8,
                stroke_opacity=0.28,
            )

        # Left margin conversion rate
        pct = int(round((counts[k + 1] / counts[k]) * 100)) if counts[k] > 0 else 0
        mid_y = (stage_y(k) + stage_y(k + 1)) / 2.0
        canvas.add_text(
            labels_g,
            layout.chart_x + 12.0,
            mid_y + 2.0,
            f"{pct}%",
            font_size=18.0 if layout.mode == "slide" else 14.0,
            font_weight=800,
            fill=palette.c2 if len(palette.colors) >= 2 else palette.ink,
        )
        canvas.add_text(
            labels_g,
            layout.chart_x + 12.0,
            mid_y + (20.0 if layout.mode == "slide" else 16.0),
            conv_caption,
            font_size=12.0,
            font_weight=600,
            fill=palette.faint,
            letter_spacing=0.8,
        )

    # 2. Draw barcode strips & right-side labels
    stage_name_size = 13.5 if layout.mode == "slide" else 12.0
    stage_val_size = 18.0 if layout.mode == "slide" else 14.0

    for k, st in enumerate(stages):
        y = stage_y(k)
        c = counts[k]
        hw = half_w(c)
        is_final = k == n - 1
        col = accent_col if is_final else mix_hex(palette.c1, palette.c2, (k / max(n - 2, 1)) * 0.6)

        strip_g = canvas.add_group(marks_g, f"stage-{k+1}")
        n_ticks = max(4, int(round((c / max_count) * max_ticks_top)))
        for t in range(n_ticks):
            tx = cx - hw + ((t + 0.5) / n_ticks) * (2.0 * hw) + (rnd(t + 1, k + 3) - 0.5) * 3.0
            op = 0.72 + rnd(t + 2, k + 5) * 0.28
            canvas.add_line(
                strip_g,
                tx,
                y - strip_h,
                tx,
                y + strip_h,
                stroke=col,
                stroke_width=1.8 if layout.mode == "slide" else 1.3,
                stroke_opacity=op,
                stroke_linecap="round",
            )

        # Hairline leader to right stage label
        canvas.add_line(
            labels_g,
            cx + hw + 12.0,
            y,
            right_label_x - 12.0,
            y,
            stroke=palette.grid,
            stroke_width=1.2,
        )
        canvas.add_text(
            labels_g,
            right_label_x,
            y - (3.0 if layout.mode == "slide" else 2.0),
            str(st["label"]),
            font_size=stage_name_size,
            font_weight=700,
            fill=col if is_final else palette.label,
            letter_spacing=0.8,
        )
        canvas.add_text(
            labels_g,
            right_label_x,
            y + (18.0 if layout.mode == "slide" else 14.0),
            format_number(c, prefix, suffix),
            font_size=stage_val_size,
            font_weight=800,
            fill=col if is_final else palette.ink,
        )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
