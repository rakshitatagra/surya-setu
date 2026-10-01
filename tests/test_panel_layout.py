from shapely.geometry import Polygon

from app.services import panel_layout


def test_fit_panels_on_large_clear_roof():
    big_square = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    result = panel_layout.fit_panels(big_square)

    assert result["panel_count"] > 0
    for panel in result["panels"]:
        assert big_square.buffer(-0.5).contains(panel)


def test_fit_panels_on_tiny_roof_returns_zero():
    tiny = Polygon([(0, 0), (0.8, 0), (0.8, 0.8), (0, 0.8)])
    result = panel_layout.fit_panels(tiny)
    assert result["panel_count"] == 0


def test_estimate_system_capacity_kw():
    assert panel_layout.estimate_system_capacity_kw(5, panel_wattage_w=400) == 2.0
