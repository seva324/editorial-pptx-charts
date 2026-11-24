"""Phase 1 editorial chart renderer registry."""

from __future__ import annotations

from typing import Any, Callable, Dict

from palette import ThemePalette
from svg_builder import FrameLayout

from . import (
    diverging_bar,
    dot_cascade,
    dot_heat,
    dot_waffle,
    dumbbell_queue,
    hairline_area,
    hairline_line,
    paired_rungs,
    rung_bars,
    stacked_rungs,
    tick_donut,
    tick_rows,
)

ChartRenderer = Callable[[Dict[str, Any], ThemePalette, FrameLayout], str]

CHART_REGISTRY: Dict[str, ChartRenderer] = {
    "rung_bars": rung_bars.render,
    "tick_rows": tick_rows.render,
    "hairline_line": hairline_line.render,
    "hairline_area": hairline_area.render,
    "tick_donut": tick_donut.render,
    "paired_rungs": paired_rungs.render,
    "stacked_rungs": stacked_rungs.render,
    "dumbbell_queue": dumbbell_queue.render,
    "dot_heat": dot_heat.render,
    "dot_cascade": dot_cascade.render,
    "diverging_bar": diverging_bar.render,
    "dot_waffle": dot_waffle.render,
}


def get_renderer(chart_type: str) -> ChartRenderer:
    key = chart_type.strip().lower().replace("-", "_")
    if key not in CHART_REGISTRY:
        avail = ", ".join(sorted(CHART_REGISTRY))
        raise KeyError(f"Unknown chart type {chart_type!r}. Available Phase 1 types: {avail}")
    return CHART_REGISTRY[key]
