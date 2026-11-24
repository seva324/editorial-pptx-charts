#!/usr/bin/env python3
"""Bridge between editorial-pptx-charts and ppt-master.

Supports three integration workflows:
  1. Validate SVGs against ppt-master's own `svg_quality_checker.py` (when ppt-master path is provided)
  2. Export a directory of 1280x720 slide SVGs into a natively editable `.pptx`
     using ppt-master's `svg_to_pptx.py`
  3. Build a lightweight `ppt-master` project folder (`svg_output/`) ready for
     direct compilation or dropping into an existing ppt-master deck.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def find_ppt_master_scripts(ppt_master_dir: str | Path) -> Path:
    base = Path(ppt_master_dir).resolve()
    candidates = [
        base / "skills" / "ppt-master" / "scripts",
        base / "scripts",
        base,
    ]
    for cand in candidates:
        if (cand / "svg_to_pptx.py").exists() and (cand / "svg_quality_checker.py").exists():
            return cand
    raise FileNotFoundError(
        f"Could not locate svg_to_pptx.py / svg_quality_checker.py under {ppt_master_dir}"
    )


def run_ppt_master_checker(ppt_master_dir: str | Path, svg_target: str | Path) -> int:
    scripts = find_ppt_master_scripts(ppt_master_dir)
    cmd = [sys.executable, str(scripts / "svg_quality_checker.py"), str(Path(svg_target).resolve())]
    res = subprocess.run(cmd, check=False)
    return res.returncode


def export_via_ppt_master(
    ppt_master_dir: str | Path,
    svg_files: List[Path],
    output_pptx: str | Path,
    work_dir: Optional[str | Path] = None,
) -> Path:
    """Stage slide SVGs into a ppt-master flat project and compile to native editable .pptx."""
    scripts = find_ppt_master_scripts(ppt_master_dir)
    out_path = Path(output_pptx).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    proj_dir = Path(work_dir).resolve() if work_dir else (out_path.parent / "_ppt_master_stage")
    svg_out = proj_dir / "svg_output"
    if svg_out.exists():
        shutil.rmtree(svg_out)
    svg_out.mkdir(parents=True, exist_ok=True)

    for idx, src in enumerate(svg_files, start=1):
        # Drop any pre-existing numeric page prefix so slide names stay clean
        # ("01_01_rung_bars" -> "01_rung_bars"), and always number by position.
        parts = src.stem.split("_", 1)
        readable = parts[1] if len(parts) == 2 and parts[0].isdigit() else src.stem
        dst = svg_out / f"{idx:02d}_{readable}.svg"
        shutil.copy2(src, dst)

    # Run ppt-master's required pre-export final quality report on the staged project
    check_cmd = [
        sys.executable,
        str(scripts / "svg_quality_checker.py"),
        str(proj_dir),
        "--quick-generate",
        "--canonical-authoring",
        "--stage",
        "final",
        "--json",
    ]
    chk = subprocess.run(check_cmd, check=False)
    if chk.returncode != 0:
        raise RuntimeError(f"ppt-master svg_quality_checker.py exited with code {chk.returncode}")

    cmd = [
        sys.executable,
        str(scripts / "svg_to_pptx.py"),
        str(proj_dir),
        "--quick-generate",
        "-o",
        str(out_path),
    ]
    res = subprocess.run(cmd, check=False)
    if res.returncode != 0:
        raise RuntimeError(f"ppt-master svg_to_pptx.py exited with code {res.returncode}")
    return out_path


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and export editorial chart SVGs via ppt-master")
    parser.add_argument("--ppt-master", required=True, help="Path to ppt-master repo or skill directory")
    parser.add_argument("--svg-dir", required=True, help="Directory containing 1280x720 slide SVGs")
    parser.add_argument("--check-only", action="store_true", help="Only run ppt-master svg_quality_checker.py")
    parser.add_argument("-o", "--output", help="Output .pptx path (required unless --check-only)")
    args = parser.parse_args(argv)

    svg_dir = Path(args.svg_dir).resolve()
    svgs = sorted(svg_dir.glob("*.svg"))
    if not svgs:
        print(f"No SVG files found in {svg_dir}")
        return 1

    rc = 0
    for svg in svgs:
        r = run_ppt_master_checker(args.ppt_master, svg)
        if r != 0:
            rc = r

    if args.check_only:
        return rc

    if not args.output:
        print("Error: -o/--output .pptx path is required unless --check-only is set")
        return 2

    out = export_via_ppt_master(args.ppt_master, svgs, args.output)
    print(f"Exported natively editable PPTX: {out}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
