"""Corrosion, crack initiation, and component lifetime prediction models.

All outputs are conditional extrapolations from published degradation laws
applied to generic material classes.  They are NOT calibrated against measured
wear or cracking data from this specific experimental cell.

Models implemented
------------------
- Linear degradation:    loss(t) = rate · t
- Parabolic degradation: loss(t) = k · √t     (Wagner oxidation / diffusion limit)
- Arrhenius rate:        rate(T) = A · exp(−Q / R / T)
- Coffin-Manson fatigue: Nf = C · (ΔT)^(−m)  (cycles to crack initiation)
- Thermal stress:        σ = E · α · ΔT
- Lifetime prediction:   remaining life estimate with uncertainty bounds

Usage
-----
    from mre_engineer.reactor_degradation import (
        linear_degradation, parabolic_degradation,
        arrhenius_rate, lifetime_prediction, model_catalog,
    )
"""

import math
from .evidence import EvidenceError

# ---------------------------------------------------------------------------
# Shared scope / limitations
# ---------------------------------------------------------------------------
_SCOPE = (
    "Conditional extrapolation using published corrosion/fatigue law forms. "
    "Model parameters are generic defaults for YSZ/Mo/Al₂O₃ material classes; "
    "they have NOT been fitted to measured wear data from this experimental cell."
)
_LIMITATIONS = [
    "Linear model assumes constant corrosion rate; not valid if kinetics change over time.",
    "Parabolic model assumes diffusion-limited oxidation (Wagner 1933); may not apply to all MRE components.",
    "Arrhenius rate uses generic activation energy; actual Q varies with environment and microstructure.",
    "Coffin-Manson parameters C and m are user-supplied; defaults are illustrative, not experimentally validated.",
    "Thermal stress model ignores creep, multiaxial stress, and surface finish effects.",
    "Lifetime bounds use a fixed uncertainty percentage; real scatter may be larger.",
    "No measured degradation data from this cell is available for model validation.",
]

_R_GAS = 8.314472  # J / (mol K)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _check_positive_finite(value: float, name: str) -> float:
    """Raise EvidenceError if value is not a positive finite number."""
    if not isinstance(value, (int, float)):
        raise EvidenceError(f"{name} must be a number")
    v = float(value)
    if not math.isfinite(v):
        raise EvidenceError(f"{name} must be finite")
    if v <= 0:
        raise EvidenceError(f"{name} must be positive (got {v})")
    return v


def _check_nonneg_finite(value: float, name: str) -> float:
    """Raise EvidenceError if value is not a non-negative finite number."""
    if not isinstance(value, (int, float)):
        raise EvidenceError(f"{name} must be a number")
    v = float(value)
    if not math.isfinite(v):
        raise EvidenceError(f"{name} must be finite")
    if v < 0:
        raise EvidenceError(f"{name} must be non-negative (got {v})")
    return v


# ---------------------------------------------------------------------------
# Individual degradation models
# ---------------------------------------------------------------------------

def linear_degradation(
    rate_um_h: float,
    horizon_h: float,
    initial_thickness_um: float,
) -> dict:
    """Compute linear corrosion loss over time.

    loss(t) = rate · t

    Parameters
    ----------
    rate_um_h : float
        Corrosion/wear rate in µm per hour.  Must be positive.
    horizon_h : float
        Time horizon in hours.  Must be positive.
    initial_thickness_um : float
        Initial component thickness in µm.  Must be positive.

    Returns
    -------
    dict
        Keys: 'model', 'total_loss_um', 'remaining_um',
              'domain_exhausted', 'scope', 'limitations'.
    """
    rate = _check_positive_finite(rate_um_h, "rate_um_h")
    horizon = _check_positive_finite(horizon_h, "horizon_h")
    thickness = _check_positive_finite(initial_thickness_um, "initial_thickness_um")

    total_loss = rate * horizon
    remaining = max(0.0, thickness - total_loss)
    exhausted = total_loss >= thickness

    return {
        "model": "linear",
        "rate_um_h": rate,
        "horizon_h": horizon,
        "initial_thickness_um": thickness,
        "total_loss_um": round(total_loss, 4),
        "remaining_um": round(remaining, 4),
        "domain_exhausted": exhausted,
        "scope": _SCOPE,
        "limitations": _LIMITATIONS,
    }


