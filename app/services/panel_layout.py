"""
Stage 4 - Shade-free polygon & layout.

v1 implementation: a self-contained greedy grid packer (no external
dependency) - buffer the usable polygon inward by the parapet safety
setback, then tile panel-sized rectangles row by row, keeping only the
ones that fall fully inside the buffered polygon. Row spacing includes a
maintenance walkway gap.

This is intentionally simple and correct-if-suboptimal. The natural
upgrade (noted in docs/ROADMAP.md, Phase 3) is Google OR-Tools' CP-SAT
solver for a closer-to-optimal packing, and row pitch derived from the
winter sun altitude (reusing solar_geometry's worst-case elevation) so
one row doesn't shade the row behind it - both left as clearly marked
TODOs rather than silently faked.
"""
from __future__ import annotations

from shapely.geometry import Polygon, box


def fit_panels(
    usable_polygon: Polygon,
    panel_width_m: float = 1.0,
    panel_length_m: float = 1.7,
    row_gap_m: float = 0.5,
    col_gap_m: float = 0.3,
    edge_setback_m: float = 0.5,
) -> dict:
    """
    Returns panel_count, the list of panel rectangles (shapely boxes, in
    the same local metric frame as usable_polygon), and the buffered
    usable area actually available after the safety setback.
    """
    buffered = usable_polygon.buffer(-edge_setback_m)
    if buffered.is_empty or buffered.area <= 0:
        return {"panel_count": 0, "panels": [], "usable_area_after_setback_m2": 0.0}

    minx, miny, maxx, maxy = buffered.bounds
    panels: list[Polygon] = []

    y = miny
    while y + panel_length_m <= maxy:
        x = minx
        while x + panel_width_m <= maxx:
            candidate = box(x, y, x + panel_width_m, y + panel_length_m)
            if buffered.contains(candidate):
                panels.append(candidate)
            x += panel_width_m + col_gap_m
        y += panel_length_m + row_gap_m

    return {
        "panel_count": len(panels),
        "panels": panels,
        "usable_area_after_setback_m2": round(buffered.area, 2),
    }


def estimate_system_capacity_kw(panel_count: int, panel_wattage_w: float = 400) -> float:
    """Standard residential panel wattage default; override with real spec sheets."""
    return round((panel_count * panel_wattage_w) / 1000, 2)
