# Accounting methods and references

Reviewed 28 October 2026. No numerical execution by the assistant.

## Reference constants

- BIPM, SI definition: https://www.bipm.org/en/measurement-units/
  N_A = 6.02214076e23 mol^-1 and e = 1.602176634e-19 C are defining constants;
  F = N_A e. The code stores a rounded floating-point representation in C/mol.
- CIAAW, Abridged Standard Atomic Weights 2024:
  https://ciaaw.org/abridged-atomic-weights.htm
  The code uses the listed abridged central values for O, Si, Fe, Mg, Ca, Al, Ti,
  Na, K, Mn and P as approximate molar masses in g/mol. Standard-weight variation
  and sample isotopic differences are not propagated. They must not be mistaken
  for exact isotope-specific masses.
- Experimental context and efficiency definition: Yu et al. (2025), main paper,
  sections 2.2.2 and 3.1, Tables 1-2:
  https://ntrs.nasa.gov/citations/20250004626

## Composition and oxygen inventory

For oxide X_a O_b with mass fraction w, oxygen represented on a chosen mass m is

`m * w * [b M(O) / (a M(X) + b M(O))]`.

Input is explicit oxide weight percent (w = wt_percent/100), one analysis and
one source basis. The narrow CSV adapter rejects missing/censored entries rather
than silently imputing them; importing a censored archive needs a later contract.
FeO and Fe2O3 are supported when explicitly reported. FeOT/total iron is rejected
because oxidation-state interpretation is not determined by the token alone.

The fixture's unrepresented mass fraction stays unrepresented. Therefore the
result is the inventory represented by measured/listed oxides, not a complete
bulk oxygen estimate or extractable oxygen. No automatic normalization is applied.
Any selected reference mass is labelled as an input assumption. It is not the
study's measured reactor batch mass and is not used to infer extraction efficiency.

## Charge accounting

Assume positive constant nominal current over the electrolysis duration. For the
declared oxygen-evolution half-reaction, four moles of electrons correspond to
one mole O2. With every electron allocated to that pathway, `Q = I t` and
`m_ideal = Q/(4 F) * M(O2)`. A measured/collected mass divided by this amount is
an apparent ratio under those assumptions. Values above one are flagged for
review, not clipped or diagnosed. No thermal efficiency or gas-generation history
is inferred. These functions reject zero/negative duration and current.

## Historical rounding policy fixed before running

For case `yu2025-inverted-hollow-anode-1h`, Table 2 prints oxygen to 0.001 g and
efficiency to an integer percentage point. Assuming nearest rounding, use half
increments of 0.0005 g and 0.005 fraction. Compare overlap of the mass-derived
ratio interval and the reported efficiency interval. Nominal current/duration
are held fixed for this limited arithmetic check; their measurement uncertainty
is unknown. Boundary equality is accepted for this coarse screen.

This check cannot validate the raw observations, allocation of current, gas
calibration or the causal mechanism. It is explicitly NOT a statistical test.
It does not establish that the model predicted an experimental outcome. If the
case has no matching policy, report `not-applicable` rather than invent a tolerance.

## Reports and replay

The report records the case, composition, source-manifest and accounting-code
SHA-256 values, constants URLs, arguments, limits and related evidence IDs.
The dashboard reads a saved result and rejects changed/modified reports or inputs.
Local hash checks are reproducibility aids, not proof of source authenticity,
correctness, tamper resistance or independent validation.
