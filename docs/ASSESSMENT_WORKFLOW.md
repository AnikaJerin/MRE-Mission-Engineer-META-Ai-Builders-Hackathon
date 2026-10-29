# Input-driven MRE assessment — owner verification

## Implemented flow
1. Enter manual measurements or load the published one-hour example.
2. Click **Preview inputs & comparisons — free**. This validates values locally, calculates numerical results, independently checks arithmetic, and shows the exact dropdowns received by the backend. No model call occurs.
3. Inspect calculated metrics, published observation applicability, selected NASA clauses, and your declared target comparisons separately. Unknown optional metrics are grouped under additional inputs, not substituted with zero.
4. Editing any value invalidates the preview and clears credit consent. Preview again.
5. Authorize credits, then click **Assess with Meta**. The model requests the mandatory performance check, drafts all six dimensions, selects another critic check, critiques with supporting evidence, and submits a final review. At most five requests; no automatic retry.
6. Inspect the model findings, first review, critic comments, final review and cited numerical/source evidence. A correct first review may be retained.
7. Export HTML/JSON; reopen through Saved reviews without another API call.

The first check is deliberately mandatory for coverage, not a claim of unconstrained autonomous tool selection. The critic selects a different permitted numerical/readiness check. All discussion is model-generated for the actual input; formulas and published reference values are fixed scientific/software definitions.

## Owner-run checks (assistant has not run these)
From the project root:

```sh
PYTHONPATH="$PWD/src" python -m unittest discover -s tests -v
```

In `frontend`:

```sh
npm test
npm run build
```

Stop the older backend with Ctrl+C and restart from the project root:

```sh
PYTHONPATH="$PWD/src" python -m mre_engineer serve --port 8769
```

Use the existing Vite server at http://127.0.0.1:5173, or run `npm run dev` from `frontend`. Backend/UI contract must both be v5 before new paid assessments. No installation, API key change, ledger deletion or old report regeneration is needed. Keep MODEL_API_KEY in the backend terminal only.

## Two useful demonstrations

**Published source reconstruction:** Load published example, then free preview. Expected charge 1800 C; ideal O2 about 0.1492361552 g; reported collected O2 0.070 g; apparent ratio about 46.9055%; resistance 1.54 to 1.44 ohm (about -6.4935%); wall recession 22 +/-10 um over 3 hot-exposure hours (about 7.3333 um/h). Direct differences from that same published row are zero by construction. This checks reconstruction, not predictive accuracy. Source: Yu et al. 2025, NASA NTRS 20250004626, Tables 2, 4, 5 and Section 3.5.1. The +/- notation is retained without inferring a confidence level. No calibration or hardware qualification is invented.

**Constructed full-workflow fixture:** The existing manual test guide and `tests/fixtures/full_workflow_synthetic.json` label every value and design requirement as synthetic. With all measurement bases selected correctly, expected charge 172800 C; ideal O2 14.3266709 g; oxygen rate 0.1458333 g/h; total-system energy 1714.2857 kWh/kg; resistance +10%; wall loss rate 0.25 um/h; conditional remaining wall life 352 h. Against the *synthetic user targets*: oxygen-rate target met; energy, purity, wall-loss and resistance limits missed; observed duration and peak-temperature target met. The NASA profile and unmatched published observations are separate context, not synthetic NASA approvals. Model prose is not predetermined.

## Scope and release checks
- Regression controls cover five-request context sizing for the full fixture, changed-input preview rejection, correct conditional comparisons, actual saved tool receipts and criticism/final-stage completion with a test transport.
- Context byte limit and local spending controls remain enforced. Duplicate schema and repeated audit metadata are removed from model input; full receipts remain in saved evidence/exports.
- Offline fake-transport success is not live Meta success. Run the checks, then one explicit live assessment and inspect its completed five-stage trace before claiming a working live demo.
- Existing failed reports stay failed. They are not silently upgraded by this code change.
- Missing or incompatible measurements remain explicitly unresolved. Research values are never promoted into universal healthy/faulty thresholds.
- No physical sensor measurements, live reactor control, lifetime qualification or NASA endorsement is claimed.
