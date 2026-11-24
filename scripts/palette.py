#!/usr/bin/env python3
"""Custom 2-3 theme-color palette engine with ppt-master spec parser.

Designed around user-supplied or ppt-master template colors (NO hardcoded preset
themes required). Given 2 or 3 hex theme colors plus an optional slide background
(opaque hex or "transparent"), derives a complete editorial token set with:
  - Uppercase 6-digit #RRGGBB colors only (ppt-master DrawingML compliant)
  - Calibrated lightness ramps, categorical series, and hero accent roles
  - WCAG contrast checks for typography and structural hairlines
  - Direct parser for ppt-master `design_spec.md` and `spec_lock.md`
"""

from __future__ import annotations

import colorsys
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

HEX_RE = re.compile(r"#([0-9A-Fa-f]{6})\b")
HEX3_RE = re.compile(r"^#([0-9A-Fa-f]{3})$")


def normalize_hex(color: str) -> str:
    """Normalize a hex color string to uppercase #RRGGBB."""
    c = color.strip()
    if not c.startswith("#"):
        c = "#" + c
    m3 = HEX3_RE.match(c)
    if m3:
        s = m3.group(1)
        c = f"#{s[0]*2}{s[1]*2}{s[2]*2}"
    m6 = re.match(r"^#([0-9A-Fa-f]{6})$", c)
    if not m6:
        raise ValueError(f"Invalid hex color: {color!r} (expected #RRGGBB)")
    return f"#{m6.group(1).upper()}"


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    h = normalize_hex(hex_color)[1:]
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb_to_hex(r: float, g: float, b: float) -> str:
    ri = max(0, min(255, int(round(r))))
    gi = max(0, min(255, int(round(g))))
    bi = max(0, min(255, int(round(b))))
    return f"#{ri:02X}{gi:02X}{bi:02X}"


def mix_hex(c1: str, c2: str, ratio_c2: float) -> str:
    """Linearly blend c1 toward c2 by ratio_c2 in [0, 1]."""
    t = max(0.0, min(1.0, float(ratio_c2)))
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return rgb_to_hex(
        r1 + (r2 - r1) * t,
        g1 + (g2 - g1) * t,
        b1 + (b2 - b1) * t,
    )


def relative_luminance(hex_color: str) -> float:
    """WCAG 2.1 relative luminance in [0, 1]."""
    r, g, b = [v / 255.0 for v in hex_to_rgb(hex_color)]

    def lin(u: float) -> float:
        return u / 12.92 if u <= 0.03928 else ((u + 0.055) / 1.055) ** 2.4

    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast_ratio(c1: str, c2: str) -> float:
    l1 = relative_luminance(c1)
    l2 = relative_luminance(c2)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def is_dark(hex_color: str) -> bool:
    return relative_luminance(hex_color) < 0.24


def adjust_lightness(hex_color: str, target_l: float, sat_scale: float = 1.0) -> str:
    """Shift HSL lightness to target_l in [0, 1] while preserving hue."""
    r, g, b = [v / 255.0 for v in hex_to_rgb(hex_color)]
    h, _l, s = colorsys.rgb_to_hls(r, g, b)
    s2 = max(0.0, min(1.0, s * sat_scale))
    l2 = max(0.04, min(0.96, target_l))
    r2, g2, b2 = colorsys.hls_to_rgb(h, l2, s2)
    return rgb_to_hex(r2 * 255, g2 * 255, b2 * 255)


def ensure_contrast(fg: str, bg: str, min_ratio: float = 4.5) -> str:
    """Adjust fg lightness toward dark or light extreme until contrast >= min_ratio."""
    fg = normalize_hex(fg)
    bg = normalize_hex(bg)
    if contrast_ratio(fg, bg) >= min_ratio:
        return fg
    target = "#FFFFFF" if is_dark(bg) else "#111111"
    for step in range(1, 21):
        cand = mix_hex(fg, target, step / 20.0)
        if contrast_ratio(cand, bg) >= min_ratio:
            return cand
    return target


