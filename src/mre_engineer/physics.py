"""Small deterministic accounting tools. No kinetic, corrosion or risk model."""

import csv
import math
from pathlib import Path

from .evidence import EvidenceError

# F = N_A * e from the fixed SI constants (BIPM). Float representation is rounded.
FARADAY_C_PER_MOL = 96485.33212331002
# CIAAW abridged standard atomic weights (2024), used as approximate g/mol.
ATOMIC_MASS = {"O": 15.999, "Si": 28.085, "Fe": 55.845, "Mg": 24.305,
               "Ca": 40.078, "Al": 26.982, "Ti": 47.867, "Na": 22.990,
               "K": 39.098, "Mn": 54.938, "P": 30.974}
OXIDES = {"SiO2": ("Si", 1, 2), "FeO": ("Fe", 1, 1), "Fe2O3": ("Fe", 2, 3),
          "MgO": ("Mg", 1, 1), "CaO": ("Ca", 1, 1), "Al2O3": ("Al", 2, 3),
          "TiO2": ("Ti", 1, 2), "Na2O": ("Na", 2, 1), "K2O": ("K", 2, 1),
          "MnO": ("Mn", 1, 1), "P2O5": ("P", 2, 5)}
HEADERS = {"analysis_id", "material", "oxide", "value", "unit",
           "uncertainty_status", "source_id", "locator"}


