from typing import Dict, Any

# Production Bonus & FAB Table mappings for LIC Plans
BONUS_TABLES = {
    "LIC Jeevan Umang": {
        "reversionary_bonus_per_1000_per_year": 48.0,
        "fab_per_1000": 40.0
    },
    "LIC Bima Shree": {
        "reversionary_bonus_per_1000_per_year": 50.0,
        "fab_per_1000": 50.0
    },
    "LIC New Money Back Plan 20 Years": {
        "reversionary_bonus_per_1000_per_year": 42.0,
        "fab_per_1000": 35.0
    },
    "LIC Jeevan Labh": {
        "reversionary_bonus_per_1000_per_year": 47.0,
        "fab_per_1000": 45.0
    },
    "LIC Jeevan Utsav": {
        "reversionary_bonus_per_1000_per_year": 40.0,
        "fab_per_1000": 40.0
    },
    "LIC Amritbaal": {
        "reversionary_bonus_per_1000_per_year": 80.0,
        "fab_per_1000": 0.0
    },
    "LIC New Pension Plus": {
        "reversionary_bonus_per_1000_per_year": 45.0,
        "fab_per_1000": 30.0
    }
}

def calculate_maturity_benefit(
    policy_name: str,
    sum_assured: float,
    term: int,
    age: int
) -> Dict[str, Any]:
    """
    Deterministic Python calculation tool for LIC policy maturity payouts.
    Calculates Basic Sum Assured + Vested Simple Reversionary Bonuses + Final Additional Bonus (FAB).
    """
    # Canonicalize policy name
    matched_plan = None
    for plan_key in BONUS_TABLES.keys():
        if plan_key.lower() in policy_name.lower() or policy_name.lower() in plan_key.lower():
            matched_plan = plan_key
            break

    if not matched_plan:
        matched_plan = "LIC Jeevan Umang"  # Default fallback table if plan matches partially

    rates = BONUS_TABLES[matched_plan]

    base_sa = float(sum_assured)
    reversionary_bonus = (base_sa / 1000.0) * rates["reversionary_bonus_per_1000_per_year"] * float(term)
    fab = (base_sa / 1000.0) * rates["fab_per_1000"]
    total_maturity = base_sa + reversionary_bonus + fab

    return {
        "policy_name": matched_plan,
        "basic_sum_assured": base_sa,
        "term_years": term,
        "entry_age": age,
        "breakdown": {
            "basic_sum_assured": base_sa,
            "total_reversionary_bonus": reversionary_bonus,
            "final_additional_bonus": fab
        },
        "total_estimated_maturity_benefit": total_maturity
    }
