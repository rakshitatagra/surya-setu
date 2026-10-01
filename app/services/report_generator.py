"""
Stage 7 - Delivery.

Assembles every earlier stage's output into one plain-language report
dict. Real i18n and a proper Monte-Carlo-derived P50/P90 band (per
docs/ROADMAP.md) are noted as TODOs - this v1 gives a simple +/- range
around the point estimate so the report shape is already P50/P90-shaped
and doesn't need restructuring later.
"""
from __future__ import annotations


def build_report(
    roof_area_m2: float,
    shade_free_area_m2: float,
    panel_count: int,
    system_capacity_kw: float,
    annual_generation_kwh: float,
    financials: dict,
    subsidy: float,
    system_cost_gross: float,
    uncertainty_pct: float = 0.15,
) -> dict:
    net_cost = round(system_cost_gross - subsidy, 2)

    return {
        "roof": {
            "gross_area_m2": roof_area_m2,
            "shade_free_area_m2": shade_free_area_m2,
            "usable_fraction_pct": round(100 * shade_free_area_m2 / roof_area_m2, 1)
            if roof_area_m2 else 0,
        },
        "system": {
            "panel_count": panel_count,
            "capacity_kw": system_capacity_kw,
        },
        "generation": {
            "annual_kwh_p50": annual_generation_kwh,
            "annual_kwh_p10_conservative": round(annual_generation_kwh * (1 - uncertainty_pct), 1),
            "annual_kwh_p90_optimistic": round(annual_generation_kwh * (1 + uncertainty_pct), 1),
            "note": "P10/P90 here is a placeholder +/-15% band, not yet a real "
                    "Monte Carlo sample over height/irradiance uncertainty - "
                    "see docs/ROADMAP.md Phase 10.",
        },
        "financials": {
            "system_cost_gross_rs": system_cost_gross,
            "subsidy_rs": subsidy,
            "net_cost_rs": net_cost,
            **financials,
        },
    }
