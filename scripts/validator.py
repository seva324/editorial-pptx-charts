#!/usr/bin/env python3
"""Standalone ppt-master SVG contract validator.

Checks every generated SVG against the strict ppt-master authoring contract:
  1. Valid XML & root <svg> viewBox="0 0 W H"
  2. Structural blacklist (no <style>, class, <script>, <animate*>, <mask>, <foreignObject>, etc.)
  3. Paint grammar (uppercase #RRGGBB or 'none', no rgba()/rgb()/hsl())
  4. Typography floor (font-size >= 12, finite unitless numbers, no dominant-baseline/em units)
  5. Top-level <g id="..." data-pptx-bounds="x y w h"> presence & non-overlap
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple
from xml.etree import ElementTree as ET

BANNED_TAGS = {
    "style", "script", "mask", "foreignobject", "textpath",
    "animate", "animatetransform", "animatemotion", "set", "iframe",
}
HEX6_RE = re.compile(r"^#[0-9A-F]{6}$")
NUM_RE = re.compile(r"^-?\d+(?:\.\d+)?$")


@dataclass
class ValidationReport:
    path: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def _local(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def validate_svg_file(svg_path: str | Path) -> ValidationReport:
    path = Path(svg_path)
    report = ValidationReport(str(path))
    raw = path.read_text(encoding="utf-8")

    # HTML named entity check
    html_ent = re.findall(r"&(nbsp|mdash|ndash|middot|copy|reg|rarr|hellip|bull);", raw)
    if html_ent:
        report.errors.append(f"Forbidden HTML named entities found: {sorted(set(html_ent))}")

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        report.errors.append(f"XML parse error: {exc}")
        return report

    if _local(root.tag) != "svg":
        report.errors.append(f"Root tag must be <svg>, got <{_local(root.tag)}>")
        return report

    vb = root.attrib.get("viewBox", "")
    vb_parts = vb.split()
    if len(vb_parts) != 4 or vb_parts[0] != "0" or vb_parts[1] != "0":
        report.errors.append(f"Invalid viewBox={vb!r}; expected '0 0 W H'")
    if "fill" in root.attrib or "stroke" in root.attrib:
        report.errors.append("Root <svg> must not declare fill or stroke paint")
    if not root.attrib.get("font-family"):
        report.errors.append("Root <svg> should declare font-family")

    # Top-level <g> bounds check & overlap check
    top_bounds: List[Tuple[str, float, float, float, float]] = []
    seen_ids = set()

    for child in root:
        tag = _local(child.tag)
        if tag == "g":
            gid = child.attrib.get("id", "")
            if not gid:
                report.errors.append("Top-level <g> missing id attribute")
            elif gid in seen_ids:
                report.errors.append(f"Duplicate id={gid!r}")
            seen_ids.add(gid)

            braw = child.attrib.get("data-pptx-bounds", "")
            if not braw:
                report.errors.append(f"Top-level <g id={gid!r}> missing data-pptx-bounds")
            else:
                bparts = braw.split()
                if len(bparts) != 4 or not all(NUM_RE.match(p) for p in bparts):
                    report.errors.append(f"Invalid data-pptx-bounds on <g id={gid!r}>: {braw!r}")
                else:
                    bx, by, bw, bh = [float(p) for p in bparts]
                    if bw <= 0 or bh <= 0:
                        report.errors.append(f"Non-positive bounds on <g id={gid!r}>")
                    top_bounds.append((gid, bx, by, bw, bh))

    # Pairwise overlap check (>1px tolerance per ppt-master contract)
    for i in range(len(top_bounds)):
        g1, x1, y1, w1, h1 = top_bounds[i]
        for j in range(i + 1, len(top_bounds)):
            g2, x2, y2, w2, h2 = top_bounds[j]
            ox = min(x1 + w1, x2 + w2) - max(x1, x2)
            oy = min(y1 + h1, y2 + h2) - max(y1, y2)
            if ox > 1.0 and oy > 1.0:
                report.errors.append(
                    f"Top-level bounds overlap between {g1!r} and {g2!r} ({ox:.1f}x{oy:.1f}px)"
                )

    # Full-tree audit
    for elem in root.iter():
        tag = _local(elem.tag)
        if tag.lower() in BANNED_TAGS:
            report.errors.append(f"Forbidden SVG element <{tag}>")

        if "class" in elem.attrib:
            report.errors.append(f"Forbidden class attribute on <{tag}>")
        if "style" in elem.attrib:
            report.warnings.append(f"Inline style attribute on <{tag}> (prefer direct XML attributes)")
        if "dominant-baseline" in elem.attrib:
            report.errors.append(f"Unsupported dominant-baseline attribute on <{tag}>")
        if tag == "g" and "opacity" in elem.attrib:
            report.warnings.append("Group opacity on <g> (prefer descendant fill-opacity/stroke-opacity)")

        for p_attr in ("fill", "stroke"):
            val = elem.attrib.get(p_attr)
            if val is None:
                continue
            if val == "none" or val.startswith("url(#"):
                continue
            if not HEX6_RE.match(val):
                report.errors.append(f"Non-canonical {p_attr}={val!r} on <{tag}> (require uppercase #RRGGBB)")

        if "font-size" in elem.attrib:
            fs = elem.attrib["font-size"]
            if not NUM_RE.match(fs):
                report.errors.append(f"Non-unitless font-size={fs!r} on <{tag}>")
            elif float(fs) < 12.0:
                report.errors.append(f"font-size={fs} < 12 minimum on <{tag}>")

        if "letter-spacing" in elem.attrib:
            ls = elem.attrib["letter-spacing"]
            if not NUM_RE.match(ls):
                report.errors.append(f"Non-unitless letter-spacing={ls!r} on <{tag}>")

    return report


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print("Usage: python validator.py <svg_file_or_dir> [...]")
        return 2
    targets: List[Path] = []
    for arg in argv[1:]:
        p = Path(arg)
        if p.is_dir():
            targets.extend(sorted(p.glob("*.svg")))
        else:
            targets.append(p)
    failed = 0
    for t in targets:
        rep = validate_svg_file(t)
        status = "PASS" if rep.ok else "FAIL"
        print(f"[{status}] {t.name} (errors={len(rep.errors)}, warnings={len(rep.warnings)})")
        for err in rep.errors:
            print(f"  ERROR: {err}")
        for warn in rep.warnings:
            print(f"  WARN:  {warn}")
        if not rep.ok:
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
