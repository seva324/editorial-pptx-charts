"""Editorial chart renderer registry (Phase 1 + Phase 2 + Phase 3: 37 chart types)."""

from __future__ import annotations

from typing import Any, Callable, Dict

from palette import ThemePalette
from svg_builder import FrameLayout

from . import (
    aggregate_sankey,
    arc_matrix,
    ballot_tally,
    barcode_lollipop,
    big_slice,
    calendar_heat,
    candlestick,
    diverging_bar,
    dot_cascade,
    dot_heat,
    dot_waffle,
    dumbbell_queue,
    hairline_area,
    hairline_line,
    hourglass_stream,
    hundred_field,
    launch_fan,
    matrix_heat,
    nested_treemap,
    paired_rungs,
    parallel_coords,
    plumb_scatter,
    radial_convergence,
    radial_patchwork,
    rank_strip,
    rung_bars,
    rung_histogram,
    rung_waterfall,
    stacked_rungs,
    stream_ribbon,
    tick_box,
    tick_donut,
    tick_gauge,
    tick_rows,
    trend_lineage,
    type_colonnade,
    violin,
)

ChartRenderer = Callable[[Dict[str, Any], ThemePalette, FrameLayout], str]

CHART_REGISTRY: Dict[str, ChartRenderer] = {
    # Phase 1 — Core high-frequency (12)
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
    # Phase 2 — Lupi Basics completion + Lupi Editorial classics (15)
    "plumb_scatter": plumb_scatter.render,
    "rung_waterfall": rung_waterfall.render,
    "tick_gauge": tick_gauge.render,
    "launch_fan": launch_fan.render,
    "barcode_lollipop": barcode_lollipop.render,
    "arc_matrix": arc_matrix.render,
    "hourglass_stream": hourglass_stream.render,
    "hundred_field": hundred_field.render,
    "ballot_tally": ballot_tally.render,
    "calendar_heat": calendar_heat.render,
    "parallel_coords": parallel_coords.render,
    "radial_patchwork": radial_patchwork.render,
    "trend_lineage": trend_lineage.render,
    "type_colonnade": type_colonnade.render,
    "radial_convergence": radial_convergence.render,
    # Phase 3 — Distributions, financial/hierarchical & Glance fast-read completion (10)
    "nested_treemap": nested_treemap.render,
    "rung_histogram": rung_histogram.render,
    "tick_box": tick_box.render,
    "stream_ribbon": stream_ribbon.render,
    "candlestick": candlestick.render,
    "big_slice": big_slice.render,
    "violin": violin.render,
    "matrix_heat": matrix_heat.render,
    "rank_strip": rank_strip.render,
    "aggregate_sankey": aggregate_sankey.render,
}


def get_renderer(chart_type: str) -> ChartRenderer:
    key = chart_type.strip().lower().replace("-", "_")
    if key not in CHART_REGISTRY:
        avail = ", ".join(sorted(CHART_REGISTRY))
        raise KeyError(f"Unknown chart type {chart_type!r}. Available types ({len(CHART_REGISTRY)}): {avail}")
    return CHART_REGISTRY[key]