def derive_third_color(c1: str, c2: str, bg: str) -> str:
    """When user provides 2 theme colors, derive a harmonious 3rd tone without
    introducing an unrelated rogue hue (interpolated muted bridge / tint)."""
    r1, g1, b1 = [v / 255.0 for v in hex_to_rgb(c1)]
    r2, g2, b2 = [v / 255.0 for v in hex_to_rgb(c2)]
    h1, l1, s1 = colorsys.rgb_to_hls(r1, g1, b1)
    h2, l2, s2 = colorsys.rgb_to_hls(r2, g2, b2)

    # If c1 is near-neutral (e.g. deep charcoal/navy) and c2 is chromatic,
    # create a lighter companion tint of c2; otherwise blend hues cleanly.
    if s1 < 0.18 or abs(h1 - h2) < 0.06:
        cand = mix_hex(c2, bg, 0.36) if not is_dark(bg) else mix_hex(c2, "#FFFFFF", 0.32)
    else:
        cand = mix_hex(c1, c2, 0.5)
        cand = mix_hex(cand, bg, 0.20)
    return ensure_contrast(cand, bg, min_ratio=2.4)


@dataclass(frozen=True)
class ThemePalette:
    """Complete editorial color token set derived from 2-3 custom theme colors."""

    # Base inputs
    colors: Tuple[str, ...]        # Original 2 or 3 theme colors
    bg: str                        # Slide/card surface hex (used for blending even if transparent)
    transparent: bool              # If True, omit background <rect>
    dark: bool                     # True when rendering on dark slide / dark card

    # Core theme roles (2-3 theme colors)
    c1: str                        # Primary theme color (main series / dominant data)
    c2: str                        # Secondary theme color (comparison / 2nd series / negative)
    c3: str                        # Accent / hero color (peak / leader / callout / 3rd series)

    # Typography & structural furniture (solid #RRGGBB for DrawingML fidelity)
    ink: str                       # Primary titles & key numbers
    label: str                     # Axis & category labels
    muted: str                     # Subtitles & secondary labels
    faint: str                     # Source line, fifth-unit dots, subtle ticks
    grid: str                      # Axes, baseline rules, ledger lines
    floor: str                     # Calendar barcode ticks, dashed guides
    quiet: str                     # Zero/empty cells, background tracks

    # Derived data scales
    ramp5: Tuple[str, str, str, str, str]          # Light -> heavy 5-step ordinal ramp
    ramp6: Tuple[str, str, str, str, str, str]     # Heavy -> light 6-step ranked bar ramp
    cat: Tuple[str, str, str, str, str, str]       # Up to 6 categorical series from 2-3 theme hues
    pos: str                                       # Positive / gain color
    neg: str                                       # Negative / loss color
    bead: str                                      # Connecting bead / hairline accent

    # Typography stack (ppt-master Office-safe default)
    font_family: str = "Arial, 'Microsoft YaHei', 'PingFang SC', sans-serif"

    def series_color(self, idx: int) -> str:
        return self.cat[idx % len(self.cat)]

    def ramp_color(self, norm: float) -> str:
        """Map norm in [0, 1] to the 5-step ordinal ramp."""
        n = max(0.0, min(1.0, norm))
        idx = min(4, int(n * 5))
        return self.ramp5[idx]


