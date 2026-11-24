#!/usr/bin/env python3
"""Unified CLI for rendering pure-static, ppt-master-compatible editorial charts.

Examples
--------
1) Render with custom 2-3 theme colors (slide mode 1280x720):
   python scripts/render.py examples/phase1_specs/01_rung_bars.json \
       --colors "#051C2C,#2251FF" --bg "#FFFFFF" -o out/rung_bars.svg

2) Render pulling theme colors directly from a ppt-master template/spec:
   python scripts/render.py examples/phase1_specs/01_rung_bars.json \
       --from-ppt-master /path/to/ppt-master/skills/ppt-master/templates/brands/mckinsey/templates/design_spec.md \
       -o out/rung_bars.svg

3) Render as a transparent sub-canvas card to drop into a ppt-master slide:
   python scripts/render.py examples/phase1_specs/05_tick_donut.json \
       --colors "#1D4ED8,#0F766E,#D97706" --bg transparent --mode card --width 600 --height 440 \
       -o out/tick_donut_card.svg
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from charts import CHART_REGISTRY, get_renderer
from palette import build_palette, extract_palette_from_ppt_master
from svg_builder import compute_layout
from validator import validate_svg_file


def render_chart_spec(
    spec: Dict[str, Any],
    *,
    colors: Optional[List[str]] = None,
    bg: Optional[str] = None,
    ink: Optional[str] = None,
    dark: Optional[bool] = None,
    font_family: Optional[str] = None,
    ppt_master_spec: Optional[str | Path] = None,
    mode: Optional[str] = None,
    width: Optional[float] = None,
    height: Optional[float] = None,
) -> str:
    """Render a JSON chart spec dictionary into a pure-static SVG string."""
    theme_cfg: Dict[str, Any] = dict(spec.get("theme") or {})

    if ppt_master_spec:
        extracted = extract_palette_from_ppt_master(ppt_master_spec)
        theme_cfg.setdefault("colors", extracted["colors"])
        theme_cfg.setdefault("bg", extracted["bg"])
        if extracted.get("ink"):
            theme_cfg.setdefault("ink", extracted["ink"])
        if extracted.get("font_family"):
            theme_cfg.setdefault("font_family", extracted["font_family"])

    final_colors = colors or theme_cfg.get("colors")
    if not final_colors:
        raise ValueError(
            "Theme colors required: pass --colors '#HEX1,#HEX2[,#HEX3]', "
            "--from-ppt-master <spec>, or set spec['theme']['colors']."
        )

    final_bg = bg if bg is not None else theme_cfg.get("bg", "#FFFFFF")
    final_ink = ink if ink is not None else theme_cfg.get("ink")
    final_dark = dark if dark is not None else theme_cfg.get("dark", spec.get("dark"))
    final_font = font_family or theme_cfg.get("font_family")

    palette = build_palette(
        final_colors,
        bg=final_bg,
        ink=final_ink,
        dark=final_dark,
        font_family=final_font,
    )

    final_mode = mode or spec.get("mode", "slide")
    layout = compute_layout(
        mode=final_mode,
        width=width or spec.get("width"),
        height=height or spec.get("height"),
        has_subtitle=bool(spec.get("subtitle")),
        has_note=bool(spec.get("unit_note", True)),
        has_source=bool(spec.get("source", True)),
    )

    renderer = get_renderer(spec["type"])
    return renderer(spec, palette, layout)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Render pure-static editorial charts for ppt-master")
    parser.add_argument("spec", nargs="?", help="Path to chart JSON specification file")
    parser.add_argument("--list", action="store_true", help="List available chart types and exit")
    parser.add_argument("--colors", help="Comma-separated 2-3 hex theme colors, e.g. '#051C2C,#2251FF,#D97706'")
    parser.add_argument("--from-ppt-master", dest="ppt_master_spec", help="Extract palette from ppt-master design_spec.md or spec_lock.md")
    parser.add_argument("--bg", help="Slide/card background hex or 'transparent'")
    parser.add_argument("--ink", help="Override primary text hex color")
    parser.add_argument("--dark", action="store_true", default=None, help="Force dark-card surface derived from primary theme color")
    parser.add_argument("--light", action="store_true", help="Force light surface even if spec defaults to dark")
    parser.add_argument("--font", dest="font_family", help="Override font-family stack")
    parser.add_argument("--mode", choices=["slide", "card"], help="Output canvas mode: slide (1280x720) or card (sub-region)")
    parser.add_argument("--width", type=float, help="Custom SVG width in px")
    parser.add_argument("--height", type=float, help="Custom SVG height in px")
    parser.add_argument("-o", "--output", help="Output .svg file path (prints to stdout if omitted)")
    parser.add_argument("--no-validate", action="store_true", help="Skip built-in ppt-master SVG contract validation")
    args = parser.parse_args(argv)

    if args.list:
        for k in sorted(CHART_REGISTRY):
            print(k)
        return 0

    if not args.spec:
        parser.error("spec JSON path is required (or pass --list)")

    spec_path = Path(args.spec)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    colors_list = [c.strip() for c in args.colors.split(",") if c.strip()] if args.colors else None
    dark_flag = False if args.light else args.dark

    svg_str = render_chart_spec(
        spec,
        colors=colors_list,
        bg=args.bg,
        ink=args.ink,
        dark=dark_flag,
        font_family=args.font_family,
        ppt_master_spec=args.ppt_master_spec,
        mode=args.mode,
        width=args.width,
        height=args.height,
    )

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(svg_str, encoding="utf-8")
        if not args.no_validate:
            rep = validate_svg_file(out)
            if not rep.ok:
                print(f"[FAIL] {out}: {rep.errors}", file=sys.stderr)
                return 1
        print(f"Wrote {out}")
    else:
        sys.stdout.write(svg_str)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
