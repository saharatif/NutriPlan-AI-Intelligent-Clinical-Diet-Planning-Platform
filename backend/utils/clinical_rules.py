"""
Shared clinical reference data used by both ocr_service and medical_profile_service.
Keeping these in one place prevents the two modules from diverging silently.
"""

CONDITION_ALIASES: dict[str, str] = {
    "high bp":             "hypertension",
    "htn":                 "hypertension",
    "hypertension":        "hypertension",
    "type ii diabetes":    "type 2 diabetes",
    "t2dm":                "type 2 diabetes",
    "type 2 diabetes":     "type 2 diabetes",
    "diabetes":            "diabetes",
    "high cholesterol":    "hyperlipidemia",
    "hyperlipidemia":      "hyperlipidemia",
    "ckd":                 "chronic kidney disease",
    "chronic kidney disease": "chronic kidney disease",
}

KNOWN_ALLERGENS: list[str] = [
    "milk", "dairy", "peanut", "peanuts",
    "egg", "eggs", "gluten", "wheat",
    "soy", "shellfish", "tree nut",
]
