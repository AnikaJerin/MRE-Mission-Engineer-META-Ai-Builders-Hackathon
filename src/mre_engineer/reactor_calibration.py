"""Temperature-dependent material property profiles for YSZ and Mo components.

NOT a calibrated digital twin of any specific reactor cell.
Arrhenius/linear fits are from published bulk material data; they have NOT been
tuned against measured resistance or temperature data from this experimental cell.
All outputs carry explicit scope and limitations fields.

Usage
-----
    from mre_engineer.reactor_calibration import calibration_profile, calibrated_scenario
    profile = calibration_profile()
    result  = calibrated_scenario(scenario_input_dict)
"""

import math
from .evidence import EvidenceError

# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------
_K_BOLTZMANN_eV = 8.617333e-5   # eV / K
_R_GAS = 8.314472                # J / (mol K)

# ---------------------------------------------------------------------------
# YSZ ionic conductivity  σ(T) = σ₀ · exp(−Eₐ / kT)
# ---------------------------------------------------------------------------
# Reference values from bulk polycrystalline 8YSZ measurements
# (Ivers-Tiffee et al. 2001; Badwal 1992; nominal Eₐ 0.95 eV).
# These are bulk material fits — not calibrated to this cell.
_YSZ_SIGMA0 = 7.20e2   # S/m  (pre-exponential, anchored to ~2 S/m at 1600 °C; Badwal 1992 / Ivers-Tiffee 2001)
_YSZ_EA_eV  = 0.95     # eV   (activation energy)
_YSZ_T_MIN_C = 900.0
_YSZ_T_MAX_C = 1800.0

# ---------------------------------------------------------------------------
# Mo electrical resistivity  ρ(T) = ρ₀ · (1 + α·(T − T₀))
# ---------------------------------------------------------------------------
# Reference: CRC Handbook; Lide 2004.  Valid 300–2600 K.
_MO_RHO0 = 5.2e-8    # Ω·m  at T₀ = 293 K
_MO_T0_K  = 293.0
_MO_ALPHA  = 4.9e-3   # K⁻¹  temperature coefficient

# ---------------------------------------------------------------------------
# Scope / limitations strings (shared across all outputs)
# ---------------------------------------------------------------------------
_SCOPE = (
    "Temperature-dependent material property estimates from published bulk data. "
    "Arrhenius fit for YSZ is from bulk polycrystalline 8YSZ (8 mol% Y₂O₃-ZrO₂); "
    "activation energy and pre-exponential have NOT been fitted to measured resistance "
    "data from this specific experimental cell."
)
_LIMITATIONS = [
    "YSZ grain-boundary and electrode contributions are not separated from bulk conductivity.",
    "Mo resistivity model is linear; valid only within documented temperature range (300-2600 K).",
    "Conductivity of molten YSZ above liquidus is not modelled.",
    "No calibration against measured current/resistance data from Yu 2025 cell.",
    "These profiles are inputs to scenario calculations, not validated hardware predictions.",
]


# ---------------------------------------------------------------------------
# Public material-property functions
# ---------------------------------------------------------------------------

def ysz_conductivity(temperature_C: float) -> float:
    """Return YSZ ionic conductivity in S/m using Arrhenius model.

    Parameters
    ----------
    temperature_C : float
        Temperature in degrees Celsius.  Valid range: 900–1800 °C.

    Returns
    -------
    float
        Conductivity σ in S/m.

    Raises
    ------
    EvidenceError
        If temperature is outside the modelled range or non-finite.
    """
    if not math.isfinite(temperature_C):
        raise EvidenceError("temperature_C must be a finite number")
    if not _YSZ_T_MIN_C <= temperature_C <= _YSZ_T_MAX_C:
        raise EvidenceError(
            f"temperature_C {temperature_C} is outside YSZ model range "
            f"({_YSZ_T_MIN_C}–{_YSZ_T_MAX_C} °C)"
        )
    T_K = temperature_C + 273.15
    return _YSZ_SIGMA0 * math.exp(-_YSZ_EA_eV / (_K_BOLTZMANN_eV * T_K))


def mo_resistivity(temperature_C: float) -> float:
    """Return Mo electrical resistivity in Ω·m using linear temperature model.

    Parameters
    ----------
    temperature_C : float
        Temperature in degrees Celsius.  Valid range: 20–2600 °C.

    Returns
    -------
    float
        Resistivity ρ in Ω·m.

    Raises
    ------
    EvidenceError
        If temperature is non-finite or outside the valid range.
    """
    if not math.isfinite(temperature_C):
        raise EvidenceError("temperature_C must be a finite number")
    T_K = temperature_C + 273.15
    T_MIN_K, T_MAX_K = 293.0, 2873.0
    if not T_MIN_K <= T_K <= T_MAX_K:
        raise EvidenceError(
            f"temperature_C {temperature_C} is outside Mo resistivity model range "
            f"(20–2600 °C)"
        )
    return _MO_RHO0 * (1.0 + _MO_ALPHA * (T_K - _MO_T0_K))


