"""
Stage 6 - Techno-economics.

This module is deliberately plain Python with no AI in it - the whole
point of SURYA-SETU's financial layer is that it's deterministic, testable
arithmetic against real (or, for now, illustrative) tariff and subsidy
data, not a model's guess.

Core idea ("cancel the costliest units first"):
Indian DISCOM billing is slabbed - the more you consume in a month, the
higher the per-unit rate on your LAST units. Solar generation reduces your
total grid draw, and because slabs are cumulative, shrinking that total
always peels units off the TOP of the ladder first. So the correct saving
is (bill at baseline units) - (bill at baseline-minus-generation units),
computed on the real slab table - never generation x average rate.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


def load_json(path: Path) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def calculate_slab_bill(units: float, slabs: list[dict]) -> float:
    """
    Progressive, tax-bracket-style billing: each slab's rate applies only
    to the units that fall inside that slab, not to the whole bill.

    slabs: list of {"upto_units": int | None, "rate_per_unit": float},
    sorted ascending, with the last slab's "upto_units" = None meaning
    "everything above the previous slab's ceiling".
    """
    if units <= 0:
        return 0.0

    total = 0.0
    lower_bound = 0.0
    remaining = units

    for slab in slabs:
        upto = slab["upto_units"]
        rate = slab["rate_per_unit"]
        slab_width = (upto - lower_bound) if upto is not None else remaining

        units_in_slab = min(remaining, slab_width)
        if units_in_slab > 0:
            total += units_in_slab * rate
            remaining -= units_in_slab

        lower_bound = upto if upto is not None else lower_bound
        if remaining <= 0:
            break

    return round(total, 2)


def calculate_savings(baseline_units: float, generation_units: float, slabs: list[dict]) -> dict:
    """
    The headline calculation. Returns both the correct slab-aware saving
    AND the naive "generation x average rate" saving side by side, so you
    can show the gap between them (this is the 2.5x / 28% story on the
    poster - it's real, and it's specifically because slab billing is
    progressive, not because of any optimistic assumption).
    """
    net_grid_units = max(baseline_units - generation_units, 0)

    bill_before = calculate_slab_bill(baseline_units, slabs)
    bill_after = calculate_slab_bill(net_grid_units, slabs)
    savings_monthly = round(bill_before - bill_after, 2)

    naive_avg_rate = (bill_before / baseline_units) if baseline_units else 0.0
    offset_units = min(generation_units, baseline_units)
    naive_savings_monthly = round(offset_units * naive_avg_rate, 2)

    return {
        "net_grid_units": net_grid_units,
        "bill_before": bill_before,
        "bill_after": bill_after,
        "savings_monthly_slab_aware": savings_monthly,
        "savings_annual_slab_aware": round(savings_monthly * 12, 2),
        "savings_monthly_naive_average": naive_savings_monthly,
        "savings_annual_naive_average": round(naive_savings_monthly * 12, 2),
    }


def calculate_subsidy(capacity_kw: float, rules: dict, state: Optional[str] = None) -> float:
    """
    PM Surya Ghar central subsidy: Rs 30,000/kW for the first 2 kW, then
    Rs 18,000 for the 3rd kW, capped at Rs 78,000 for 3 kW and above.
    Optionally adds a state top-up if one is configured in subsidy_rules.json.
    """
    central = rules["central_subsidy"]
    capped_capacity = min(capacity_kw, central["max_capacity_kw_considered"])

    if capped_capacity <= 2:
        amount = central["rate_per_kw_first_2kw"] * capped_capacity
    else:
        amount = (
            central["rate_per_kw_first_2kw"] * 2
            + central["rate_per_kw_third_kw"] * (capped_capacity - 2)
        )

    if state:
        amount += rules.get("state_top_up", {}).get(state, 0)

    return round(amount, 2)


def calculate_payback(net_cost: float, annual_savings: float) -> Optional[float]:
    """
    Simple (undiscounted) payback in years. A discounted / Monte-Carlo
    version (sampling generation and tariff uncertainty) is a Phase-10
    upgrade noted in docs/ROADMAP.md - this v1 gives a single defensible
    number to validate the pipeline end to end first.
    """
    if annual_savings <= 0:
        return None
    return round(net_cost / annual_savings, 2)


def calculate_lcoe(
    net_cost: float,
    annual_om_cost: float,
    annual_generation_kwh: float,
    lifetime_years: int = 25,
    degradation_rate: float = 0.005,
    discount_rate: float = 0.0,
) -> Optional[float]:
    """
    Levelized Cost of Energy, in Rs/kWh:
        LCOE = (discounted lifetime cost) / (discounted lifetime generation)

    Generation each year is reduced by the panel degradation rate; both
    cost and generation streams are discounted back to present value if a
    discount_rate > 0 is supplied.
    """
    total_discounted_cost = net_cost
    total_discounted_energy = 0.0

    for year in range(1, lifetime_years + 1):
        generation = annual_generation_kwh * ((1 - degradation_rate) ** (year - 1))
        discount_factor = 1 / ((1 + discount_rate) ** year)
        total_discounted_cost += annual_om_cost * discount_factor
        total_discounted_energy += generation * discount_factor

    if total_discounted_energy <= 0:
        return None

    return round(total_discounted_cost / total_discounted_energy, 3)
