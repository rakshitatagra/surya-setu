"""
Ties Stages 1-7 together into one synchronous call.

This is deliberately synchronous for now (v1 / demo). Once Stage 2's
three-tap human confirmation step is wired into a real frontend, this
needs to become an async Celery chain with a pause point after Stage 2 -
see docs/ROADMAP.md Phase 8. Keeping the stage functions pure and
independent (as they are in app/services/) is exactly what makes that
migration straightforward later: this file is the only thing that
changes, not the stage logic itself.
"""
from __future__ import annotations

from typing import Optional

from app import config
from app.services import (
    financial_engine,
    obstacle_detection,
    panel_layout,
    report_generator,
    roof_segmentation,
    solar_geometry,
)


def run_assessment(
    latitude: float,
    longitude: float,
    monthly_units: float,
    state: Optional[str] = None,
    roof_image_path: Optional[str] = None,
    obstacle_image_path: Optional[str] = None,
    tilt_deg: float = 20,
    panel_wattage_w: float = 400,
    annual_generation_kwh_override: Optional[float] = None,
) -> dict:
    """
    annual_generation_kwh_override lets you skip the live NASA POWER call
    (e.g. in tests, or offline demos) by supplying a precomputed figure.
    Leave it None to run the real Stage 5 fetch (needs internet access).
    """
    # --- Stage 1: roof segmentation (mocked until Phase 5) ---
    roof_polygon = roof_segmentation.segment_roof(roof_image_path, mock=True)

    # --- Stage 2: obstacle detection (mocked until Phase 6) ---
    obstacles = obstacle_detection.detect_obstacles(obstacle_image_path, mock=True)

    # --- Stage 3: shadow geometry (real - pvlib + shapely) ---
    shade_result = solar_geometry.compute_shade_free_area(
        roof_polygon, obstacles, latitude, longitude
    )

    # --- Stage 4: panel layout (real - grid packer) ---
    layout = panel_layout.fit_panels(
        shade_result["shade_free_polygon"],
        panel_width_m=config.PANEL_WIDTH_M,
        panel_length_m=config.PANEL_LENGTH_M,
    )
    system_capacity_kw = panel_layout.estimate_system_capacity_kw(
        layout["panel_count"], panel_wattage_w
    )

    # --- Stage 5: yield simulation (real, needs internet unless overridden) ---
    if annual_generation_kwh_override is not None:
        annual_generation_kwh = annual_generation_kwh_override
    else:
        from app.services import yield_simulation  # imported lazily: only needs
        # requests/pvlib's irradiance chain when actually hitting the network
        yield_result = yield_simulation.estimate_annual_yield(
            latitude, longitude, system_capacity_kw, tilt_deg
        )
        annual_generation_kwh = yield_result["annual_generation_kwh"]

    # --- Stage 6: techno-economics (real) ---
    slabs = financial_engine.load_json(config.TARIFF_SLABS_PATH)["slabs"]
    subsidy_rules = financial_engine.load_json(config.SUBSIDY_RULES_PATH)
    generation_units_per_month = annual_generation_kwh / 12

    savings = financial_engine.calculate_savings(monthly_units, generation_units_per_month, slabs)
    subsidy = financial_engine.calculate_subsidy(system_capacity_kw, subsidy_rules, state)
    system_cost_gross = round(system_capacity_kw * config.DEFAULT_SYSTEM_COST_PER_KW, 2)
    net_cost = round(system_cost_gross - subsidy, 2)

    payback_years = financial_engine.calculate_payback(
        net_cost, savings["savings_annual_slab_aware"]
    )
    lcoe = financial_engine.calculate_lcoe(
        net_cost, annual_om_cost=1500, annual_generation_kwh=annual_generation_kwh
    )

    financials = {
        **savings,
        "payback_years": payback_years,
        "lcoe_rs_per_kwh": lcoe,
    }

    # --- Stage 7: report assembly (real) ---
    report = report_generator.build_report(
        roof_area_m2=shade_result["roof_area_m2"],
        shade_free_area_m2=shade_result["shade_free_area_m2"],
        panel_count=layout["panel_count"],
        system_capacity_kw=system_capacity_kw,
        annual_generation_kwh=annual_generation_kwh,
        financials=financials,
        subsidy=subsidy,
        system_cost_gross=system_cost_gross,
    )
    return report