def parabolic_degradation(
    k_parabolic: float,
    horizon_h: float,
    initial_thickness_um: float,
) -> dict:
    """Compute parabolic (Wagner) oxidation loss over time.

    loss(t) = k · √t   (Wagner diffusion-limited oxidation model)

    Parameters
    ----------
    k_parabolic : float
        Parabolic rate constant in µm / h^0.5.  Must be positive.
    horizon_h : float
        Time horizon in hours.  Must be positive.
    initial_thickness_um : float
        Initial component thickness in µm.  Must be positive.

    Returns
    -------
    dict
        Keys: 'model', 'total_loss_um', 'remaining_um',
              'domain_exhausted', 'scope', 'limitations'.
    """
    k = _check_positive_finite(k_parabolic, "k_parabolic")
    horizon = _check_positive_finite(horizon_h, "horizon_h")
    thickness = _check_positive_finite(initial_thickness_um, "initial_thickness_um")

    total_loss = k * math.sqrt(horizon)
    remaining = max(0.0, thickness - total_loss)
    exhausted = total_loss >= thickness

    return {
        "model": "parabolic",
        "k_parabolic_um_per_sqrth": k,
        "horizon_h": horizon,
        "initial_thickness_um": thickness,
        "total_loss_um": round(total_loss, 4),
        "remaining_um": round(remaining, 4),
        "domain_exhausted": exhausted,
        "parabolic_note": "Wagner 1933 diffusion-limited model: loss = k·√t. Valid when oxide scale controls kinetics.",
        "scope": _SCOPE,
        "limitations": _LIMITATIONS,
    }


def arrhenius_rate(
    A_pre: float,
    Q_J_per_mol: float,
    temperature_K: float,
) -> float:
    """Return an Arrhenius-scaled rate.

    rate(T) = A · exp(−Q / (R · T))

    Parameters
    ----------
    A_pre : float
        Pre-exponential (Arrhenius A-factor).  Units are rate-units of the caller.
    Q_J_per_mol : float
        Activation energy in J/mol.  Must be positive.
    temperature_K : float
        Absolute temperature in Kelvin.  Must be positive.

    Returns
    -------
    float
        Scaled rate in the same units as A_pre.

    Raises
    ------
    EvidenceError
        If any input is non-positive or non-finite.
    """
    A = _check_positive_finite(A_pre, "A_pre")
    Q = _check_positive_finite(Q_J_per_mol, "Q_J_per_mol")
    T = _check_positive_finite(temperature_K, "temperature_K")
    return A * math.exp(-Q / (_R_GAS * T))


def coffin_manson_cycles(
    delta_T_C: float,
    C_constant: float,
    m_exponent: float,
) -> dict:
    """Estimate cycles to crack initiation via Coffin-Manson relation.

    Nf = C · (ΔT)^(−m)

    Parameters
    ----------
    delta_T_C : float
        Cyclic temperature range ΔT in °C (or K; same magnitude).  Must be > 0.
    C_constant : float
        Material constant C.  Must be positive.  Default reference: ~1e6 for YSZ.
    m_exponent : float
        Exponent m.  Must be positive.  Reference: ~2.0 for ceramics.

    Returns
    -------
    dict
        Keys: 'model', 'cycles_to_initiation', 'delta_T_C', 'scope', 'limitations'.

    Raises
    ------
    EvidenceError
        If ΔT ≤ 0 or other inputs are non-positive.
    """
    dT = _check_positive_finite(delta_T_C, "delta_T_C")
    C = _check_positive_finite(C_constant, "C_constant")
    m = _check_positive_finite(m_exponent, "m_exponent")

    Nf = C * (dT ** (-m))
    if not math.isfinite(Nf):
        raise EvidenceError("Coffin-Manson calculation produced a non-finite result")

    return {
        "model": "coffin_manson",
        "cycles_to_initiation": round(Nf, 2),
        "delta_T_C": dT,
        "C_constant": C,
        "m_exponent": m,
        "note": "Cycles to crack INITIATION only; propagation life not modelled. C and m must be experimentally validated for the specific material.",
        "scope": _SCOPE,
        "limitations": _LIMITATIONS,
    }


def thermal_stress(
    E_Pa: float,
    alpha_per_K: float,
    delta_T_C: float,
) -> dict:
    """Estimate thermoelastic stress from temperature differential.

    σ = E · α · ΔT   (unconstrained uniaxial; upper bound)

    Parameters
    ----------
    E_Pa : float
        Elastic modulus in Pa.  Must be positive.
    alpha_per_K : float
        Coefficient of thermal expansion in K⁻¹.  Must be positive.
    delta_T_C : float
        Temperature difference in °C (or K; same magnitude).  Must be positive.

    Returns
    -------
    dict
        Keys: 'model', 'stress_MPa', 'scope', 'limitations'.
    """
    E = _check_positive_finite(E_Pa, "E_Pa")
    alpha = _check_positive_finite(alpha_per_K, "alpha_per_K")
    dT = _check_positive_finite(delta_T_C, "delta_T_C")

    sigma_Pa = E * alpha * dT
    sigma_MPa = sigma_Pa / 1e6

    return {
        "model": "thermoelastic_uniaxial",
        "E_Pa": E,
        "alpha_per_K": alpha,
        "delta_T_C": dT,
        "stress_MPa": round(sigma_MPa, 4),
        "note": "Uniaxial fully-constrained upper bound. Real geometry (cylinder, gradient) will produce lower effective stress. Creep and plasticity excluded.",
        "scope": _SCOPE,
        "limitations": _LIMITATIONS,
    }


