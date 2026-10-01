"""
Stage 2 - Obstruction detection (the research frontier).

NOT YET IMPLEMENTED with a real model - this is Phase 6 in docs/ROADMAP.md.
Plan: YOLOv8-seg (via the Ultralytics package), fine-tuned on a custom,
hand-labelled Indian-rooftop taxonomy (mumty, water tank, satellite dish,
vents, parapet) using CVAT or Label Studio for annotation. Published
work on this specific task reports ~0.40 IoU - this is genuinely hard,
which is exactly why the product design routes every prediction through
a three-tap human confirmation step rather than trusting the model alone.

mock=True (the default) returns a couple of plausible dummy obstacles
(a water tank and a mumty) with rough heights, positioned inside the
mock roof polygon from roof_segmentation.py, so the shadow-casting and
layout stages have something real to chew on during development.
"""
from __future__ import annotations

from shapely.geometry import Polygon


def detect_obstacles(image_path: str, mock: bool = True) -> list[dict]:
    if not mock:
        raise NotImplementedError(
            "Real obstacle detection (fine-tuned YOLOv8-seg) is not wired "
            "up yet - see docs/ROADMAP.md Phase 6. Call with mock=True for "
            "pipeline development and testing."
        )
    return [
        {
            "label": "water_tank",
            "polygon": Polygon([(1, 5.5), (2, 5.5), (2, 6.5), (1, 6.5)]),
            "height_m": 1.2,
            "confidence": 0.62,
        },
        {
            "label": "mumty",
            "polygon": Polygon([(5.5, 0.5), (7.5, 0.5), (7.5, 2.5), (5.5, 2.5)]),
            "height_m": 2.6,
            "confidence": 0.58,
        },
    ]
