#!/usr/bin/env python3
"""L14 · Hundred Field — Phyllotaxis golden-angle 100-dot cluster constellation.

Decomposes a 100% composition (2-5 groups) into 100 countable unit dots arranged
in golden-angle phyllotaxis clusters, tied together by delicate dashed
constellation hairlines and radial spokes on every 5th unit.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

from palette import ThemePalette
from svg_builder import FrameLayout, SvgCanvas, fmt, pol, rnd


def _normalize_to_100(values: List[float]) -> List[int]:
    total = sum(values)
    if total <= 0:
        return [0] * len(values)
    raw = [v / total * 100.0 for v in values]
    floors = [int(math.floor(r)) for r in raw]
    rem = 100 - sum(floors)
    order = sorted(range(len(raw)), key=lambda i: raw[i] - floors[i], reverse=True)
    for idx in order[:rem]:
        floors[idx] += 1
    return floors


def _cluster_centers(n: int, x0: float, y0: float, w: float, h: float) -> List[Tuple[float, float]]:
    if n == 2:
        return [(x0 + w * 0.34, y0 + h * 0.50), (x0 + w * 0.68, y0 + h * 0.50)]
    if n == 3:
        return [
            (x0 + w * 0.32, y0 + h * 0.44),
            (x0 + w * 0.68, y0 + h * 0.36),
            (x0 + w * 0.54, y0 + h * 0.72),
        ]
    if n == 4:
        return [
            (x0 + w * 0.28, y0 + h * 0.42),
            (x0 + w * 0.66, y0 + h * 0.34),
            (x0 + w * 0.42, y0 + h * 0.74),
            (x0 + w * 0.78, y0 + h * 0.70),
        ]
    # 5 or more: balanced pentagon/ellipse layout
    out = []
    for i in range(n):
        ang = -90.0 + i * (360.0 / n)
        cx, cy = pol(x0 + w * 0.5, y0 + h * 0.48, min(w * 0.30, h * 0.30), ang)
        out.append((cx, cy))
    return out


def render(spec: Dict[str, Any], palette: ThemePalette, layout: FrameLayout) -> str:
    items: List[Dict[str, Any]] = spec["data"]
    if not items:
        raise ValueError("hundred_field requires non-empty 'data' list")

    title = spec.get("title", "A hundred of us, clustered by view")
    subtitle = spec.get("subtitle", "")
    source = spec.get("source", "HUNDRED FIELD")

    raw_vals = [max(0.0, float(d["value"])) for d in items]
    pcts = _normalize_to_100(raw_vals)
    sum_expr = " + ".join(str(p) for p in pcts)
    unit_note = spec.get("unit_note", f"ONE DOT = ONE IN A HUNDRED · {sum_expr} = 100")

    canvas = SvgCanvas(layout, palette, chart_id=spec.get("id", "hundred-field"))
    canvas.add_header(title, subtitle)
    _outer, area = canvas.add_chart_area()

    centers = _cluster_centers(len(items), layout.chart_x, layout.chart_y, layout.chart_w, layout.chart_h)
    grid_g = canvas.add_group(area, "chart-grid")
    marks_g = canvas.add_group(area, "chart-marks")
    labels_g = canvas.add_group(area, "chart-labels")

    # Constellation dashed lines tying cluster cores
    n = len(centers)
    edges = [(i, (i + 1) % n) for i in range(n)] if n >= 3 else [(0, 1)]
    if n == 4:
        edges = [(0, 1), (0, 2), (1, 3), (2, 3)]
    for a, b in edges:
        canvas.add_line(
            grid_g,
            centers[a][0],
            centers[a][1],
            centers[b][0],
            centers[b][1],
            stroke=palette.grid,
            stroke_width=1.3,
            stroke_dasharray="3,6",
        )

    step_r = 16.5 if layout.mode == "slide" else 10.5
    base_r = 10.0 if layout.mode == "slide" else 6.5
    dot_min = 3.2 if layout.mode == "slide" else 2.2
    dot_var = 2.6 if layout.mode == "slide" else 1.8
    lbl_size = 15.0 if layout.mode == "slide" else 12.5

    for ci, item in enumerate(items):
        cx, cy = centers[ci]
        v = pcts[ci]
        col = palette.series_color(ci)
        clu_g = canvas.add_group(marks_g, f"cluster-{ci+1}")

        edge = 0.0
        for k in range(v):
            ang = k * 137.508 + ci * 55.0
            rr = base_r + math.sqrt(k) * step_r + rnd(k + 1, ci + 2) * (6.0 if layout.mode == "slide" else 3.5)
            edge = max(edge, rr)
            px, py = pol(cx, cy, rr, ang)
            if k % 5 == 0:
                canvas.add_line(clu_g, cx, cy, px, py, stroke=palette.floor, stroke_width=1.0, stroke_opacity=0.65)
            dr = dot_min + rnd(k + 2, ci + 3) * dot_var
            canvas.add_circle(clu_g, px, py, dr, fill=col, fill_opacity=0.90)

        # Cluster core anchor dot
        canvas.add_circle(clu_g, cx, cy, 4.5 if layout.mode == "slide" else 3.0, fill=palette.ink)

        # Label cleanly below cluster edge
        ly = min(layout.chart_bottom - 10.0, cy + edge + (24.0 if layout.mode == "slide" else 18.0))
        canvas.add_text(
            labels_g,
            cx,
            ly,
            f"{item['label']} · {v}%",
            font_size=lbl_size,
            font_weight=800,
            fill=col if ci < 3 else palette.ink,
            text_anchor="middle",
            letter_spacing=0.8,
        )

    canvas.add_footer(unit_note, source)
    return canvas.to_string()
