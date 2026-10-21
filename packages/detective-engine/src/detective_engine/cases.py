"""Minimal deterministic validation of authored case identifiers.

This is an authoring-time check, not a second runtime source of truth.
"""

from collections.abc import Mapping


def validate_case_index(case: Mapping[str, object]) -> tuple[str, ...]:
    """Return human-readable errors for a small, versioned case index.

    This intentionally validates only case identity and evidence references.
    Deeper graph validation belongs to a later case-schema milestone.
    """
    errors: list[str] = []
    if case.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not isinstance(case.get("case_id"), str) or not case["case_id"].strip():
        errors.append("case_id must be a non-empty string")

    evidence = case.get("evidence")
    if not isinstance(evidence, list):
        errors.append("evidence must be a list")
        return tuple(errors)

    seen: set[str] = set()
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            errors.append(f"evidence[{index}] must be an object")
            continue
        identifier = item.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            errors.append(f"evidence[{index}].id must be a non-empty string")
        elif identifier in seen:
            errors.append(f"duplicate evidence id: {identifier}")
        else:
            seen.add(identifier)
    return tuple(errors)
