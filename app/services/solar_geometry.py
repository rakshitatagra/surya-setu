"""
Stage 3 - Height & shadow modelling (the geometry half).

No AI here either - sun position is computed exactly via pvlib's
implementation of the NREL Solar Position Algorithm, and shadow casting
is plain trigonometry + 2D polygon math (shapely). Height estimation
(the other half of Stage 3, from monocular depth) lives in a separate,
model-backed module once Phase 7 is wired up - see docs/ROADMAP.md.

Coordinate convention used throughout this module: roof and obstacle
polygons are in a LOCAL metric frame (x = metres east, y = metres north
of an arbitrary roof origin) - NOT lat/lon. lat/lon is only used to look
up where the sun is.
"""
from __future__ import annotations

import math
from datetime import datetime
from typing import Optional

import pandas as pd
import pvlib
from shapely.affinity import translate
from shapely.geometry import Polygon
from shapely.ops import unary_union


def get_sun_position(latitude: float, longitude: float, timestamp: pd.Timestamp) -> dict:
    """
    Exact sun position (NREL SPA via pvlib) for one timestamp.
    Returns azimuth (deg, clockwise from North) and apparent elevation
    (deg above horizon, atmospheric-refraction corrected).
    """
    solpos = pvlib.solarposition.get_solarposition(
        pd.DatetimeIndex([timestamp]), latitude, longitude
    )
    row = solpos.iloc[0]
    return {
        "azimuth": float(row["azimuth"]),
        "elevation": float(row["apparent_elevation"]),
    }


def worst_case_timestamps(latitude: float, longitude: float, year: Optional[int] = None,
                           start_hour: str = "09:00", end_hour: str = "15:00",
                           freq: str = "30min") -> pd.DatetimeIndex:
    """
    The design window the poster names explicitly: 21 December (winter
    solstice - the shortest day, lowest sun angle, longest shadows),
    09:00-15:00 local time, the hours that actually matter for generation.
    """
    if year is None:
        year = datetime.now().year
    return pd.date_range(
        f"{year}-12-21 {start_hour}",
        f"{year}-12-21 {end_hour}",
        freq=freq,
        tz="Asia/Kolkata",
    )


def cast_shadow(obstacle_polygon: Polygon, height_m: float,
                 sun_azimuth_deg: float, sun_elevation_deg: float) -> Optional[Polygon]:
    """
    Project one obstacle's shadow onto the roof plane for one sun position.

    shadow_length = height / tan(elevation)   [longer as the sun gets lower]
    shadow_direction = azimuth + 180 deg      [shadow falls AWAY from the sun]

    Simplification (documented, not hidden): this approximates the shadow
    as the convex hull of the obstacle footprint unioned with a copy of
    itself translated by the shadow vector - a good, fast approximation
    for roughly box-shaped rooftop obstacles (tanks, mumtys, vents).
    A full 3D silhouette projection is a v2 upgrade for irregular shapes.
    """
    if sun_elevation_deg <= 0:
        return None  # sun below horizon - no shadow to cast

    elevation_rad = math.radians(sun_elevation_deg)
    shadow_length = height_m / math.tan(elevation_rad)

    shadow_direction_deg = (sun_azimuth_deg + 180) % 360
    direction_rad = math.radians(shadow_direction_deg)

    # Compass-to-Cartesian: 0 deg = North = +y, 90 deg = East = +x
    dx = shadow_length * math.sin(direction_rad)
    dy = shadow_length * math.cos(direction_rad)

    translated = translate(obstacle_polygon, xoff=dx, yoff=dy)
    return obstacle_polygon.union(translated).convex_hull


def compute_shade_free_area(roof_polygon: Polygon, obstacles: list[dict],
                             latitude: float, longitude: float,
                             year: Optional[int] = None) -> dict:
    """
    Runs cast_shadow for every obstacle at every worst-case-window
    timestamp, and returns the part of the roof that is shadow-free at
    EVERY one of those timestamps - i.e. an obstacle's shadow at ANY
    checked hour removes that area from the usable result.

    obstacles: list of {"polygon": shapely Polygon, "height_m": float}
    """
    times = worst_case_timestamps(latitude, longitude, year)
    solpos = pvlib.solarposition.get_solarposition(times, latitude, longitude)

    usable = roof_polygon
    hours_checked = 0

    for _, row in solpos.iterrows():
        elevation = row["apparent_elevation"]
        if elevation <= 0:
            continue
        azimuth = row["azimuth"]
        hours_checked += 1

        hour_shadows = []
        for obs in obstacles:
            shadow = cast_shadow(obs["polygon"], obs["height_m"], azimuth, elevation)
            if shadow is not None:
                hour_shadows.append(shadow)

        if hour_shadows:
            shaded_this_hour = unary_union(hour_shadows)
            usable = usable.difference(shaded_this_hour)

    return {
        "shade_free_polygon": usable,
        "roof_area_m2": round(roof_polygon.area, 2),
        "shade_free_area_m2": round(usable.area, 2),
        "hours_checked": hours_checked,
    }
