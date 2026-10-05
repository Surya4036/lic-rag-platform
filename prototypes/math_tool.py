import json

def calculate_endowment_maturity(plan_name: str, sum_assured: float, term: int, age: int) -> dict:
    """
    A prototype tool representing the deterministic math engine for LIC policies.
    In a full application, the LLM will extract the parameters (plan, SA, term, age)
    from the user prompt, and pass them here.
    """
    
    # MOCK DATA: In production, these tables will be loaded from a database or JSON 
    # based on the parsed official PDFs.
    # Example rates for Jeevan Labh (Plan 936)
    mock_bonus_rates = {
        "Jeevan Labh": {
            "reversionary_bonus_per_1000_per_year": 50.0,
            "final_additional_bonus_per_1000": 20.0 # simplified
        }
    }
    
    if plan_name not in mock_bonus_rates:
        return {"error": f"Plan {plan_name} not supported or not found in tables."}
        
    rates = mock_bonus_rates[plan_name]
    
    # 1. Basic Sum Assured
    base = sum_assured
    
    # 2. Vested Simple Reversionary Bonus = (SA / 1000) * Bonus Rate * Term
    reversionary_bonus = (sum_assured / 1000) * rates["reversionary_bonus_per_1000_per_year"] * term
    
    # 3. Final Additional Bonus (FAB) = (SA / 1000) * FAB Rate
    fab = (sum_assured / 1000) * rates["final_additional_bonus_per_1000"]
    
    # Total Maturity
    total_maturity = base + reversionary_bonus + fab
    
    return {
        "plan": plan_name,
        "parameters": {
            "sum_assured": sum_assured,
            "term_years": term,
            "entry_age": age
        },
        "breakdown": {
            "basic_sum_assured": base,
            "total_reversionary_bonus": reversionary_bonus,
            "final_additional_bonus": fab
        },
        "total_estimated_maturity_benefit": total_maturity
    }

if __name__ == "__main__":
    print("--- LIC Math Engine Prototype ---")
    # Simulate LLM extracting intent: "I am 30 years old, want to invest in Jeevan Labh for 21 years with 5L sum assured"
    llm_extracted_params = {
        "plan_name": "Jeevan Labh",
        "sum_assured": 500000,
        "term": 21,
        "age": 30
    }
    
    print(f"Extracted Params from LLM: {llm_extracted_params}\n")
    
    # Call the deterministic tool
    result = calculate_endowment_maturity(**llm_extracted_params)
    
    print("Calculated Payout:")
    print(json.dumps(result, indent=2))
