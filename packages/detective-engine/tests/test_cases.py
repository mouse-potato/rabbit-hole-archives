from detective_engine import validate_case_index


def test_valid_minimal_case():
    case = {"schema_version": 1, "case_id": "demo", "evidence": [{"id": "letter"}]}
    assert validate_case_index(case) == ()


def test_missing_required_values():
    assert validate_case_index({}) == (
        "schema_version must be 1",
        "case_id must be a non-empty string",
        "evidence must be a list",
    )


def test_invalid_evidence_entries_and_duplicates():
    case = {"schema_version": 1, "case_id": "demo", "evidence": [
        {"id": "letter"}, {"id": "letter"}, {"id": " "}, "other"
    ]}
    assert validate_case_index(case) == (
        "duplicate evidence id: letter",
        "evidence[2].id must be a non-empty string",
        "evidence[3] must be an object",
    )


def test_case_id_rejects_whitespace_and_wrong_type():
    base = {"schema_version": 1, "evidence": []}
    for invalid in (" ", None, 123):
        assert "case_id must be a non-empty string" in validate_case_index(
            {**base, "case_id": invalid}
        )


def test_unsupported_schema_version():
    assert validate_case_index({"schema_version": 2, "case_id": "demo", "evidence": []}) == (
        "schema_version must be 1",
    )
