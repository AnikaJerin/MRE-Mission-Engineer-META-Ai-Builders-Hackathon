# Day 2: bounded chemical and charge accounting

Implementation authored; not executed by the assistant. No new dependencies or Meta
key are needed. The owner reported all thirteen Day 1 tests passing.

## Run these yourself

Stop the previous server with Ctrl+C before restarting it. In the existing virtual
environment, from this repository:

```sh
python -m pip install --no-deps -e .
python -m unittest discover -s tests -v
python -m mre_engineer accounting --run-name v1 --reference-mass-g 100
python -m mre_engineer serve --accounting-run v1
```

Open http://127.0.0.1:8766 and choose **Accounting**. This view displays the saved
report. It performs no calculations or Meta requests on refresh. Export evidence JSON
includes the available saved report. Reports are saved under ignored
`outputs/day2/v1/report.json`. A repeated run name is rejected to avoid overwriting
evidence; choose `v2` for a new run and restart with `--accounting-run v2`.

## What should happen (expectations, not results already executed)

- Source oxide total remains 99.1 wt%; it is not normalized to 100.
- The remaining 0.9 wt% is marked unrepresented, not assumed oxygen-free.
- Inventory refers to your selected 100 g reference mass, NOT the study's actual batch.
- Charge is 1800 C under the nominal 0.5 A constant-current / 3600 s assumptions.
- Ideal four-electron oxygen amount should be around 0.149 g, not a prediction of
  the reported collected amount.
- Using the paper's reported oxygen mass as an INPUT gives an apparent ratio near
  the reported 47%. `rounding-compatible` means arithmetic consistency only.
- Seven historical evidence entries remain visible and uncertainty stays unknown.
- `api_calls: 0`, `network_calls: 0` and `agent_run_ready: false` remain expected.

## Tools implemented

1. `load_composition`: single-analysis CSV, source IDs, exact units, supported oxides,
   no duplicates or silent pooling, finite values, no implicit iron redox conversion.
2. `oxygen_inventory`: oxygen represented in listed oxides; original percentage basis
   and selected reference mass; per-oxide contributions; no recoverable-yield estimate.
3. `charge_oxygen_bound`: Q = I t, n(O2) = Q/(4 F), m = n M; explicit setpoint/pathway
   assumptions; optional reported measured mass as a separate input.
4. `build_report` / saved replay: linked inputs and code hashes, historical printed-number
   check, uncertainty limits, zero API use. Changed inputs/code invalidate saved replay.

These Python functions are the future agent tool foundation; a Meta tool registration,
agent, gas calibration model, numerical retrieval or reactor simulation is NOT implemented.
Saved report hashes provide local integrity, not independent scientific certification.

## Acceptance checklist

- All old and new tests pass (the authored suite contains 31 tests).
- Accounting command succeeds with no API calls; original file hashes remain linked.
- Original 99.1% composition remains visible; no manufactured 100% composition.
- Inventory and charge masses have visibly different bases in the UI.
- Historical comparison is rounding-compatible, and the ratio is shown as a fraction.
- Missing gas traces, calibration and measurement uncertainty remain unresolved.
- No-replay state before the first run, stale-report state after input changes, and
  new-run-name behavior are explicit. Do not edit saved numerical results to make them pass.
- Owner visually checks the lunar Accounting view, phone layout, dialogs and export.

## Scientific boundaries

This is conditional accounting, not a model that predicts oxygen production. Reported
efficiency is derived from related reported measurements, so it is not independent
ground truth. Gas reference conditions are not inferred from sccm and no gas concentration
is converted to mass. Unknown measurement error is not treated as zero. Printed-number
intervals reflect representation/rounding, not confidence or calibration.

No attempt is made to predict corrosion, failure probability, lifetime, temperature
field, reaction kinetics or optimal next experiments. Those claims need other evidence.
We do not run optional OxideProperties/FactSage code in this step.

## Next: substantial Meta reasoning

After these tools pass owner verification, the Meta layer can choose a check, receive
structured numerical evidence, challenge an interpretation and revise a next-test card.
The raw-trace and calibration gaps are meaningful constraints for that reasoning,
not placeholders to fill with invented values.
