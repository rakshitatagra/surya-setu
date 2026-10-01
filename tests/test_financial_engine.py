from app.services import financial_engine

SLABS = [
    {"upto_units": 200, "rate_per_unit": 3.0},
    {"upto_units": 400, "rate_per_unit": 4.5},
    {"upto_units": 800, "rate_per_unit": 6.5},
    {"upto_units": None, "rate_per_unit": 8.0},
]

SUBSIDY_RULES = {
    "central_subsidy": {
        "rate_per_kw_first_2kw": 30000,
        "rate_per_kw_third_kw": 18000,
        "max_capacity_kw_considered": 3,
    },
    "state_top_up": {"DL": 0},
}


def test_slab_bill_matches_hand_calculation():
    # 500 units across 3 slabs: 200@3 + 200@4.5 + 100@6.5 = 600+900+650
    assert financial_engine.calculate_slab_bill(500, SLABS) == 2150.0


def test_slab_bill_zero_units():
    assert financial_engine.calculate_slab_bill(0, SLABS) == 0.0


def test_slab_bill_above_top_slab():
    # 1000 units: 200@3 + 200@4.5 + 400@6.5 + 200@8 = 600+900+2600+1600
    assert financial_engine.calculate_slab_bill(1000, SLABS) == 5700.0


def test_savings_reproduces_poster_worked_example():
    """
    The exact worked example from the poster/pitch: a Delhi household on
    500 units/month, solar generating 200 units/month. Slab-aware saving
    should land close to Rs 13,200/year; the naive average-rate method
    should land close to Rs 10,300/year - a ~28% gap, purely from slab
    progressivity, not optimism.
    """
    result = financial_engine.calculate_savings(500, 200, SLABS)

    assert result["net_grid_units"] == 300
    assert result["savings_annual_slab_aware"] == 13200.0
    assert 10200 <= result["savings_annual_naive_average"] <= 10400
    assert result["savings_annual_slab_aware"] > result["savings_annual_naive_average"]


def test_subsidy_tiers():
    assert financial_engine.calculate_subsidy(1, SUBSIDY_RULES) == 30000
    assert financial_engine.calculate_subsidy(2, SUBSIDY_RULES) == 60000
    assert financial_engine.calculate_subsidy(3, SUBSIDY_RULES) == 78000
    # capped - a 5kW system should get the same subsidy as a 3kW system
    assert financial_engine.calculate_subsidy(5, SUBSIDY_RULES) == 78000


def test_subsidy_with_state_top_up():
    rules_with_topup = {
        **SUBSIDY_RULES,
        "state_top_up": {"DL": 5000},
    }
    assert financial_engine.calculate_subsidy(2, rules_with_topup, state="DL") == 65000


def test_payback_years():
    assert financial_engine.calculate_payback(65000, 13200) == 4.92
    assert financial_engine.calculate_payback(65000, 0) is None


def test_lcoe_is_positive_and_reasonable():
    lcoe = financial_engine.calculate_lcoe(
        net_cost=65000, annual_om_cost=1500, annual_generation_kwh=3050
    )
    # Should land somewhere in a plausible Rs/kWh range for Indian RTS
    assert 1.0 < lcoe < 10.0
