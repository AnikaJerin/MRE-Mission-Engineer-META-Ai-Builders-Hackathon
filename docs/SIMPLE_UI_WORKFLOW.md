# Streamlined manual assessment UI

## Minimum required to start
- Experiment name.
- Electrolysis duration (hours).
- Either a positive declared constant current (A), or a measured current history covering the interval from 0 to duration in seconds.

These permit charge and ideal oxygen accounting. They do not establish collected oxygen, performance against an engineering specification, or reactor condition.

## Inputs needed for each additional result
| Result | Your experiment inputs |
| --- | --- |
| Oxygen rate / collected-to-ideal ratio | Collected O2 mass in g and confirmed oxygen/electrical time alignment. Calibration and measurement method support interpretation; they are not NASA threshold values. |
| Matched published comparison | Configuration, feedstock, operating temperature, current and matching duration. Wall and resistance comparisons also require their measurement bases. Load the public example to reconstruct reported values. |
| Cell energy | Matched current and voltage; current/voltage history if variable. This excludes furnace and auxiliaries. |
| Full-system specific energy | Metered energy, declared system boundary, record and oxygen/energy time alignment. |
| Current density | Current/history plus active anode area. |
| Resistance change / trend | Endpoints or measured R(t), comparable conditions and a record. A history is required for the descriptive slope. |
| Wall-loss rate | Measured wall recession, hot exposure or justified electrolysis denominator, and measurement record. +/- bound is optional and never invented. |
| Endurance | Observed duration, outcome, applicable run conditions/record. Predicted lifetime is a separate advanced model. |
| Purity | Measured percent, mole/volume/mass denominator, wet/dry basis and measurement reference. |
| NASA integrated-system clauses | Explicitly select the NASA profile, then supply the relevant full-system measurements. A laboratory cell does not become a system demonstration by selecting the option. |

Unknown optional data stays unknown. The software does not replace measured inputs with another experiment's numbers.

## Four main tabs
1. **Experiment:** core values and reactor context. Optional measured I/V history is here.
2. **Measurements:** compact category tabs for electrical, oxygen/energy, materials, endurance, environment, and records/inventory. Only the active category is shown. An Integrated system category appears when the NASA profile is selected.
3. **Reference data:** read-only published experimental values, NASA selected-clause values, registry version and source links. No editable measurement or target fields. Optional NASA/custom comparison settings live under Experiment; opting in adds the corresponding measurement category.
4. **Review & assess:** free preview, actual submitted choices, then explicit Meta consent and assessment. Arrow keys navigate tabs; mobile tabs scroll horizontally.

Published reference values are stored in the backend. Researchers enter their measurements, not the library's reference numbers. Internal/private NASA data integration remains future work; this UI demonstrates public-source comparisons.

## Removed from the normal input flow
- No diagnostic-budget, available-time or individual test-cost entry. They do not measure reactor performance.
- Synthetic custom limits are not silently reused. When own requirements are off, target values/references are excluded from the assessment payload.
- Lifetime assumptions are also excluded unless advanced own-requirements mode is enabled.
- Historic assessment reports are retained unchanged. Opting out affects the next submission only.

## Owner checks
From `frontend`: `npm test`, then `npm run build`. Tests and app were not run by the assistant. No new backend migration or model call is needed for this UI-only change. Existing Vite development server should reload source changes; otherwise refresh http://127.0.0.1:5173. Backend remains on port 8769. Built UI requires the owner build before refreshing.
