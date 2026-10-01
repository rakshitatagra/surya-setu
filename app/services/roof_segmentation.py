"""
Stage 1 - Roof-plane segmentation.

NOT YET IMPLEMENTED with a real model - this is Phase 5 in docs/ROADMAP.md.
Plan: Meta's SAM2 (Segment Anything Model), used zero-shot with a
bounding-box/point prompt on a nadir satellite tile fetched for the
given lat/lon, to get a working demo without any custom training data.
Published benchmarks for this task report 0.90-0.96 IoU.

mock=True (the default) returns a plausible dummy rooftop polygon in the
local metric frame (metres, roof origin at 0,0) so the rest of the
pipeline can be built, wired and tested end-to-end before the real model
is plugged in.
"""
from __future__ import annotations

from shapely.geometry import Polygon


def segment_roof(image_path: str, mock: bool = True) -> Polygon:
    if not mock:
        raise NotImplementedError(
            "Real roof segmentation (SAM2) is not wired up yet - see "
            "docs/ROADMAP.md Phase 5. Call with mock=True for pipeline "
            "development and testing."
        )
    # A plausible ~8m x 7m rectangular roof footprint (56 m^2, matching
    # the poster's own worked test case) as a stand-in.
    return Polygon([(0, 0), (8, 0), (8, 7), (0, 7)])
