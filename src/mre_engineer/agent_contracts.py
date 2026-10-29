"""Narrow, locally validated Meta tool contracts; no model code execution."""
import json
import math
from jsonschema import Draft202012Validator
from .evidence import EvidenceError


def obj(props):
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


TEXT = {"type": "string", "minLength": 1, "maxLength": 1800}
REFS = {"type": "array", "items": {"type": "string", "minLength": 1, "maxLength": 100}, "minItems": 1, "maxItems": 12, "uniqueItems": True}
STRINGS = {"type": "array", "items": TEXT, "minItems": 1, "maxItems": 8}
PLAN = obj({
    "hypotheses": {"type": "array", "minItems": 2, "maxItems": 3, "items": obj({
        "label": TEXT, "explanation": TEXT, "evidence_refs": REFS,
        "discriminating_observation": TEXT})},
    "next_test": obj({
        "category": {"enum": ["gas-accounting-review", "current-trace-review", "post-test-material-characterization", "request-additional-evidence"]},
        "question": TEXT, "measurement": TEXT, "why_discriminates": TEXT,
        "evidence_refs": REFS, "prerequisites": STRINGS}),
    "decision_status": {"enum": ["draft_requires_engineer_review", "insufficient_evidence"]},
    "limitations": {"type": "array", "items": TEXT, "minItems": 2, "maxItems": 8},
})
CHALLENGE = obj({"weakness": TEXT, "why_it_matters": TEXT, "alternate_explanation": TEXT,
                 "evidence_refs": REFS, "requested_revision": TEXT})
CHECKS = {
    "check_charge_accounting": ("Recalculate the fixed historical case's charge/oxygen accounting using source-linked inputs; no invented measurements.", obj({})),
    "check_oxide_inventory": ("Calculate oxygen represented by listed oxides for an illustrative reference mass, not reactor yield.",
                              obj({"reference_mass_g": {"type": "number", "minimum": 1, "maximum": 1000}})),
    "check_measurement_readiness": ("Inspect the case's recorded missing inputs and their implications for interpreting oxygen collection. Does not invent data or diagnose a fault.", obj({})),
}


def definition(name):
    if name == "submit_plan":
        desc, schema = "Submit a structured, evidence-linked next-test DRAFT for qualified engineer review.", PLAN
    elif name == "submit_challenge":
        desc, schema = "Submit the strongest evidence-linked challenge after reviewing the tool result.", CHALLENGE
    else:
        desc, schema = CHECKS[name]
    return {"type": "function", "name": name, "description": desc, "parameters": schema}


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise EvidenceError("Duplicate model JSON key")
            result[key] = value
        return result
    def invalid(_):
        raise EvidenceError("Non-finite model JSON")
    def finite(value):
        number = float(value)
        if not math.isfinite(number):
            raise EvidenceError("Non-finite model number")
        return number
    if not isinstance(text, str) or len(text.encode()) > 24_000:
        raise EvidenceError("Invalid/oversized model JSON")
    try:
        return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid, parse_float=finite)
    except (ValueError, TypeError) as exc:
        raise EvidenceError("Model did not return valid strict JSON") from exc


def validate(data, schema):
    if next(Draft202012Validator(schema).iter_errors(data), None) is not None:
        raise EvidenceError("Model output violates the allowed schema; no action executed")
    return data


def parse_action(response, allowed):
    calls = [i for i in response.get("output", []) if isinstance(i, dict) and i.get("type") == "function_call"]
    if len(calls) != 1:
        raise EvidenceError("Expected one model-selected tool; no action selected or multiple actions returned")
    call = calls[0]
    name, call_id = call.get("name"), call.get("call_id")
    if name not in allowed or not isinstance(call_id, str) or not 1 <= len(call_id) <= 64:
        raise EvidenceError("Unsupported tool or invalid call identifier")
    arguments = validate(strict_json(call.get("arguments")), definition(name)["parameters"])
    return name, call_id, arguments


def structured_result(response, name, known_refs, tool_refs):
    calls = [i for i in response.get("output", []) if isinstance(i, dict) and i.get("type") == "function_call"]
    if calls:
        _, _, result = parse_action(response, {name})
    else:
        parts = [p["text"] for i in response.get("output", []) if isinstance(i, dict) and i.get("type") == "message"
                 for p in i.get("content", []) if isinstance(p, dict) and p.get("type") == "output_text" and isinstance(p.get("text"), str)]
        result = validate(strict_json("\n".join(parts)), definition(name)["parameters"])
    refs = []
    def collect(item):
        if isinstance(item, dict):
            for key, value in item.items():
                if key == "evidence_refs": refs.extend(value)
                else: collect(value)
        elif isinstance(item, list):
            for value in item: collect(value)
    collect(result)
    if not set(refs) <= set(known_refs) or not set(refs).intersection(tool_refs):
        raise EvidenceError("Unknown evidence citation or no actual tool evidence cited")
    if name == "submit_plan":
        labels = [h["label"] for h in result["hypotheses"]]
        if len(set(labels)) != len(labels):
            raise EvidenceError("Hypothesis labels must be distinct")
        if not set(result["next_test"]["evidence_refs"]).intersection(tool_refs):
            raise EvidenceError("Next-test draft must cite returned tool evidence")
    return result