# ---------------------------------------------------------------------------
# Combined lifetime prediction
# ---------------------------------------------------------------------------

def lifetime_prediction(
    measured_loss_um: float,
    exposure_h: float,
    horizon_h: float,
    initial_thickness_um: float,
    model: str = "linear",
    temperature_C: float = None,
    uncertainty_percent: float = 20.0,
) -> dict:
    """Predict remaining component lifetime by extrapolating an observed loss rate.

    Parameters
    ----------
    measured_loss_um : float
        Measured material loss in µm over the observation period.
    exposure_h : float
        Length of observation period in hours.
    horizon_h : float
        Total service life horizon in hours.
    initial_thickness_um : float
        Initial thickness of the component in µm.
    model : str
        Degradation model: 'linear', 'parabolic', or 'arrhenius'.
        'arrhenius' requires temperature_C.
    temperature_C : float or None
        Operating temperature in °C.  Required when model='arrhenius'.
    uncertainty_percent : float
        ±% uncertainty band applied to the fitted rate (default 20%).

    Returns
    -------
    dict
        Keys: 'model_used', 'predicted_remaining_h',
              'lower_bound_h', 'upper_bound_h',
              'domain_exhausted', 'scope', 'limitations'.

    Raises
    ------
    EvidenceError
        On invalid inputs or unsupported model name.
    """
    loss = _check_positive_finite(measured_loss_um, "measured_loss_um")
    obs = _check_positive_finite(exposure_h, "exposure_h")
    horizon = _check_positive_finite(horizon_h, "horizon_h")
    thickness = _check_positive_finite(initial_thickness_um, "initial_thickness_um")
    unc = _check_positive_finite(uncertainty_percent, "uncertainty_percent")

    if model not in ("linear", "parabolic", "arrhenius"):
        raise EvidenceError(
            f"Unknown degradation model '{model}'. Choose: linear, parabolic, arrhenius"
        )

    remaining_thickness = thickness - loss
    if remaining_thickness <= 0:
        return {
            "model_used": model,
            "predicted_remaining_h": 0.0,
            "lower_bound_h": 0.0,
            "upper_bound_h": 0.0,
            "domain_exhausted": True,
            "note": "Observed loss already equals or exceeds initial thickness.",
            "scope": _SCOPE,
            "limitations": _LIMITATIONS,
        }

    if model == "linear":
        rate = loss / obs                         # µm/h
        rate_hi = rate * (1 + unc / 100)
        rate_lo = rate * (1 - unc / 100)
        pred_h = remaining_thickness / rate
        lo_h = remaining_thickness / rate_hi      # pessimistic (faster rate)
        hi_h = remaining_thickness / rate_lo      # optimistic (slower rate)

    elif model == "parabolic":
        # loss = k·√t → k = loss / √obs
        k = loss / math.sqrt(obs)
        k_hi = k * (1 + unc / 100)
        k_lo = k * (1 - unc / 100)
        # Solve remaining_thickness = k·√t_remaining
        pred_h = (remaining_thickness / k) ** 2
        lo_h   = (remaining_thickness / k_hi) ** 2
        hi_h   = (remaining_thickness / k_lo) ** 2

    else:  # arrhenius
        if temperature_C is None:
            raise EvidenceError("temperature_C is required for arrhenius model")
        if not math.isfinite(float(temperature_C)) or float(temperature_C) <= 0:
            raise EvidenceError("temperature_C must be a positive finite number")
        # Generic YSZ activation energy: Q = 100 kJ/mol
        Q_generic = 100_000.0
        A_generic = loss / (obs * arrhenius_rate(1.0, Q_generic, float(temperature_C) + 273.15))
        rate = A_generic * arrhenius_rate(1.0, Q_generic, float(temperature_C) + 273.15)
        rate_hi = rate * (1 + unc / 100)
        rate_lo = rate * (1 - unc / 100)
        pred_h = remaining_thickness / rate
        lo_h   = remaining_thickness / rate_hi
        hi_h   = remaining_thickness / rate_lo

    for v in (pred_h, lo_h, hi_h):
        if not math.isfinite(v):
            raise EvidenceError("Lifetime calculation produced a non-finite result")

    exhausted = pred_h <= 0

    return {
        "model_used": model,
        "predicted_remaining_h": round(max(0.0, pred_h), 2),
        "lower_bound_h": round(max(0.0, lo_h), 2),
        "upper_bound_h": round(max(0.0, hi_h), 2),
        "horizon_h": horizon,
        "within_horizon": pred_h <= horizon,
        "domain_exhausted": exhausted,
        "uncertainty_percent": unc,
        "interpretation": (
            "Conditional extrapolation only. Bounds reflect ±{:.0f}% rate uncertainty; "
            "real degradation may follow a different functional form. "
            "No measured wear data from this cell has been used to fit these parameters."
        ).format(unc),
        "scope": _SCOPE,
        "limitations": _LIMITATIONS,
    }


