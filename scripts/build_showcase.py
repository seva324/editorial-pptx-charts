#!/usr/bin/env python3
"""Build one combined showcase from multiple chart-spec directories.

Renders every spec in the given directories (in order) into a single output
folder with sequential page prefixes, emits one browsable HTML gallery, and
optionally compiles the whole set into a single natively editable `.pptx`
through `ppt-master`'s `svg_to_pptx.py`.

Example
-------
    python scripts/build_showcase.py \
      --spec-dirs examples/phase1_specs examples/phase2_specs examples/phase3_specs \
      --out-dir examples/out/showcase \
      --colors "#051C2C,#2251FF,#E65100" \
      --title "Editorial PPTX Charts — 37 chart types" \
      --ppt-master /path/to/ppt-master \
      --export-pptx examples/demo/editorial_charts_37.pptx
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

from gallery import build_html_gallery
from palette import extract_palette_from_ppt_master
from pptx_bridge import export_via_ppt_master, run_ppt_master_checker
from render import render_chart_spec
from validator import validate_svg_file


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build one combined chart showcase + optional single PPTX")
    parser.add_argument("--spec-dirs", nargs="+", required=True, help="Spec directories, in page order")
    parser.add_argument("--out-dir", required=True, help="Output directory for SVGs and gallery")
    parser.add_argument("--colors", help="Comma-separated 2-3 hex theme colors")
    parser.add_argument("--from-ppt-master", dest="ppt_master_spec", help="Extract palette from a ppt-master design_spec.md / spec_lock.md")
    parser.add_argument("--bg", help="Background hex or 'transparent'")
    parser.add_argument("--mode", choices=["slide", "card"], default="slide")
    parser.add_argument("--title", default="Editorial PPTX Charts", help="Gallery HTML title")
    parser.add_argument("--ppt-master", help="ppt-master repo path for native quality check + PPTX export")
    parser.add_argument("--export-pptx", help="Output .pptx path (requires --ppt-master and --mode slide)")
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    # Start from a clean page set so re-runs never leave stale pages behind
    for stale in out_dir.glob("*.svg"):
        stale.unlink()

    colors_list = [c.strip() for c in args.colors.split(",") if c.strip()] if args.colors else None
    swatches = list(colors_list or [])
    if not swatches and args.ppt_master_spec:
        swatches = extract_palette_from_ppt_master(args.ppt_master_spec)["colors"]

    spec_files: List[Path] = []
    for d in args.spec_dirs:
        dd = Path(d).resolve()
        if not dd.is_dir():
            print(f"Skip missing spec dir: {dd}")
            continue
        spec_files.extend(sorted(dd.glob("*.json")))
    if not spec_files:
        print("No JSON specs found in the given directories")
        return 1

    svg_paths: List[Path] = []
    failed = 0
    for idx, sp in enumerate(spec_files, start=1):
        spec = json.loads(sp.read_text(encoding="utf-8"))
        svg_str = render_chart_spec(
            spec,
            colors=colors_list,
            bg=args.bg,
            ppt_master_spec=args.ppt_master_spec,
            mode=args.mode,
        )
        # Keep the source ordinal in the filename so page order is obvious & stable
        stem = sp.stem
        parts = stem.split("_", 1)
        readable = parts[1] if len(parts) == 2 and parts[0].isdigit() else stem
        out_svg = out_dir / f"{idx:02d}_{readable}.svg"
        out_svg.write_text(svg_str, encoding="utf-8")
        rep = validate_svg_file(out_svg)
        status = "PASS" if rep.ok else "FAIL"
        print(f"[{status}] {out_svg.name} (errors={len(rep.errors)}, warnings={len(rep.warnings)})")
        for err in rep.errors:
            print(f"  ERROR: {err}")
        if not rep.ok:
            failed += 1
        svg_paths.append(out_svg)

    build_html_gallery(svg_paths, out_dir / "index.html", args.title, swatches)
    print(f"\nPages: {len(svg_paths)} | Gallery: {out_dir / 'index.html'}")

    if args.ppt_master:
        print("\n=== ppt-master svg_quality_checker.py ===")
        for svg in svg_paths:
            if run_ppt_master_checker(args.ppt_master, svg) != 0:
                failed += 1

        if args.export_pptx and args.mode == "slide":
            out_pptx = Path(args.export_pptx).resolve()
            print(f"\n=== Compiling natively editable PPTX: {out_pptx.name} ===")
            pptx_path = export_via_ppt_master(
                args.ppt_master, svg_paths, out_pptx, work_dir=out_dir.parent / "_showcase_stage"
            )
            print(f"PPTX ready: {pptx_path}")

    print(f"\n{'FAILED' if failed else 'ALL PASSED'} ({len(svg_paths) - failed}/{len(svg_paths)})")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