# ---------------------------------------------------------------------------
# Calibration profile
# ---------------------------------------------------------------------------

def calibration_profile() -> dict:
    """Return material property curves over the MRE operating temperature range.

    Returns a dict with temperature steps (1000–1700 °C in 50 °C increments)
    and corresponding YSZ conductivity and Mo resistivity values.

    Returns
    -------
    dict
        Keys: 'temperatures_C', 'ysz_conductivity_S_m', 'mo_resistivity_ohm_m',
        'source', 'scope', 'limitations'.
    """
    temperatures = list(range(1000, 1751, 50))
    ysz_vals = []
    mo_vals = []
    for t in temperatures:
        ysz_vals.append(round(ysz_conductivity(t), 6))
        mo_vals.append(round(mo_resistivity(t), 12))

    return {
        "temperatures_C": temperatures,
        "ysz_conductivity_S_m": ysz_vals,
        "mo_resistivity_ohm_m": mo_vals,
        "reference_values": {
            "ysz_at_1600C_S_m": round(ysz_conductivity(1600), 4),
            "mo_at_1600C_ohm_m": round(mo_resistivity(1600), 12),
        },
        "model_parameters": {
            "ysz_sigma0_S_m": _YSZ_SIGMA0,
            "ysz_activation_energy_eV": _YSZ_EA_eV,
            "mo_rho0_ohm_m": _MO_RHO0,
            "mo_alpha_per_K": _MO_ALPHA,
            "mo_reference_T_K": _MO_T0_K,
        },
        "source": "Bulk YSZ: Badwal 1992, Ivers-Tiffee 2001. Mo: CRC Handbook (Lide 2004).",
        "scope": _SCOPE,
        "limitations": _LIMITATIONS,
    }


# ---------------------------------------------------------------------------
# Calibrated scenario runner
# ---------------------------------------------------------------------------

def calibrated_scenario(raw: dict) -> dict:
    """Run a reactor scenario replacing user-supplied conductivity with T-dependent YSZ value.

    The conductivity_S_m field in the scenario input is overridden by the
    Arrhenius YSZ conductivity evaluated at the midpoint of the supplied inner
    and outer boundary temperatures.  All other scenario fields are passed
    through unchanged.

    Parameters
    ----------
    raw : dict
        Scenario input dict as accepted by reactor_field.simulate().
        Must contain 'inner_temperature_C' and 'outer_temperature_C'.

    Returns
    -------
    dict
        Same structure as reactor_field.simulate(), plus 'calibration' sub-dict
        describing the overridden conductivity value and its source.

    Raises
    ------
    EvidenceError
        If the scenario is invalid, or if midpoint temperature is outside
        the YSZ conductivity model range.
    """
    from .reactor_field import validate_scenario, simulate as _simulate

    # Validate to obtain clean inputs with correct types / ranges
    clean = validate_scenario(raw)

    # Compute midpoint temperature for conductivity evaluation
    T_inner = clean["inner_temperature_C"]
    T_outer = clean["outer_temperature_C"]
    T_mid = (T_inner + T_outer) / 2.0

    # Override conductivity with T-dependent YSZ value
    sigma_ysz = ysz_conductivity(T_mid)
    overridden = {**clean, "conductivity_S_m": sigma_ysz}

    # Run simulation with overridden conductivity
    result = _simulate(overridden)

    # Attach calibration metadata
    result["calibration"] = {
        "method": "ysz_arrhenius_bulk",
        "midpoint_temperature_C": T_mid,
        "overridden_conductivity_S_m": round(sigma_ysz, 6),
        "user_supplied_conductivity_S_m": raw.get("conductivity_S_m"),
        "ysz_sigma0_S_m": _YSZ_SIGMA0,
        "ysz_activation_energy_eV": _YSZ_EA_eV,
        "scope": _SCOPE,
        "limitations": _LIMITATIONS,
        "interpretation": (
            "Conductivity substituted from bulk YSZ Arrhenius fit. "
            "This is NOT a calibrated reconstruction of measured resistance values. "
            "Comparison with published resistance data requires independent fitting."
        ),
    }
    return result
