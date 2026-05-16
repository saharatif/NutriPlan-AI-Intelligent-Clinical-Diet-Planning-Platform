from services.ocr_service import OcrService


def test_parse_blood_markers_allergens_and_conditions() -> None:
    raw_text = """
    HbA1c: 8.1 % ref 4.0-5.6
    LDL Cholesterol: 160 mg/dL ref 0-100
    Vitamin D: 28 ng/mL ref 30-100
    Patient notes: high bp, allergy to milk and peanuts.
    """

    parsed = OcrService().parse_text(raw_text)

    assert len(parsed.blood_markers) == 3
    assert parsed.blood_markers[0].marker_name == "HbA1c"
    assert parsed.blood_markers[0].is_abnormal is True
    assert parsed.blood_markers[1].reference_range == "0-100"
    assert "milk" in parsed.allergens
    assert "peanuts" in parsed.allergens
    assert "hypertension" in parsed.conditions
