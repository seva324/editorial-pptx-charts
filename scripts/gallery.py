#!/usr/bin/env python3
"""Batch-render a directory of chart JSON specs into SVGs + static HTML gallery preview.

Optionally runs ppt-master's own `svg_quality_checker.py` and `svg_to_pptx.py`
to produce a real natively editable `.pptx` verification deck.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from palette import extract_palette_from_ppt_master
from pptx_bridge import export_via_ppt_master, run_ppt_master_checker
from render import render_chart_spec
from validator import validate_svg_file


def build_html_gallery(svg_files: List[Path], out_html: Path, title: str, swatches: List[str]) -> None:
    chip_html = "".join(
        f'<span style="display:inline-block;width:14px;height:14px;border-radius:99px;'
        f'background:{c};margin-right:6px;vertical-align:middle;border:1px solid rgba(0,0,0,.12)"></span>'
        f'<code style="margin-right:14px;font-size:12px">{c}</code>'
        for c in swatches
    )
    cards = []
    for f in svg_files:
        cards.append(
            f'<div class="card"><div class="meta">{f.name}</div>'
            f'<img src="{f.name}" alt="{f.stem}"/></div>'
        )
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<title>{title}</title>
<style>
  body{{margin:0;padding:32px;background:#ECECE8;font-family:Arial,'Microsoft YaHei',sans-serif;color:#1C1C1A}}
  h1{{margin:0 0 8px;font-size:22px}}
  .swatches{{margin-bottom:24px;font-size:13px;color:#555}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(560px,1fr));gap:20px}}
  .card{{background:#FFF;border-radius:12px;padding:12px;box-shadow:0 2px 10px rgba(0,0,0,.06)}}
  .meta{{font-size:12px;color:#666;margin-bottom:8px;font-family:monospace}}
  .card img{{width:100%;height:auto;display:block;border:1px solid #E5E7EB;border-radius:6px}}
</style>
</head>
<body>
  <h1>{title}</h1>
  <div class="swatches">Theme colors: {chip_html}</div>
  <div class="grid">
    {"".join(cards)}
  </div>
</body>
</html>
"""
    out_html.write_text(html, encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Batch-render chart specs and build preview gallery")
    parser.add_argument("--specs-dir", required=True, help="Directory of chart *.json spec files")
    parser.add_argument("--out-dir", required=True, help="Output directory for SVG files & index.html")
    parser.add_argument("--colors", help="Comma-separated 2-3 hex theme colors")
    parser.add_argument("--from-ppt-master", dest="ppt_master_spec", help="Extract palette from ppt-master design_spec.md or spec_lock.md")
    parser.add_argument("--bg", help="Background hex or 'transparent'")
    parser.add_argument("--mode", choices=["slide", "card"], default="slide")
    parser.add_argument("--ppt-master", help="Optional path to ppt-master repo for native quality check & .pptx export")
    parser.add_argument("--export-pptx", help="Optional output .pptx path (requires --ppt-master and --mode slide)")
    args = parser.parse_args(argv)

    specs_dir = Path(args.specs_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    colors_list = [c.strip() for c in args.colors.split(",") if c.strip()] if args.colors else None
    swatches = list(colors_list or [])
    if not swatches and args.ppt_master_spec:
        swatches = extract_palette_from_ppt_master(args.ppt_master_spec)["colors"]

    spec_files = sorted(specs_dir.glob("*.json"))
    if not spec_files:
        print(f"No JSON specs found in {specs_dir}")
        return 1

    svg_paths: List[Path] = []
    failed = 0
    for sp in spec_files:
        spec = json.loads(sp.read_text(encoding="utf-8"))
        svg_str = render_chart_spec(
            spec,
            colors=colors_list,
            bg=args.bg,
            ppt_master_spec=args.ppt_master_spec,
            mode=args.mode,
        )
        out_svg = out_dir / f"{sp.stem}.svg"
        out_svg.write_text(svg_str, encoding="utf-8")
        rep = validate_svg_file(out_svg)
        status = "PASS" if rep.ok else "FAIL"
        print(f"[{status}] {out_svg.name} (errors={len(rep.errors)}, warnings={len(rep.warnings)})")
        for err in rep.errors:
            print(f"  ERROR: {err}")
        if not rep.ok:
            failed += 1
        svg_paths.append(out_svg)

    build_html_gallery(svg_paths, out_dir / "index.html", "Editorial PPTX Charts — Phase 1 Gallery", swatches)
    print(f"Gallery preview written: {out_dir / 'index.html'}")

    if args.ppt_master:
        print("\n=== Running ppt-master svg_quality_checker.py ===")
        for svg in svg_paths:
            rc = run_ppt_master_checker(args.ppt_master, svg)
            if rc != 0:
                failed += 1

        if args.export_pptx and args.mode == "slide":
            print("\n=== Exporting natively editable PPTX via ppt-master svg_to_pptx.py ===")
            pptx_out = export_via_ppt_master(args.ppt_master, svg_paths, args.export_pptx)
            print(f"PPTX ready: {pptx_out}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
