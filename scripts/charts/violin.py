#!/usr/bin/env python3
"""G19 · Violin — Static Gaussian KDE density silhouettes with median bars.

Accepts raw sample arrays `samples` (or mean/spread parameters for compact
specs), computes smooth mirrored Gaussian kernel density silhouettes in pure
Python, draws a crisp paper median bar across each violin belly, and labels the
median right beside it.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

from palette import ThemePalette, mix_hex
from svg_builder import FrameLayout, SvgCanvas, fmt, format_number, rnd


def _synthesize_samples(mean: float, spread: float, seed: int, count: int = 64) -> List[float]:
    out = []
    for i in range(count):
        z = (rnd(i + 1, seed * 3 + 1) + rnd(i + 7, seed * 3 + 2) + rnd(i + 13, seed * 3 + 3)) - 1.5
        out.append(max(0.1, mean + spread * z))
    return out


def _median(vals: List[float]) -> float:
    s = sorted(vals)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 == 1 else (s[mid - 1] + s[mid]) / 2.0


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    items: List[Dict[str, Any]] = spec["data"]
    if not items:
        raise ValueError("violin requires non-empty 'data' list")

    title = spec.get("title", "Distribution density across groups")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "VIOLIN")
    prefix = spec.get("value_prefix", "")
    suffix = spec.get("value_suffix", "")
    highlight_idx = spec.get("highlight_index", 0)
    unit_note = spec.get(
        "unit_note",
        "WIDTH = DENSITY AT THAT VALUE · PAPER BAR = MEDIAN · ACCENT = BENCHMARK GROUP",
    )

    sample_sets: List[List[float]] = []
    for idx, d in enumerate(items):
        if "samples" in d and d["samples"]:
            sample_sets.append([float(v) for v in d["samples"]])
        else:
            sample_sets.append(_synthesize_samples(float(d["mean"]), float(d["spread"]), idx + 1))

    all_v = [v for grp in sample_sets for v in grp]
    y_min = float(spec.get("y_min", min(0.0, min(all_v))))
    y_max = float(spec.get("y_max", max(all_v) * 1.15))
    if y_max <= y_min:
        y_max = y_min + 1.0

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "violin"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    left_rail = 68.0 if layout.mode == "slide" else 48.0
    right_pad = 58.0 if layout.mode == "slide" else 36.0
    top_pad = 24.0 if layout.mode == "slide" else 18.0
    bot_pad = 44.0 if layout.mode == "slide" else 34.0

    x0 = layout.chart_x + left_rail
    x1 = layout.chart_right - right_pad
    y_top = layout.chart_y + top_pad
    y_bot = layout.chart_bottom - bot_pad

    def map_y(v: float) -> float:
        return y_bot - ((v - y_min) / (y_max - y_min)) * (y_bot - y_top)

    grid_g = canvas.add_group(area, "chart-grid")
    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    axis_size = 12.5 if layout.mode == "slide" else 12.0
    for g in range(5):
        v = y_min + (g / 4.0) * (y_max - y_min)
        gy = map_y(v)
        canvas.add_line(grid_g, x0, gy, x1, gy, stroke=palette.grid if g == 0 else palette.quiet, stroke_width=1.2 if g == 0 else 1.0)
        canvas.add_text(
            labels_g,
            x0 - 14.0,
            gy + axis_size * 0.34,
            format_number(v, prefix, suffix, decimals=0),
            font_size=axis_size,
            font_weight=600,
            fill=palette.muted,
            text_anchor="end",
        )

    canvas.add_comment(
        area,
        f"chart-plot-area: object={canvas.chart_id} | "
        f"{fmt(x0)},{fmt(y_top)},{fmt(x1)},{fmt(y_bot)}",
    )

    n = len(items)
    slot_w = (x1 - x0) / max(n, 1)
    max_half_w = min(slot_w * 0.32, 68.0 if layout.mode == "slide" else 40.0)
    accent_col = palette.c3 if len(palette.colors) >= 3 else palette.c2
    med_size = 15.0 if layout.mode == "slide" else 12.5
    cat_size = 14.0 if layout.mode == "slide" else 12.0

    n_grid = 42
    for i, d in enumerate(items):
        vs = sorted(sample_sets[i])
        med = _median(vs)
        std = math.sqrt(sum((v - sum(vs) / len(vs)) ** 2 for v in vs) / max(len(vs), 1)) or 0.5
        bw = max((y_max - y_min) * 0.045, std * 0.65)
        lo = max(y_min, vs[0] - bw * 1.6)
        hi = min(y_max, vs[-1] + bw * 1.6)

        grid_vals = [lo + (k / (n_grid - 1)) * (hi - lo) for k in range(n_grid)]
        dens = [
            sum(math.exp(-((gv - v) ** 2) / (2.0 * bw * bw)) for v in vs)
            for gv in grid_vals
        ]
        d_max = max(dens) or 1.0

        cx = x0 + (i + 0.5) * slot_w
        pts: List[Tuple[float, float]] = []
        for k in range(n_grid):
            pts.append((cx + (dens[k] / d_max) * max_half_w, map_y(grid_vals[k])))
        for k in range(n_grid - 1, -1, -1):
            pts.append((cx - (dens[k] / d_max) * max_half_w, map_y(grid_vals[k])))

        # Smooth closed quadratic midpoint path
        d_parts = [f"M {fmt(pts[0][0])} {fmt(pts[0][1])}"]
        m = len(pts)
        for t in range(m):
            px, py = pts[t]
            qx, qy = pts[(t + 1) % m]
            d_parts.append(f"Q {fmt(px)} {fmt(py)} {fmt((px + qx) / 2.0)} {fmt((py + qy) / 2.0)}")
        path_d = " ".join(d_parts) + " Z"

        is_hero = i == highlight_idx
        frac = i / max(n - 1, 1)
        col = accent_col if is_hero else (mix_hex(palette.c1, palette.c2, frac * 0.7) if len(palette.colors) >= 2 else palette.c1)

        grp = canvas.add_group(marks_g, f"violin-{i+1}")
        canvas.add_path(grp, path_d, fill=col, fill_opacity=0.88)

        # Paper median tick across the silhouette
        mk = max(0, min(n_grid - 1, int(round(((med - lo) / max(hi - lo, 1e-6)) * (n_grid - 1)))))
        w_med = (dens[mk] / d_max) * max_half_w
        ym = map_y(med)
        canvas.add_line(
            grp,
            cx - w_med + 3.0,
            ym,
            cx + w_med - 3.0,
            ym,
            stroke=palette.bg if not palette.dark else palette.ink,
            stroke_width=3.2 if layout.mode == "slide" else 2.4,
            stroke_linecap="round",
        )
        canvas.add_text(
            labels_g,
            cx + max_half_w + 8.0,
            ym + med_size * 0.34,
            format_number(med, prefix, suffix, decimals=1),
            font_size=med_size,
            font_weight=800,
            fill=col if is_hero else palette.ink,
        )

        # Category label
        canvas.add_text(
            labels_g,
            cx,
            y_bot + (28.0 if layout.mode == "slide" else 22.0),
            str(d["label"]),
            font_size=cat_size,
            font_weight=700 if is_hero else 600,
            fill=palette.ink if is_hero else palette.label,
            text_anchor="middle",
            letter_spacing=0.6,
        )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
