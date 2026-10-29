# Owner-run performance assessment walkthrough

The assistant authored this change without running the application, tests, build or paid Meta calls. Static source parsing and blank-template rendering are not end-to-end validation.

## 1. Run local checks first (no Meta calls)

From the repository root, in the activated environment:

```sh
PYTHONPATH="$PWD/src" python -m unittest discover -s tests -v
```

New coverage is in `tests/test_performance.py`, the additional Excel tests and the updated offline agent loop test. Stop and report any failure before paying for an assessment.

## 2. Restart the backend; start React separately

Stop the old backend with Ctrl+C in its terminal. Use the same key-setting method already used successfully; export MODEL_API_KEY only in the backend terminal. Do not paste the key into a file, browser or chat.

```sh
PYTHONPATH="$PWD/src" python -m mre_engineer serve --port 8769
```

In a second terminal:

```sh
cd frontend
npm run dev
```

Open the Vite URL printed in that terminal (normally http://127.0.0.1:5173). If you choose to serve a built frontend instead, rebuild it yourself after these UI changes with `npm run build`. Restarting an old built page does not rebuild React.

## 3. Begin with the small arithmetic control

New assessment → manual input:

| Form field | Input |
| --- | --- |
| Experiment name | Arithmetic control A |
| Question | What does the accounting support and what measurements are missing? |
| Constant current | 0.5 A |
| Electrolysis duration | 1 hour |
| Collected oxygen | 0.07 g |
| Oxygen/electrical windows | Reported for the same interval |

Leave values you do not know blank. Keep the official profile unselected. These are test inputs, not a claim about your reactor. Authorize the displayed credits and click **Assess experiment** once.

Expected computed values to compare **after** the run: 1800 C charge, about 0.149236 g ideal O2 and 46.91% reported-collected/ideal ratio. Do not type these outputs into the form. Unknown calibration/material/endurance evidence should remain unknown, not become a fault. All six final dimensions should appear if the full loop completes.

Change current to 1 A and create a separate assessment: charge should double to 3600 C, ideal O2 to about 0.298472 g, and the ratio halve to about 23.45%. The generated discussion can vary; no particular wording or change of recommendation is guaranteed.

## 4. Reconstruct published material/electrical observations

Create a new assessment and clearly label it **Yu2025 published 12h reconstruction**. This is a paper reconstruction, not new laboratory telemetry. Use [Yu et al. 2025](https://ntrs.nasa.gov/citations/20250004626), Tables 2, 4, 5 and the experimental-method sections.

| Section / field | Input |
| --- | --- |
| Current, electrolysis duration, collected O2 | 0.5 A; 12 hours; 0.749 g |
| Windows | Reported same interval |
| Configuration | Hollow YSZ/Pt option |
| Feedstock; anode; cathode; temperature | LHS-1; YSZ/Pt; Mo; 1600 °C |
| Original record / source label | Publication URL, Table 2; published scalar reconstruction |
| Resistance / initial and final | 1.46 ohm; 0.78 ohm |
| Resistance record | Publication Table 5; leave comparability unconfirmed unless you establish the exact matched method/conditions |
| Total hot-melt exposure | 14 h |
| Measured wall loss; printed bound | 85 µm; 19 µm |
| Wall-loss rate basis | Hot-melt exposure |
| Wall-loss record | Publication Table 4 and method section; characterize the printed ± convention rather than calling it a calibrated confidence interval |

Do not invent raw traces, number of thermal cycles, calibration receipts, initial wall thickness, retirement criterion, actual 214 h endurance, integrated-system status or a universal pass/fail target. A published projection can be entered separately with its model reference; it is not observed test duration.

Expected arithmetic: resistance endpoint change about **−46.5753%**; wall recession `85/14 ≈ 6.07143 µm/h`; collected output `0.749/12 ≈ 0.0624167 g/h`. There is no R(t) slope from two endpoints. This module should not assert that declining resistance proves better oxygen production or that a wall-loss average establishes safe life.

## 5. Inspect the evidence behind a result

1. **Performance assessment:** six separate findings and proposed next evidence, not one health score.
2. **All numerical performance metrics and formulas:** available/missing metrics, units, clock/boundary and independent arithmetic status.
3. **Your declared requirement comparisons:** appears only for targets you actually supplied with a reference. If conditions do not match, expect insufficient evidence.
4. **Decision evidence:** open a dimension to inspect exact cited input fields, metric formula/results, source locator/applicability and actual tool receipts.
5. **First review → critic → final review:** inspect whether the critic identified a substantive gap or retained the original finding. Text changes alone do not establish improvement.
6. Export HTML/JSON. Verify the exported input matches the submitted values and contains the new performance/decision-evidence sections. Refresh/reopen the saved report should make no new paid request.

## 6. Use the NASA profile only for the appropriate system case

Under **Optional NASA system-demonstration context**, select **NASA 2026 LEIA Topic 2**. Supply your own full operations-window duration, system-output measurement point, integrated continuous-run evidence, consumables/repair records and relevant performance measurements. Do not mark a paper's laboratory-cell experiment as an integrated-system test merely to fill the fields.

Expected UI distinctions: 48 h is a selected required duration; approximate 0.2 kg/h is an encouraged pilot reference; cleanliness values remain notional/context only; 10 t/year needs a reviewed scaling argument. Missing evidence must withhold a conclusion. No overall NASA-compliant badge should appear.

## 7. Excel route

Download the **new** template. Fill `Experiment` values with the specified units; `Trace` accepts current/voltage histories; `Composition` one oxide analysis; `Resistance` an optional measured R(t) series. Do not supply resistance endpoints and history together. Leave unused measurement cells empty and unknown dropdown values unchanged. Upload, inspect the imported values and their cell provenance, then authorize and assess. Results must derive from the uploaded values, not the example.

Integration to a live reactor, potentiostat, DAQ, historian or LIMS remains planned only. This demo reads submitted records; it does not operate hardware.


For persistent drafts, the versioned local reference library, matched publication comparisons and the new purity/feedstock measurement-basis checks, see [Persistence and reference library](PERSISTENCE_AND_REFERENCE_LIBRARY.md). Reopening an existing assessment does not require another paid run.
