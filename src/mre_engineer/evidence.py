"""Strict local evidence validation, not scientific certification."""

import hashlib
import json
import math
from importlib.resources import files
from pathlib import Path

from jsonschema import Draft202012Validator


class EvidenceError(ValueError):
    pass


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise EvidenceError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_constant(value):
    raise EvidenceError(f"Non-finite JSON constant: {value}")


def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise EvidenceError("JSON number exceeds finite floating-point range")
    return number


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"),
                      object_pairs_hook=_pairs, parse_constant=_invalid_constant,
                      parse_float=_finite_float)


def validate_schema(data, name):
    schema = json.loads(files("mre_engineer").joinpath("schemas", name).read_text())
    errors = sorted(Draft202012Validator(schema).iter_errors(data),
                    key=lambda e: str(list(e.absolute_path)))
    if errors:
        detail = "; ".join(f"{'/'.join(map(str, e.absolute_path)) or '$'}: {e.message}"
                           for e in errors[:8])
        raise EvidenceError(detail)


def _unique(items, key, label):
    ids = [x[key] for x in items]
    if len(ids) != len(set(ids)):
        raise EvidenceError(f"Duplicate {label} IDs")


def validate_manifest(manifest):
    validate_schema(manifest, "source-manifest.schema.json")
    _unique(manifest["sources"], "id", "source")
    return {s["id"]: s for s in manifest["sources"]}


def validate_case(case, manifest):
    sources = validate_manifest(manifest)
    validate_schema(case, "case.schema.json")
    _unique(case["evidence"], "id", "evidence")
    _unique(case["missing_inputs"], "id", "missing-input")
    for item in case["evidence"]:
        if item["source_id"] not in sources:
            raise EvidenceError(f"Unknown source: {item['source_id']}")
        if item["kind"] == "quantity":
            v = item["value"]
            # Bounds describe the supported data fields, not reactor operating limits.
            field = item["field"]
            if field == "faradaic_efficiency" and not 0 <= v <= 1:
                raise EvidenceError("Faradaic efficiency must be a fraction between 0 and 1")
            if field != "faradaic_efficiency" and v <= 0:
                raise EvidenceError(f"{field} must be positive in this case format")
    return case


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
