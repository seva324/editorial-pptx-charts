#!/usr/bin/env python3
"""F16 · Stream Ribbon — Silhouette-centered continuous-time Streamgraph.

Shows 2-5 series trading share over continuous time while revealing total
volume through overall river thickness. Ribbons are separated by crisp paper
strokes, labeled directly inside each band at its widest section, and grounded
by a calendar barcode tick floor below.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from palette import ThemePalette, contrast_ratio
from svg_builder import FrameLayout, SvgCanvas, fmt


def _smooth_open_path(pts: List[Tuple[float, float]]) -> str:
    if not pts:
        return ""
    d = [f"M {fmt(pts[0][0])} {fmt(pts[0][1])}"]
    for k in range(1, len(pts) - 1):
        px, py = pts[k]
        qx, qy = pts[k + 1]
        d.append(f"Q {fmt(px)} {fmt(py)} {fmt((px + qx) / 2.0)} {fmt((py + qy) / 2.0)}")
    d.append(f"L {fmt(pts[-1][0])} {fmt(pts[-1][1])}")
    return " ".join(d)


def _text_on_fill(fill_hex: str, palette: ThemePalette) -> str:
    light_txt = "#FFFFFF" if not palette.dark else palette.ink
    dark_txt = palette.ink if not palette.dark else palette.bg
    if contrast_ratio(light_txt, fill_hex) >= 3.2:
        return light_txt
    return dark_txt


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    series: List[Dict[str, Any]] = spec["series"]
    if len(series) < 2:
        raise ValueError("stream_ribbon requires at least 2 series in 'series'")

    n_pts = len(series[0]["values"])
    if n_pts < 4:
        raise ValueError("stream_ribbon requires at least 4 time points per series")

    title = spec.get("title", "Series trading the same river over time")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "STREAM RIBBON")
    ticks: List[Dict[str, Any]] = spec.get("ticks", [])
    unit_note = spec.get(
        "unit_note",
        "BAND WIDTH = VOLUME PER SERIES · TOTAL RIVER HEIGHT = COMBINED TOTAL",
    )

    mat = [[max(0.0, float(v)) for v in s["values"]] for s in series]
    totals = [sum(mat[si][t] for si in range(len(series))) for t in range(n_pts)]
    max_tot = max(totals) or 1.0

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "stream-ribbon"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    pad_l = 28.0 if layout.mode == "slide" else 16.0
    pad_r = 28.0 if layout.mode == "slide" else 16.0
    top_pad = 18.0 if layout.mode == "slide" else 12.0
    floor_reserve = 56.0 if layout.mode == "slide" else 42.0

    x0 = layout.chart_x + pad_l
    x1 = layout.chart_right - pad_r
    river_top = layout.chart_y + top_pad
    river_bot = layout.chart_bottom - floor_reserve
    river_h = max(80.0, river_bot - river_top)
    cy = (river_top + river_bot) / 2.0
    scale = (river_h * 0.88) / max_tot

    def map_x(t: int) -> float:
        return x0 + (t / max(n_pts - 1, 1)) * (x1 - x0)

    marks_g = canvas.add_group(area, "chart-marks")
    grid_g = canvas.add_group(area, "chart-grid")
    labels_g = canvas.add_group(area, "chart-labels")

    # Silhouette baseline: center total stack around cy
    run_y = [cy - (totals[t] * scale) / 2.0 for t in range(n_pts)]
    lbl_size = 15.0 if layout.mode == "slide" else 12.0

    for si, s in enumerate(series):
        vals = mat[si]
        top_pts = [(map_x(t), run_y[t]) for t in range(n_pts)]
        bot_pts = [(map_x(t), run_y[t] + vals[t] * scale) for t in range(n_pts)]
        run_y = [p[1] for p in bot_pts]

        col = palette.series_color(si)
        rev_bot = list(reversed(bot_pts))
        # Smooth top edge forward, smooth bottom edge backward
        d_top = _smooth_open_path(top_pts)
        d_bot_parts = [f"L {fmt(rev_bot[0][0])} {fmt(rev_bot[0][1])}"]
        for k in range(1, len(rev_bot) - 1):
            px, py = rev_bot[k]
            qx, qy = rev_bot[k + 1]
            d_bot_parts.append(f"Q {fmt(px)} {fmt(py)} {fmt((px + qx) / 2.0)} {fmt((py + qy) / 2.0)}")
        d_bot_parts.append(f"L {fmt(rev_bot[-1][0])} {fmt(rev_bot[-1][1])} Z")
        path_d = d_top + " " + " ".join(d_bot_parts)

        canvas.add_path(
            marks_g,
            path_d,
            fill=col,
            stroke=palette.bg,
            stroke_width=2.4 if layout.mode == "slide" else 1.8,
            stroke_linejoin="round",
        )

        # Label inside band at its widest interior point
        lo_i = max(2, int(n_pts * 0.12))
        hi_i = min(n_pts - 3, int(n_pts * 0.88))
        best_t = max(range(lo_i, hi_i + 1), key=lambda t: vals[t])
        mid_y = (top_pts[best_t][1] + bot_pts[best_t][1]) / 2.0
        band_h = bot_pts[best_t][1] - top_pts[best_t][1]
        if band_h >= lbl_size * 1.25:
            canvas.add_text(
                labels_g,
                map_x(best_t),
                mid_y + lbl_size * 0.34,
                str(s["label"]),
                font_size=lbl_size,
                font_weight=800,
                fill=_text_on_fill(col, palette),
                text_anchor="middle",
                letter_spacing=0.8,
            )

    # Calendar barcode floor below river
    floor_y = layout.chart_bottom - (28.0 if layout.mode == "slide" else 22.0)
    canvas.add_line(grid_g, x0 - 6, floor_y, x1 + 6, floor_y, stroke=palette.grid, stroke_width=1.2)
    major_step = max(1, n_pts // 6)
    tick_segs = []
    for t in range(n_pts):
        tx = map_x(t)
        th = (10.0 if t % major_step == 0 else 5.5) if layout.mode == "slide" else (7.0 if t % major_step == 0 else 4.0)
        tick_segs.append(f"M {fmt(tx)} {fmt(floor_y)} V {fmt(floor_y - th)}")
    canvas.add_path(grid_g, " ".join(tick_segs), fill="none", stroke=palette.floor, stroke_width=1.0)

    axis_size = 12.5 if layout.mode == "slide" else 12.0
    if not ticks:
        ticks = [{"index": t, "label": f"T{t+1}"} for t in range(0, n_pts, major_step)]
    for tk in ticks:
        idx = max(0, min(n_pts - 1, int(tk["index"])))
        anchor = "start" if idx == 0 else ("end" if idx >= n_pts - 2 else "middle")
        canvas.add_text(
            labels_g,
            map_x(idx),
            floor_y + (22.0 if layout.mode == "slide" else 18.0),
            str(tk["label"]),
            font_size=axis_size,
            font_weight=600,
            fill=palette.muted,
            text_anchor=anchor,
            letter_spacing=0.8,
        )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