# ---------------------------------------------------------------------------
# Model catalog (for /api/reactor-degradation-models GET endpoint)
# ---------------------------------------------------------------------------

def model_catalog() -> dict:
    """Return a catalog of available degradation models and their parameters.

    Returns
    -------
    dict
        Description of all models and required inputs.
    """
    return {
        "models": {
            "linear": {
                "description": "Constant-rate corrosion/wear: loss(t) = rate · t",
                "inputs": {
                    "rate_um_h": "Corrosion rate in µm/h (positive)",
                    "horizon_h": "Time horizon in hours (positive)",
                    "initial_thickness_um": "Component thickness in µm (positive)",
                },
                "reference": "Standard linear corrosion law. Appropriate when rate is approximately constant.",
            },
            "parabolic": {
                "description": "Diffusion-limited oxidation: loss(t) = k · √t  (Wagner 1933)",
                "inputs": {
                    "k_parabolic": "Parabolic rate constant in µm/h^0.5 (positive)",
                    "horizon_h": "Time horizon in hours (positive)",
                    "initial_thickness_um": "Component thickness in µm (positive)",
                },
                "reference": "Wagner (1933) parabolic oxidation model. Appropriate for oxide scale growth.",
            },
            "arrhenius": {
                "description": "Temperature-dependent rate: rate(T) = A · exp(−Q/RT)",
                "inputs": {
                    "A_pre": "Pre-exponential factor (units match rate units)",
                    "Q_J_per_mol": "Activation energy in J/mol (positive)",
                    "temperature_K": "Absolute temperature in K (positive)",
                },
                "reference": "Arrhenius kinetics. Q ≈ 50–200 kJ/mol for YSZ and alumina.",
            },
            "coffin_manson": {
                "description": "Cycles to crack initiation: Nf = C · (ΔT)^(−m)",
                "inputs": {
                    "delta_T_C": "Cyclic temperature range in °C (positive)",
                    "C_constant": "Material constant C (positive; default ref ~1e6 for YSZ)",
                    "m_exponent": "Exponent m (positive; reference ~2.0 for ceramics)",
                },
                "reference": "Coffin (1954) / Manson (1953) low-cycle fatigue relation adapted for thermal cycling.",
            },
            "thermoelastic": {
                "description": "Thermoelastic stress upper bound: σ = E · α · ΔT",
                "inputs": {
                    "E_Pa": "Elastic modulus in Pa (positive; YSZ reference ~200 GPa)",
                    "alpha_per_K": "CTE in K⁻¹ (positive; YSZ reference ~10.5e-6 K⁻¹)",
                    "delta_T_C": "Temperature difference in °C (positive)",
                },
                "reference": "Linear thermoelastic theory. Gives fully-constrained uniaxial upper bound.",
            },
            "lifetime": {
                "description": "Remaining life estimate from observed loss rate (linear, parabolic, or arrhenius)",
                "inputs": {
                    "measured_loss_um": "Observed material loss in µm (positive)",
                    "exposure_h": "Observation period in hours (positive)",
                    "horizon_h": "Service life target in hours (positive)",
                    "initial_thickness_um": "Initial thickness in µm (positive)",
                    "model": "Base model: 'linear', 'parabolic', or 'arrhenius'",
                    "temperature_C": "Operating temperature °C (required for arrhenius only)",
                    "uncertainty_percent": "Rate uncertainty ± % (default 20)",
                },
            },
        },
        "scope": _SCOPE,
        "limitations": _LIMITATIONS,
        "important_disclaimer": (
            "All models are conditional extrapolations from published law forms. "
            "Parameters are NOT fitted to measured data from this experimental cell. "
            "Results must not be used for hardware qualification or operational decisions."
        ),
    }

