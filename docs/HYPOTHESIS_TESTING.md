# Additive hypothesis testing

The existing assessment, reviewer, critic, mathematical accounting and research comparisons are not modified by this extension.

In Review & assess → Hypotheses & 3D:
1. Generate/open the separate Wonder hypothesis version.
2. Open Test the hypotheses. Enter all eight annular geometry/material/boundary assumptions; specify conductivity and thermal-conductivity multipliers. The explicitly labelled demo button supplies editable synthetic assumptions, not NASA recommended properties.
3. Optional: supply an independently established or explicitly assumed generation mass, baseline recovery and recovery change for oxygen collection accounting. These three inputs are used together. The collected mass from the experiment is never silently substituted for generation.
4. Optional: add a comparable experimental reference, absolute tolerance and source. Full cell voltage is not comparable to the solver's bulk-only voltage. Choose comparable only after checking conditions, measurement method and system boundary. Unmatched/missing references do not become passes.
5. Consent → Rank, simulate & recommend. Maximum two additional Wonder requests; $0.50 local reservation envelope, not a provider cap. The first ranks investigative support and selects bounded models from reviewer/critic/hypothesis evidence. Python computes outputs. The second recommends a distinguishing experiment from actual calculated receipts. Previous results are not rewritten.
6. Ranking shows evidence priority, not failure probabilities. Simulation shows baseline → changed predictions for each supported hypothesis. Select Show this computed field in 3D to view its radial thermal/current field on the existing idealized reactor. No model-generated geometry or damage animation is used.
7. Recommendation explains the next measurement, expected rival patterns and prerequisites. Validation shows analytic agreement, energy-balance residual, refinement sensitivity, and any supplied experimental comparison. All run assumptions and results persist under outputs/hypothesis-tests; reopening makes no request.

Supported physics: constant-property, steady annular radial conduction with bulk Joule heating; declared-generation collection mass balance. The full finite-volume model and analytic verification are in reactor_field.py. It excludes electrochemical interfaces, overpotential, fluid flow, radiation, phase changes, corrosion kinetics, cracks and lifetime. Unsupported hypotheses remain explicitly not_modelled; they get evidence/experiment requests rather than invented predictions. The solver's source references establish context and arrangement, not calibrated thermal properties or a measured three-dimensional field.

An imported approximate SAM/Blender GLB is visual geometry; no verified computational mapping has been established. The current field renderer uses the idealized annular geometry and disables quantitative field overlays on unverified imported meshes. Do not claim a calibrated digital twin or all-hypothesis causal validation.

Owner checks:
PYTHONPATH="$PWD/src" python -m unittest discover -s tests -v
cd frontend
npm run build

Restart the backend on port 8769 before using new routes. Tests, simulations, builds and paid calls were not executed by the assistant, per owner instruction. Existing T12 findings and baseline comparisons remain separately versioned. This extension needs its own live validation; old evaluation scores do not certify it.
