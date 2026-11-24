#!/usr/bin/env python3
"""Pure-static, ppt-master-canonical SVG builder.

Enforces ppt-master `shared-standards-core.md` and `svg-effects.md` by construction:
  - Strict XML escaping (raw Unicode typography, XML entities only for & < > " ')
  - Uppercase 6-digit #RRGGBB paint or lowercase 'none' (NEVER rgba())
  - Finite unitless numeric geometry & font-size >= 12
  - Zero <style>, class, <script>, <animate*>, <mask>, <title>, paint-order, dominant-baseline
  - Semantic top-level <g id="..." data-pptx-bounds="x y w h"> groups
  - Deterministic PRNG matching lieflat-charts `rnd(i, k)`
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from xml.sax.saxutils import escape as xml_escape

from palette import ThemePalette, normalize_hex

D2R = math.pi / 180.0


def rnd(i: int, k: int) -> float:
    """Deterministic pseudo-random in [0, 1), matching lieflat-charts `rnd(i, k)`."""
    return abs(((int(i) * 73856093) ^ (int(k) * 19349663)) % 1000) / 1000.0


def pol(cx: float, cy: float, r: float, deg: float) -> Tuple[float, float]:
    """Polar to Cartesian coordinates (degrees, 0° = 3 o'clock, -90° = 12 o'clock)."""
    rad = deg * D2R
    return cx + r * math.cos(rad), cy + r * math.sin(rad)


def fmt(val: float, digits: int = 2) -> str:
    """Format finite float cleanly without trailing fractional zeros or -0."""
    if not math.isfinite(val):
        raise ValueError(f"Non-finite SVG coordinate: {val}")
    rounded = round(val, digits)
    if rounded == 0:
        return "0"
    if digits <= 0:
        return str(int(round(rounded)))
    s = f"{rounded:.{digits}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s if s != "-0" else "0"


def escape_attr(val: str) -> str:
    return xml_escape(str(val), {'"': "&quot;"})


def escape_text(val: str) -> str:
    return xml_escape(str(val))


def clean_paint(val: Optional[str]) -> Optional[str]:
    if val is None:
        return None
    s = val.strip()
    if s.lower() == "none":
        return "none"
    if s.startswith("url(#"):
        return s
    return normalize_hex(s)


def format_number(val: float, prefix: str = "", suffix: str = "", decimals: Optional[int] = None) -> str:
    if decimals is not None:
        num = f"{val:,.{decimals}f}"
    elif abs(val - round(val)) < 1e-6:
        num = f"{int(round(val)):,}"
    else:
        num = f"{val:,.1f}"
    return f"{prefix}{num}{suffix}"


@dataclass
class FrameLayout:
    """Normalized canvas geometry for either full-slide (1280x720) or card mode."""

    width: float
    height: float
    pad_x: float
    pad_top: float
    pad_bottom: float
    title_size: float
    sub_size: float
    footer_size: float
    source_size: float
    header_y: float
    header_h: float
    chart_x: float
    chart_y: float
    chart_w: float
    chart_h: float
    footer_y: float
    footer_h: float
    mode: str

    @property
    def chart_right(self) -> float:
        return self.chart_x + self.chart_w

    @property
    def chart_bottom(self) -> float:
        return self.chart_y + self.chart_h

    @property
    def scale(self) -> float:
        """Relative visual scale compared to 1280x720 slide baseline."""
        return min(self.width / 1280.0, self.height / 720.0)


def compute_layout(
    mode: str = "slide",
    width: Optional[float] = None,
    height: Optional[float] = None,
    has_subtitle: bool = True,
    has_note: bool = True,
    has_source: bool = True,
) -> FrameLayout:
    """Compute non-overlapping header / chart-area / footer zones.

    - `slide` mode: 1280x720 native ppt-master 16:9 canvas.
    - `card` mode: default 620x460 (or custom WxH) sub-canvas for inserting
      into multi-column ppt-master slides.
    """
    m = mode.lower().strip()
    if m == "slide":
        w = float(width or 1280)
        h = float(height or 720)
        pad_x = round(w * 0.055)          # ~70px
        pad_top = round(h * 0.055)        # ~40px
        pad_bottom = round(h * 0.04)      # ~29px
        title_size = 30.0
        sub_size = 15.0
        footer_size = 12.0
        source_size = 12.0
        header_h = 44.0 + (28.0 if has_subtitle else 0.0)
        footer_h = (22.0 if has_note else 0.0) + (22.0 if has_source else 0.0)
        gap_top = 18.0
        gap_bot = 14.0
    else:
        w = float(width or 620)
        h = float(height or 460)
        pad_x = max(24.0, round(w * 0.048))
        pad_top = max(22.0, round(h * 0.048))
        pad_bottom = max(16.0, round(h * 0.035))
        title_size = 20.0
        sub_size = 12.5
        footer_size = 12.0
        source_size = 12.0
        header_h = 30.0 + (22.0 if has_subtitle else 0.0)
        footer_h = (18.0 if has_note else 0.0) + (18.0 if has_source else 0.0)
        gap_top = 12.0
        gap_bot = 10.0

    header_y = pad_top
    footer_y = h - pad_bottom - max(footer_h, 1.0)
    chart_y = header_y + header_h + gap_top
    chart_bottom = (footer_y - gap_bot) if footer_h > 0 else (h - pad_bottom)
    chart_h = max(120.0, chart_bottom - chart_y)
    chart_w = max(200.0, w - 2.0 * pad_x)

    return FrameLayout(
        width=w,
        height=h,
        pad_x=pad_x,
        pad_top=pad_top,
        pad_bottom=pad_bottom,
        title_size=title_size,
        sub_size=sub_size,
        footer_size=footer_size,
        source_size=source_size,
        header_y=header_y,
        header_h=header_h,
        chart_x=pad_x,
        chart_y=chart_y,
        chart_w=chart_w,
        chart_h=chart_h,
        footer_y=footer_y,
        footer_h=footer_h,
        mode=m,
    )


@dataclass
class SvgNode:
    tag: str
    attrs: Dict[str, str] = field(default_factory=dict)
    text: Optional[str] = None
    children: List[Any] = field(default_factory=list)  # SvgNode or raw comment string

    def to_xml(self, indent: int = 0) -> str:
        pad = "  " * indent
        attr_str = "".join(f' {k}="{escape_attr(v)}"' for k, v in self.attrs.items())
        if not self.children and self.text is None:
            return f"{pad}<{self.tag}{attr_str}/>"
        if not self.children and self.text is not None:
            return f"{pad}<{self.tag}{attr_str}>{escape_text(self.text)}</{self.tag}>"
        lines = [f"{pad}<{self.tag}{attr_str}>"]
        if self.text is not None:
            lines.append(f"{pad}  {escape_text(self.text)}")
        for child in self.children:
            if isinstance(child, str):
                lines.append(f"{pad}  <!-- {child} -->")
            else:
                lines.append(child.to_xml(indent + 1))
        lines.append(f"{pad}</{self.tag}>")
        return "\n".join(lines)


class SvgCanvas:
    """ppt-master canonical static SVG document builder."""

    def __init__(self, layout: FrameLayout, palette: ThemePalette, chart_id: str = "chart", lang: str = "zh-CN"):
        self.layout = layout
        self.palette = palette
        self.chart_id = chart_id
        self.root_attrs: Dict[str, str] = {
            "xmlns": "http://www.w3.org/2000/svg",
            "lang": lang,
            "viewBox": f"0 0 {fmt(layout.width, 0)} {fmt(layout.height, 0)}",
            "width": fmt(layout.width, 0),
            "height": fmt(layout.height, 0),
            "font-family": palette.font_family,
        }
        if layout.mode == "slide":
            self.root_attrs["data-pptx-page-role"] = "content"

        self.root = SvgNode("svg", self.root_attrs)

        # Full-canvas solid background rect (promoted to native p:bg by ppt-master)
        if not palette.transparent:
            self.root.children.append(
                SvgNode(
                    "rect",
                    {
                        "id": "slide-bg",
                        "data-pptx-role": "background",
                        "x": "0",
                        "y": "0",
                        "width": fmt(layout.width, 0),
                        "height": fmt(layout.height, 0),
                        "fill": palette.bg,
                    },
                )
            )

    def add_group(
        self,
        parent: Optional[SvgNode],
        gid: str,
        bounds: Optional[Tuple[float, float, float, float]] = None,
        extra_attrs: Optional[Dict[str, str]] = None,
    ) -> SvgNode:
        attrs: Dict[str, str] = {"id": gid}
        if bounds is not None:
            bx, by, bw, bh = bounds
            attrs["data-pptx-bounds"] = f"{fmt(bx)} {fmt(by)} {fmt(bw)} {fmt(bh)}"
        if extra_attrs:
            attrs.update(extra_attrs)
        node = SvgNode("g", attrs)
        (parent or self.root).children.append(node)
        return node

    def add_comment(self, parent: SvgNode, text: str) -> None:
        safe = text.replace("--", "—")
        parent.children.append(safe)

    def add_rect(
        self,
        parent: SvgNode,
        x: float,
        y: float,
        width: float,
        height: float,
        *,
        fill: Optional[str] = None,
        fill_opacity: Optional[float] = None,
        stroke: Optional[str] = None,
        stroke_width: Optional[float] = None,
        stroke_opacity: Optional[float] = None,
        rx: Optional[float] = None,
        ry: Optional[float] = None,
        extra: Optional[Dict[str, str]] = None,
    ) -> SvgNode:
        attrs: Dict[str, str] = {
            "x": fmt(x),
            "y": fmt(y),
            "width": fmt(max(0.0, width)),
            "height": fmt(max(0.0, height)),
        }
        if rx is not None and rx > 0:
            attrs["rx"] = fmt(rx)
            attrs["ry"] = fmt(ry if ry is not None else rx)
        self._apply_paint(attrs, fill, fill_opacity, stroke, stroke_width, stroke_opacity)
        if extra:
            attrs.update(extra)
        node = SvgNode("rect", attrs)
        parent.children.append(node)
        return node

    def add_line(
        self,
        parent: SvgNode,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        stroke: str,
        stroke_width: float = 1.2,
        stroke_opacity: Optional[float] = None,
        stroke_dasharray: Optional[str] = None,
        stroke_linecap: Optional[str] = None,
    ) -> SvgNode:
        attrs: Dict[str, str] = {
            "x1": fmt(x1),
            "y1": fmt(y1),
            "x2": fmt(x2),
            "y2": fmt(y2),
            "stroke": clean_paint(stroke) or "none",
            "stroke-width": fmt(stroke_width),
        }
        if stroke_opacity is not None and stroke_opacity < 0.999:
            attrs["stroke-opacity"] = fmt(stroke_opacity, 3)
        if stroke_dasharray:
            attrs["stroke-dasharray"] = stroke_dasharray
        if stroke_linecap:
            attrs["stroke-linecap"] = stroke_linecap
        node = SvgNode("line", attrs)
        parent.children.append(node)
        return node

    def add_circle(
        self,
        parent: SvgNode,
        cx: float,
        cy: float,
        r: float,
        *,
        fill: Optional[str] = None,
        fill_opacity: Optional[float] = None,
        stroke: Optional[str] = None,
        stroke_width: Optional[float] = None,
        stroke_opacity: Optional[float] = None,
        stroke_dasharray: Optional[str] = None,
    ) -> SvgNode:
        attrs: Dict[str, str] = {
            "cx": fmt(cx),
            "cy": fmt(cy),
            "r": fmt(max(0.2, r)),
        }
        self._apply_paint(attrs, fill, fill_opacity, stroke, stroke_width, stroke_opacity)
        if stroke_dasharray:
            attrs["stroke-dasharray"] = stroke_dasharray
        node = SvgNode("circle", attrs)
        parent.children.append(node)
        return node

    def add_path(
        self,
        parent: SvgNode,
        d: str,
        *,
        fill: Optional[str] = "none",
        fill_opacity: Optional[float] = None,
        stroke: Optional[str] = None,
        stroke_width: Optional[float] = None,
        stroke_opacity: Optional[float] = None,
        stroke_dasharray: Optional[str] = None,
        stroke_linecap: Optional[str] = None,
        stroke_linejoin: Optional[str] = None,
    ) -> SvgNode:
        attrs: Dict[str, str] = {"d": d}
        self._apply_paint(attrs, fill, fill_opacity, stroke, stroke_width, stroke_opacity)
        if stroke_dasharray:
            attrs["stroke-dasharray"] = stroke_dasharray
        if stroke_linecap:
            attrs["stroke-linecap"] = stroke_linecap
        if stroke_linejoin:
            attrs["stroke-linejoin"] = stroke_linejoin
        node = SvgNode("path", attrs)
        parent.children.append(node)
        return node

    def add_text(
        self,
        parent: SvgNode,
        x: float,
        y: float,
        content: str,
        *,
        font_size: float = 14.0,
        font_weight: Optional[str | int] = None,
        font_style: Optional[str] = None,
        fill: Optional[str] = None,
        fill_opacity: Optional[float] = None,
        text_anchor: Optional[str] = None,
        letter_spacing: Optional[float] = None,
        rotate: Optional[Tuple[float, float, float]] = None,
    ) -> SvgNode:
        # Enforce ppt-master minimum readable text size (>= 12)
        safe_size = max(12.0, float(font_size))
        attrs: Dict[str, str] = {
            "x": fmt(x),
            "y": fmt(y),
            "font-size": fmt(safe_size, 1),
        }
        if font_weight is not None:
            attrs["font-weight"] = str(font_weight)
        if font_style:
            attrs["font-style"] = font_style
        if fill is not None:
            attrs["fill"] = clean_paint(fill) or self.palette.ink
        if fill_opacity is not None and fill_opacity < 0.999:
            attrs["fill-opacity"] = fmt(fill_opacity, 3)
        if text_anchor:
            attrs["text-anchor"] = text_anchor
        # Skip positive letter-spacing on CJK strings per ppt-master §6.7
        if letter_spacing is not None and abs(letter_spacing) > 1e-4:
            if not _contains_cjk(content):
                attrs["letter-spacing"] = fmt(letter_spacing, 2)
        if rotate is not None:
            ang, rx, ry = rotate
            attrs["transform"] = f"rotate({fmt(ang, 1)} {fmt(rx)} {fmt(ry)})"
        node = SvgNode("text", attrs, text=str(content))
        parent.children.append(node)
        return node

    def add_header(self, title: str, subtitle: str = "") -> SvgNode:
        ly = self.layout
        pal = self.palette
        hdr = self.add_group(
            self.root,
            "header",
            bounds=(ly.pad_x, ly.header_y, ly.chart_w, ly.header_h),
        )
        title_y = ly.header_y + ly.title_size * 0.95
        self.add_text(
            hdr,
            ly.pad_x,
            title_y,
            title,
            font_size=ly.title_size,
            font_weight=700,
            fill=pal.ink,
        )
        if subtitle:
            sub_y = title_y + ly.sub_size * 1.65
            self.add_text(
                hdr,
                ly.pad_x,
                sub_y,
                subtitle,
                font_size=ly.sub_size,
                font_weight=400,
                fill=pal.muted,
            )
        return hdr

    def add_footer(self, unit_note: str = "", source: str = "") -> Optional[SvgNode]:
        if not unit_note and not source:
            return None
        ly = self.layout
        pal = self.palette
        ftr = self.add_group(
            self.root,
            "footer",
            bounds=(ly.pad_x, ly.footer_y, ly.chart_w, ly.footer_h),
        )
        cur_y = ly.footer_y + ly.footer_size * 1.05
        if unit_note:
            self.add_text(
                ftr,
                ly.width / 2.0,
                cur_y,
                unit_note,
                font_size=ly.footer_size,
                font_weight=600,
                fill=pal.muted,
                text_anchor="middle",
                letter_spacing=1.1,
            )
            cur_y += ly.footer_size * 1.65
        if source:
            self.add_text(
                ftr,
                ly.pad_x,
                cur_y,
                source,
                font_size=ly.source_size,
                font_weight=500,
                fill=pal.faint,
                letter_spacing=0.9,
            )
        return ftr

    def add_chart_area(self) -> Tuple[SvgNode, SvgNode]:
        """Create top-level chart wrapper + inner chartArea matching ppt-master conventions."""
        ly = self.layout
        outer = self.add_group(
            self.root,
            self.chart_id,
            bounds=(ly.chart_x, ly.chart_y, ly.chart_w, ly.chart_h),
        )
        inner = self.add_group(outer, f"{self.chart_id}-chartArea")
        return outer, inner

    def to_string(self) -> str:
        return self.root.to_xml(0) + "\n"

    @staticmethod
    def _apply_paint(
        attrs: Dict[str, str],
        fill: Optional[str],
        fill_opacity: Optional[float],
        stroke: Optional[str],
        stroke_width: Optional[float],
        stroke_opacity: Optional[float],
    ) -> None:
        if fill is not None:
            attrs["fill"] = clean_paint(fill) or "none"
        if fill_opacity is not None and fill_opacity < 0.999:
            attrs["fill-opacity"] = fmt(fill_opacity, 3)
        if stroke is not None:
            attrs["stroke"] = clean_paint(stroke) or "none"
        if stroke_width is not None:
            attrs["stroke-width"] = fmt(stroke_width)
        if stroke_opacity is not None and stroke_opacity < 0.999:
            attrs["stroke-opacity"] = fmt(stroke_opacity, 3)


def _contains_cjk(s: str) -> bool:
    for ch in s:
        code = ord(ch)
        if (
            0x4E00 <= code <= 0x9FFF
            or 0x3400 <= code <= 0x4DBF
            or 0x3000 <= code <= 0x303F
            or 0xFF00 <= code <= 0xFFEF
        ):
            return True
    return False


def estimate_text_width(s: str, font_size: float) -> float:
    """Estimate rendered text width in SVG px with headroom for CJK & Latin."""
    total = 0.0
    for ch in str(s):
        code = ord(ch)
        if (
            0x4E00 <= code <= 0x9FFF
            or 0x3400 <= code <= 0x4DBF
            or 0x3000 <= code <= 0x303F
            or 0xFF00 <= code <= 0xFFEF
        ):
            total += font_size * 1.12
        elif ch.isupper():
            total += font_size * 0.72
        else:
            total += font_size * 0.58
    return total