def number(value, label, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EvidenceError(f"{label} must be a finite number")
    try:
        finite = math.isfinite(value)
    except OverflowError as exc:
        raise EvidenceError(f"{label} exceeds floating-point range") from exc
    if not finite or value < 0 or (positive and value == 0):
        raise EvidenceError(f"{label} must be {'positive' if positive else 'nonnegative'} and finite")
    return float(value)


def load_composition(path, source_ids):
    """Accept one source-linked analysis in the project's narrow CSV contract."""
    path = Path(path)
    if path.stat().st_size > 1024 * 1024:
        raise EvidenceError("Composition fixture exceeds 1 MB; use a reviewed subset")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        names = reader.fieldnames or []
        if len(names) != len(HEADERS) or set(names) != HEADERS:
            raise EvidenceError("Composition CSV headers must match the documented contract exactly")
        rows = []
        for raw in reader:
            if None in raw or any(v is None or not v.strip() for v in raw.values()):
                raise EvidenceError("Malformed composition row or missing provenance/value")
            row = {k: v.strip() for k, v in raw.items()}
            if row["unit"] != "wt_percent":
                raise EvidenceError("Only explicit oxide wt_percent is supported; no implicit conversions")
            if row["uncertainty_status"] != "unknown":
                raise EvidenceError("This CSV version supports unknown uncertainty only; do not discard supplied uncertainty")
            if row["source_id"] not in source_ids:
                raise EvidenceError(f"Unknown composition source: {row['source_id']}")
            if row["oxide"] not in OXIDES:
                raise EvidenceError(f"Unsupported/ambiguous oxide: {row['oxide']}; no inferred iron speciation")
            try:
                value = float(row["value"])
            except ValueError as exc:
                raise EvidenceError("Invalid oxide weight percentage") from exc
            row["value"] = number(value, "Oxide weight percentage")
            if row["value"] > 100:
                raise EvidenceError("Individual oxide percentage exceeds 100")
            rows.append(row)
            if len(rows) > len(OXIDES):
                raise EvidenceError("Too many rows for one supported analysis")
    if not rows:
        raise EvidenceError("Composition CSV is empty")
    for key in ("analysis_id", "material", "source_id", "locator"):
        if len({r[key] for r in rows}) != 1:
            raise EvidenceError(f"Mixed {key}: do not pool separate analyses or source bases")
    if len({r["oxide"] for r in rows}) != len(rows):
        raise EvidenceError("Duplicate oxide within one analysis")
    total = math.fsum(r["value"] for r in rows)
    if total <= 0 or total > 100 + 1e-8:
        raise EvidenceError("Oxide total must be above zero and no greater than 100; no silent renormalization")
    return rows


def oxygen_inventory(rows, batch_mass_g):
    """Inventory represented by listed oxides, not oxygen extraction yield."""
    mass = number(batch_mass_g, "Reference batch mass in g", positive=True)
    if not rows:
        raise EvidenceError("No validated composition rows supplied")
    seen = set()
    for row in rows:
        if row.get("oxide") not in OXIDES or row["oxide"] in seen:
            raise EvidenceError("Unsupported or duplicate oxide supplied to inventory")
        seen.add(row["oxide"])
        if row.get("unit") != "wt_percent":
            raise EvidenceError("Inventory requires explicit wt_percent")
        number(row.get("value"), "Oxide weight percentage")
    if len({r.get("analysis_id") for r in rows}) != 1:
        raise EvidenceError("Inventory cannot combine analyses")
    total_check = math.fsum(r["value"] for r in rows)
    if not 0 < total_check <= 100 + 1e-8:
        raise EvidenceError("Inventory requires an unnormalized positive total no greater than 100")
    components = []
    for row in rows:
        element, cations, oxygens = OXIDES[row["oxide"]]
        molar_mass = cations * ATOMIC_MASS[element] + oxygens * ATOMIC_MASS["O"]
        oxygen_fraction = oxygens * ATOMIC_MASS["O"] / molar_mass
        oxide_g = number(mass * row["value"] / 100, "Represented oxide mass")
        components.append({"oxide": row["oxide"], "wt_percent": row["value"],
                           "oxide_mass_g": oxide_g,
                           "oxygen_mass_fraction_in_oxide": oxygen_fraction,
                           "represented_oxygen_g": number(oxide_g * oxygen_fraction, "Oxygen mass"),
                           "source_id": row["source_id"], "locator": row["locator"]})
    total = math.fsum(r["value"] for r in rows)
    return {
        "tool": "oxygen_inventory", "status": "conditional-inventory-computed",
        "analysis_id": rows[0]["analysis_id"], "reference_batch_mass_g": mass,
        "mass_basis": "user-selected reference mass, not a measured reactor batch mass",
        "oxide_total_wt_percent": total, "unrepresented_wt_percent": max(0.0, 100 - total),
        "normalization_applied": False,
        "represented_oxygen_g": math.fsum(c["represented_oxygen_g"] for c in components),
        "components": components, "uncertainty": {"status": "unknown", "value": None},
        "limitations": ["Inventory within the listed oxide components, not recoverable yield",
                        "Unrepresented composition is not assumed oxygen-free",
                        "Source oxide/redox and weight-percent conventions retained",
                        "Approximate standard atomic weights; isotopic and measurement uncertainty not propagated"],
    }


def charge_oxygen_bound(current_a, duration_s, measured_oxygen_g=None):
    current = number(current_a, "Current in A", positive=True)
    duration = number(duration_s, "Electrolysis duration in s", positive=True)
    charge = number(current * duration, "Charge in C", positive=True)
    moles = charge / (4 * FARADAY_C_PER_MOL)
    theoretical_g = number(moles * (2 * ATOMIC_MASS["O"]), "Theoretical oxygen mass", positive=True)
    result = {
        "tool": "charge_oxygen_bound", "status": "conditional-charge-accounting-computed",
        "current_a": current, "duration_s": duration, "charge_c": charge,
        "ideal_oxygen_mol": moles, "ideal_oxygen_g": theoretical_g,
        "equations": ["Q = I * t (constant current assumption)", "n(O2) = Q / (4 F)", "m(O2) = n(O2) * M(O2)"],
        "faraday_c_per_mol": FARADAY_C_PER_MOL,
        "oxygen_molar_mass_g_per_mol": 2 * ATOMIC_MASS["O"],
        "limitations": ["Reported setpoint treated as constant; not integration of measured current",
                        "100 percent current allocation to the declared four-electron oxygen pathway",
                        "Collected oxygen is not necessarily total oxygen generated",
                        "No gas-flow conversion, calibration check, failure prediction or statistical uncertainty"],
    }
    if measured_oxygen_g is not None:
        observed = number(measured_oxygen_g, "Reported measured oxygen mass in g")
        ratio = number(observed / theoretical_g, "Apparent oxygen-to-charge ratio")
        result.update(reported_oxygen_g=observed, apparent_oxygen_to_charge_ratio=ratio,
                      ratio_exceeds_one=ratio > 1)
        if ratio > 1:
            result["status"] = "accounting-inconsistency-needs-review"
            result["limitations"].append("Ratio above one is not clipped; inspect units, boundaries and inputs")
    return result