def build_palette(
    colors: Sequence[str],
    *,
    bg: str = "#FFFFFF",
    ink: Optional[str] = None,
    dark: Optional[bool] = None,
    font_family: Optional[str] = None,
) -> ThemePalette:
    """Build a ThemePalette from 2-3 custom theme colors (or 1 fallback).

    Parameters
    ----------
    colors:
        2 or 3 hex theme colors, ordered as [primary, secondary] or
        [primary, secondary, accent]. (1 color is also accepted and expanded
        into a monochromatic editorial ramp.)
    bg:
        Background hex color (e.g. '#FFFFFF', '#F7F2EB', '#0F172A') or
        'transparent' (defaults to light-mode contrast calibration against
        #FFFFFF unless dark=True).
    ink:
        Optional explicit text color hex. Auto-derived when omitted.
    dark:
        Force dark-card mode (e.g. L2 Dot Cascade). When True on a light bg,
        automatically synthesizes a deep dark surface from c1.
    font_family:
        Optional Office-safe font family stack.
    """
    if not colors:
        raise ValueError("At least 1 theme color (recommended 2-3) must be provided.")
    norm_colors = tuple(normalize_hex(c) for c in colors[:3])

    transparent = bg.strip().lower() in ("transparent", "none", "")
    raw_bg = "#FFFFFF" if transparent else normalize_hex(bg)

    if dark is True and not is_dark(raw_bg):
        # Synthesize a rich dark card surface tinted with the primary theme color
        # (echoing Lieflat Porcelain #081F5C / Palm #28311F / Mono #1C1C1A)
        surface_bg = mix_hex(norm_colors[0], "#0D1117", 0.72)
        if relative_luminance(surface_bg) > 0.08:
            surface_bg = adjust_lightness(norm_colors[0], 0.11, sat_scale=0.65)
        is_dark_mode = True
    elif dark is False:
        surface_bg = raw_bg
        is_dark_mode = False
    else:
        surface_bg = raw_bg
        is_dark_mode = is_dark(surface_bg)

    # Assign c1, c2, c3
    if len(norm_colors) == 1:
        c1_raw = norm_colors[0]
        c2_raw = mix_hex(c1_raw, "#FFFFFF" if is_dark_mode else surface_bg, 0.42)
        c3_raw = adjust_lightness(c1_raw, 0.68 if is_dark_mode else 0.34, sat_scale=1.15)
    elif len(norm_colors) == 2:
        c1_raw, c2_raw = norm_colors
        c3_raw = derive_third_color(c1_raw, c2_raw, surface_bg)
    else:
        c1_raw, c2_raw, c3_raw = norm_colors

    # Ensure each data color is readable on the actual surface
    c1 = ensure_contrast(c1_raw, surface_bg, min_ratio=3.0)
    c2 = ensure_contrast(c2_raw, surface_bg, min_ratio=2.8)
    c3 = ensure_contrast(c3_raw, surface_bg, min_ratio=3.0)

    # Ink & typography hierarchy
    # If dark=True synthesized a dark card from a light spec, discard a dark ink
    # inherited from the light template so dark cards always get crisp paper ink.
    if ink and (not is_dark_mode or not is_dark(normalize_hex(ink))):
        txt_ink = ensure_contrast(normalize_hex(ink), surface_bg, min_ratio=4.5)
    elif is_dark_mode:
        txt_ink = mix_hex("#F4F3EF", c1, 0.05)
    else:
        txt_ink = mix_hex("#18191B", c1, 0.14)
        txt_ink = ensure_contrast(txt_ink, surface_bg, min_ratio=7.0)

    # Structural furniture: pre-blended onto surface_bg so DrawingML renders
    # crisp solid #RRGGBB tones with zero alpha-stacking surprises.
    label = mix_hex(txt_ink, surface_bg, 0.24)
    muted = mix_hex(txt_ink, surface_bg, 0.44)
    faint = mix_hex(txt_ink, surface_bg, 0.62)
    floor = mix_hex(txt_ink, surface_bg, 0.72)
    grid = mix_hex(txt_ink, surface_bg, 0.82)
    quiet = mix_hex(txt_ink, surface_bg, 0.88)

    # 5-step ordinal ramp (light/quiet -> strong/peak)
    if is_dark_mode:
        ramp5 = (
            mix_hex(c1, surface_bg, 0.62),
            mix_hex(c1, surface_bg, 0.38),
            c1,
            mix_hex(c1, "#FFFFFF", 0.35),
            c3,
        )
        ramp6 = (
            c3,
            mix_hex(c1, "#FFFFFF", 0.32),
            c1,
            mix_hex(c1, c2, 0.45),
            mix_hex(c1, surface_bg, 0.34),
            mix_hex(c1, surface_bg, 0.54),
        )
    else:
        ramp5 = (
            mix_hex(c1, surface_bg, 0.76),
            mix_hex(c1, surface_bg, 0.52),
            mix_hex(c1, surface_bg, 0.24),
            c1,
            c3 if contrast_ratio(c3, c1) >= 1.25 else ensure_contrast(mix_hex(c1, "#000000", 0.32), surface_bg, 5.0),
        )
        ramp6 = (
            c1,
            mix_hex(c1, c2, 0.35) if len(norm_colors) >= 2 else mix_hex(c1, surface_bg, 0.16),
            c2,
            mix_hex(c2, surface_bg, 0.26),
            mix_hex(c1, surface_bg, 0.42),
            mix_hex(c1, surface_bg, 0.58),
        )

    # Categorical palette (strictly derived from the 2-3 theme colors + tints)
    tint1 = mix_hex(c1, surface_bg, 0.42)
    tint2 = mix_hex(c2, surface_bg, 0.42)
    tint3 = mix_hex(c3, surface_bg, 0.42)
    if len(norm_colors) == 2:
        cat = (c1, c2, tint1, tint2, c3, mix_hex(c1, surface_bg, 0.64))
    else:
        cat = (c1, c2, c3, tint1, tint2, tint3)

    # Positive / negative semantic pairing from user's theme colors
    pos = c1
    neg = c2 if len(norm_colors) >= 2 else mix_hex(c1, surface_bg, 0.48)
    bead = c2 if len(norm_colors) == 2 else c3

    return ThemePalette(
        colors=norm_colors,
        bg=surface_bg,
        transparent=transparent,
        dark=is_dark_mode,
        c1=c1,
        c2=c2,
        c3=c3,
        ink=txt_ink,
        label=label,
        muted=muted,
        faint=faint,
        grid=grid,
        floor=floor,
        quiet=quiet,
        ramp5=ramp5,
        ramp6=ramp6,
        cat=cat,
        pos=pos,
        neg=neg,
        bead=bead,
        font_family=font_family or "Arial, 'Microsoft YaHei', 'PingFang SC', sans-serif",
    )


