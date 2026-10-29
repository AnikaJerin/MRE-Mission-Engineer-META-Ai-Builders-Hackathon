"""Owner-run accounting report and read-only replay. Nothing runs on import."""

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .evidence import EvidenceError, read_json, sha256, validate_case, validate_manifest
from .physics import charge_oxygen_bound, load_composition, number, oxygen_inventory

DEFAULT_CASE = "cases/yu2025-1h.json"
DEFAULT_COMPOSITION = "cases/feedstocks/lhs1-yu2025.csv"
CODE_FILES = ["physics.py", "day2.py", "evidence.py"]


def run_directory(root, run_name):
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}", run_name):
        raise EvidenceError("Run name must be a short identifier without path separators")
    return Path(root) / "outputs/day2" / run_name


def input_hashes(root):
    root = Path(root)
    result = {name: sha256(root / name) for name in
              (DEFAULT_CASE, DEFAULT_COMPOSITION, "sources/manifest.json")}
    for name in CODE_FILES:
        result[f"code/{name}"] = sha256(Path(__file__).with_name(name))
    return result


def report_digest(report):
    content = {k: v for k, v in report.items() if k != "report_sha256"}
    return hashlib.sha256(json.dumps(content, sort_keys=True, allow_nan=False,
                                     separators=(",", ":")).encode()).hexdigest()


def build_report(root, reference_mass_g=100.0):
    root = Path(root)
    before = input_hashes(root)
    manifest = read_json(root / "sources/manifest.json")
    sources = validate_manifest(manifest)
    case = validate_case(read_json(root / DEFAULT_CASE), manifest)
    values = {}
    for item in case["evidence"]:
        if item["kind"] == "quantity":
            if item["field"] in values:
                raise EvidenceError("Ambiguous repeated numerical field in case")
            values[item["field"]] = item
    required = {"current", "duration", "oxygen_mass", "faradaic_efficiency"}
    if not required <= values.keys():
        raise EvidenceError("Historical accounting requires current, duration, oxygen mass and reported efficiency")
    rows = load_composition(root / DEFAULT_COMPOSITION, set(sources))
    inventory = oxygen_inventory(rows, reference_mass_g)
    charge = charge_oxygen_bound(values["current"]["value"], values["duration"]["value"],
                                 values["oxygen_mass"]["value"])
    charge["evidence_ids"] = [values[f]["id"] for f in ("current", "duration", "oxygen_mass")]
    comparison = {"status": "not-applicable", "scope": "No matching predeclared historical rounding policy"}
    if case["case_id"] == "yu2025-inverted-hollow-anode-1h":
        # Table 2 prints 0.070 g and integer percent. These intervals reflect printing
        # resolution only. They are NOT measurement uncertainty or confidence intervals.
        observed = values["oxygen_mass"]["value"]
        efficiency = values["faradaic_efficiency"]["value"]
        mass_half_step = 0.0005  # grams: half of a 0.001 g printed increment
        efficiency_half_step = 0.005  # fraction: half a percentage point
        ideal = charge["ideal_oxygen_g"]
        ratio_interval = [max(0.0, observed - mass_half_step) / ideal,
                          (observed + mass_half_step) / ideal]
        printed_interval = [max(0.0, efficiency - efficiency_half_step),
                            min(1.0, efficiency + efficiency_half_step)]
        consistent = max(ratio_interval[0], printed_interval[0]) <= min(ratio_interval[1], printed_interval[1])
        comparison = {
            "status": "rounding-compatible" if consistent else "rounding-mismatch-needs-review",
            "source_id": "yu2025-main", "locator": "Table 2, one-hour row",
            "reported_efficiency_fraction": efficiency,
            "computed_apparent_ratio": charge["apparent_oxygen_to_charge_ratio"],
            "oxygen_print_resolution_g": 0.001, "efficiency_print_resolution_fraction": 0.01,
            "ratio_interval_from_printed_oxygen": ratio_interval,
            "printed_efficiency_interval": printed_interval,
            "scope": "Arithmetic consistency under nearest-rounding and fixed setpoint assumptions; not independent prediction or statistical validation",
        }
    after = input_hashes(root)
    if before != after:
        raise EvidenceError("Inputs/code changed during accounting; rerun with stable files")
    report = {
        "schema_version": "day2-1.0", "status": "conditional-accounting-completed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "case_id": case["case_id"], "input_sha256": before,
        "reference_mass_g": number(reference_mass_g, "Reference mass", positive=True),
        "inventory": inventory, "charge": charge, "historical_comparison": comparison,
        "missing_inputs": case["missing_inputs"], "api_calls": 0, "network_calls": 0,
        "agent_run_ready": False,
        "constants_sources": ["https://www.bipm.org/en/measurement-units/",
                              "https://ciaaw.org/abridged-atomic-weights.htm"],
        "limits": ["No Meta investigation or next-test recommendation has run",
                   "Reference inventory mass is user-selected, not the experiment's measured batch mass",
                   "No raw current/gas trace reconstruction or gas calibration validation",
                   "Published efficiency and mass are related quantities, not independent ground truth",
                   "No recoverable-yield, corrosion, lifetime, failure-risk or significance claim"],
    }
    report["report_sha256"] = report_digest(report)
    return report


def save_report(root, run_name, reference_mass_g=100.0):
    target = run_directory(root, run_name)
    if target.exists():
        raise EvidenceError("Run already exists; select a new --run-name to preserve previous evidence")
    report = build_report(root, reference_mass_g)
    target.mkdir(parents=True, exist_ok=False)
    path = target / "report.json"
    path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return report, path


def load_saved_report(root, run_name):
    """Check saved evidence, without rerunning accounting on dashboard refresh."""
    path = run_directory(root, run_name) / "report.json"
    if not path.exists():
        return {"status": "not-run", "run_name": run_name}
    try:
        report = read_json(path)
        if not isinstance(report, dict) or report.get("schema_version") != "day2-1.0":
            raise EvidenceError("Unknown report version")
        if report.get("report_sha256") != report_digest(report):
            raise EvidenceError("Saved report contents changed")
        if report["input_sha256"] != input_hashes(root):
            return {"status": "stale", "run_name": run_name,
                    "reason": "Inputs or accounting code changed; generate a new run"}
        if not all(isinstance(report.get(k), dict) for k in ("inventory", "charge", "historical_comparison")):
            raise EvidenceError("Incomplete report")
        return {"status": "saved-accounting-available", "run_name": run_name, "report": report}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"status": "needs-review", "run_name": run_name, "reason": str(exc)}
