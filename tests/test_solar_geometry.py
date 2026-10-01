import pandas as pd
from shapely.geometry import Polygon

from app.services import solar_geometry

DELHI_LAT, DELHI_LON = 28.6139, 77.2090


def test_sun_higher_at_summer_noon_than_winter_noon():
    summer_noon = pd.Timestamp("2026-06-21 12:00", tz="Asia/Kolkata")
    winter_noon = pd.Timestamp("2026-12-21 12:00", tz="Asia/Kolkata")

    summer = solar_geometry.get_sun_position(DELHI_LAT, DELHI_LON, summer_noon)
    winter = solar_geometry.get_sun_position(DELHI_LAT, DELHI_LON, winter_noon)

    assert summer["elevation"] > winter["elevation"]
    # Delhi's latitude means even summer noon sun isn't quite overhead
    assert 60 < summer["elevation"] < 90
    assert 20 < winter["elevation"] < 55


def test_shadow_is_none_when_sun_below_horizon():
    obstacle = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    shadow = solar_geometry.cast_shadow(obstacle, height_m=1.5, sun_azimuth_deg=180, sun_elevation_deg=-5)
    assert shadow is None


def test_shadow_lengthens_as_sun_gets_lower():
    obstacle = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    high_sun_shadow = solar_geometry.cast_shadow(obstacle, 2.0, sun_azimuth_deg=180, sun_elevation_deg=70)
    low_sun_shadow = solar_geometry.cast_shadow(obstacle, 2.0, sun_azimuth_deg=180, sun_elevation_deg=20)

    # A lower sun casts a longer shadow -> a larger combined footprint
    assert low_sun_shadow.area > high_sun_shadow.area


def test_compute_shade_free_area_reduces_roof_area():
    roof = Polygon([(0, 0), (8, 0), (8, 7), (0, 7)])
    obstacles = [
        {"polygon": Polygon([(1, 5.5), (2, 5.5), (2, 6.5), (1, 6.5)]), "height_m": 1.2},
        {"polygon": Polygon([(5.5, 0.5), (7.5, 0.5), (7.5, 2.5), (5.5, 2.5)]), "height_m": 2.6},
    ]
    result = solar_geometry.compute_shade_free_area(roof, obstacles, DELHI_LAT, DELHI_LON, year=2026)

    assert result["hours_checked"] > 0
    assert result["shade_free_area_m2"] < result["roof_area_m2"]
    assert result["shade_free_area_m2"] > 0
