"""Submission adapter for additive reactor extensions only."""
import os
from jsonschema import Draft202012Validator
from .agent_contracts import strict_json
from .evidence import EvidenceError
from .evaluation import SubmissionError, scrub

def parse_submission(response, name, schema, refs):
    items = response.get("output", [])
    calls = [i for i in items if isinstance(i, dict) and i.get("type") == "function_call"]
    if calls:
        if len(calls) != 1 or calls[0].get("name") != name:
            raise SubmissionError("Unexpected evaluation submission tool", [{"path": "/output", "rule": "submission_name"}])
        text = calls[0].get("arguments")
    else:
        text = "\n".join(p["text"] for i in items if isinstance(i, dict) and i.get("type") == "message"
                          for p in i.get("content", []) if isinstance(p, dict) and p.get("type") == "output_text" and isinstance(p.get("text"), str))
    key = os.environ.get("MODEL_API_KEY", "").strip()
    if key and isinstance(text, str) and key in text:
        raise SubmissionError("Reflected credential rejected", [{"path": "/output", "rule": "credential_reflection"}])
    try:
        decision = strict_json(text)
    except EvidenceError as exc:
        raise SubmissionError("Pilot output is not valid strict JSON", [{"path": "/", "rule": "strict_json"}]) from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(decision), key=lambda error: str(list(error.absolute_path)))
    if errors:
        diagnostics = [{"path": "/" + "/".join(map(str, error.absolute_path)), "rule": error.validator,
                        "message": scrub(error.message[:400])} for error in errors[:10]]
        location = diagnostics[0]
        raise SubmissionError(f"Pilot schema mismatch at {location['path']} ({location['rule']}); inspect recorded submission", diagnostics)
    if not set(decision.get("evidence_refs", [])) <= set(refs):
        raise SubmissionError("Unknown evaluation evidence reference", [{"path": "/evidence_refs", "rule": "known_reference"}])
    return decision

