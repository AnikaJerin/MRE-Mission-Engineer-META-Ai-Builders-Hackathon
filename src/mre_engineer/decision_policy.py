"""Deterministic release policy, separate from raw model accuracy."""
from copy import deepcopy
from .evaluation import checked_packet, checklist, DECISION
from .agent_contracts import validate


def release_decision(packet, proposed):
    validate(proposed, DECISION)
    available = checked_packet({"packet": packet})
    required = checklist(available)
    effective = deepcopy(proposed)
    blocked = required["decision"] != "proceed_conditional_review"
    if blocked:
        for field in ("decision", "missing_inputs", "next_action", "why_this_action"):
            effective[field] = deepcopy(required[field])
    return {"raw_decision": deepcopy(proposed), "effective_decision": effective,
            "gate_applied": blocked, "decision_changed_by_code": proposed["decision"] != effective["decision"],
            "scope": "Deterministic input/readiness policy. A code correction is not Meta reasoning improvement or hardware clearance."}