def extract_palette_from_ppt_master(spec_path: str | Path) -> Dict[str, Any]:
    """Parse a ppt-master `design_spec.md` or `spec_lock.md` and return theme kwargs.

    Returns a dict with keys: `colors` (2-3 hex list), `bg`, optional `ink`,
    optional `font_family`, and `source_roles` (raw parsed role->hex mapping).
    """
    path = Path(spec_path)
    text = path.read_text(encoding="utf-8")
    roles: Dict[str, str] = {}
    font_family: Optional[str] = None

    # 1. YAML frontmatter primary_color
    fm_match = re.match(r"^---\s*\n(.*?)\n---", text, flags=re.S)
    if fm_match:
        for line in fm_match.group(1).splitlines():
            m = re.match(r"^\s*([A-Za-z0-9_-]+)\s*:\s*[\"']?(#[0-9A-Fa-f]{6})[\"']?", line)
            if m:
                roles[m.group(1).lower()] = normalize_hex(m.group(2))

    # 2. Markdown tables (design_spec.md Color Scheme & Typography tables)
    for line in text.splitlines():
        if "|" in line:
            cells = [c.strip().strip("`").strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 2:
                role_key = cells[0].lower().replace(" ", "_").replace("-", "_")
                hex_m = HEX_RE.search(cells[1])
                if hex_m and role_key not in ("role", "---", ""):
                    roles[role_key] = f"#{hex_m.group(1).upper()}"
                # Typography table: | body | `Arial, "Microsoft YaHei", sans-serif` | ...
                if role_key in ("body", "body_family", "font_family") and not font_family:
                    cand = cells[1].strip("`").strip()
                    if cand and not cand.startswith("#") and not cand.startswith("---"):
                        font_family = cand.replace('"', "'")

        # 3. Bullet lines (spec_lock.md `## colors` / `## typography`)
        bm = re.match(r"^\s*-\s*([A-Za-z0-9_ -]+?)\s*:\s*(.+?)\s*$", line)
        if bm:
            key = bm.group(1).strip().lower().replace(" ", "_").replace("-", "_")
            val = bm.group(2).strip()
            hex_m = HEX_RE.search(val)
            if hex_m:
                roles[key] = f"#{hex_m.group(1).upper()}"
            elif key in ("font_family", "body_family", "title_family") and not font_family:
                font_family = val.strip("`").replace('"', "'")

    # Select background & ink
    bg = (
        roles.get("bg")
        or roles.get("background")
        or roles.get("field")
        or roles.get("canvas")
        or "#FFFFFF"
    )
    ink = (
        roles.get("ink")
        or roles.get("neutral_dark")
        or roles.get("text")
        or roles.get("primary_text")
        or None
    )

    # Pick 2-3 semantic theme colors (excluding bg/surface/border/muted-text)
    exclude_roles = {
        "bg", "background", "field", "canvas", "surface", "card", "card_bg",
        "border", "divider", "muted_text", "secondary_text", "text", "primary_text",
        "ink", "neutral_dark", "neutral_light",
    }
    priority_keys = [
        "primary", "primary_color", "brand", "focus",
        "secondary", "secondary_color", "on_plan", "positive", "success",
        "accent", "accent_color", "highlight", "watch", "warning", "off_plan", "negative", "danger",
    ]

    picked: List[str] = []
    for k in priority_keys:
        val = roles.get(k)
        if val and val not in picked and val != bg:
            picked.append(val)
        if len(picked) == 3:
            break

    # Fallback: scan any remaining non-excluded role hexes
    if len(picked) < 2:
        for k, val in roles.items():
            if k not in exclude_roles and val not in picked and val != bg:
                picked.append(val)
            if len(picked) == 3:
                break

    # If a brand spec only had 1 color + neutral_dark (e.g. Anthropic), pair primary + neutral_dark
    if len(picked) == 1 and ink and ink != bg and ink not in picked:
        picked.append(ink)

    if not picked:
        raise ValueError(f"No theme colors found in ppt-master spec: {spec_path}")

    return {
        "colors": picked[:3],
        "bg": bg,
        "ink": ink,
        "font_family": font_family,
        "source_roles": roles,
    }
