# MRE Mission Engineer

A Meta-powered evidence-review workbench for lunar oxygen reactor ground experiments.
Researchers enter a run manually, then request
an input-driven review: checked accounting, competing explanations, model-selected
tools, critique, revision and a next-evidence request they can inspect and export.

## Setup and run

### Requirements

- Python **3.11+** with `venv` and pip.
- Node.js **20.19+ within Node 20**, or **22.12+** (Vite requirement), and npm.
- A Meta Model API key with access to Muse Wonder and, for image segmentation, SAM 3.1.
- A modern browser with WebGL for the interactive Three.js view. No local NVIDIA GPU is needed for cloud SAM.

Run all root-level commands from this repository's directory. Clone/download the
repository first, then `cd` into it. The examples below use macOS/Linux.

### 1. Install once

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
cd frontend
npm ci
cd ..
```

Use the committed `frontend/package-lock.json` with `npm ci`. Python dependencies
are declared in `pyproject.toml`; their allowed versions are ranges, not an exact lock.
`--no-deps` is unnecessary for a clean installation.

### 2. Terminal A — start the Python backend

From the repository root, activate the environment and enter your key privately.
For the default macOS **zsh** shell:

```zsh
source .venv/bin/activate
read -r -s 'MODEL_API_KEY?Paste Meta API key, then press Enter: '
export MODEL_API_KEY
PYTHONPATH="$PWD/src" python -m mre_engineer serve --port 8769
```

For **bash**, replace the `read` line with:

```bash
read -r -s -p 'Paste Meta API key, then press Enter: ' MODEL_API_KEY
```

Keep this terminal running. The key must be set **before** starting the backend;
setting it in another terminal does not update a running server. Never put the key
in frontend code, screenshots, reports or Git. This setup does not automatically load `.env`.

### 3. Terminal B — start the React frontend

From the repository root:

```bash
cd frontend
npm run dev
```

Open **http://127.0.0.1:5173/**. The development frontend forwards API requests to
**http://127.0.0.1:8769**. Use these matching ports; `5173` is configured as a strict port.

### 4. Use the application

1. Choose **New experiment** and enter measurements manually. Required to start:
   experiment name, duration, and either constant current or a current history.
2. Add collected oxygen and the other measurements you actually have. Leave unknown
   values blank. Published reference values are supplied separately by the backend.
3. In **Review & assess**, check the input summary, authorize Meta credits and click
   **Assess with Meta**. The live cycle produces a first review, critic and final review.
4. Inspect Summary, Measurements, Review & critic and Evidence. Completed results can
   be reopened from **Saved reviews** and exported as HTML/JSON.
5. In **Hypotheses & 3D**, explicitly authorize hypothesis generation. Numerical tests
   require declared scenario assumptions; these are separate from measured inputs.
6. For SAM before/after comparison, upload PNG images, inspect the returned masks,
   supply measured image scales and confirm comparable views before running comparison.

Opening saved reports, refreshing and exporting do not start paid Meta requests.
Assessment, hypothesis and SAM actions require explicit authorization. Synthetic demo
inputs must remain labelled synthetic. Physical equipment/LIMS integration is not implemented.

### 5. Reopen or restart

Installation is not required every time. Start Terminal A and Terminal B again.
After a backend code update, press **Ctrl+C** in Terminal A and rerun its serve command.
If the key was entered in that same terminal it remains exported; a new terminal needs it again.

Saved drafts/reference records use `data/workspace/mre.sqlite3`; saved reports and
traces are under `outputs/`. Preserve both directories to retain your workspace.
They are ignored by Git, so a fresh clone will not contain the owner's saved live results.
Reopening a saved result does not rerun it or spend credits.

### 6. Verify the installation

From the repository root with `.venv` active:

```bash
PYTHONPATH="$PWD/src" python -m unittest discover -s tests -v
cd frontend
npm test
npm run build
cd ..
```

These checks do not establish live provider availability or physical reactor validity.
Use an explicitly authorized UI assessment for a live end-to-end check.

Optional known-cause **synthetic** diagnostic benchmark (up to 15 Wonder requests;
$3.75 local reservation envelope, not a provider billing cap):

```bash
PYTHONPATH="$PWD/src" python -m mre_engineer.reactor_diagnostics freeze --name diagnostics-v1
PYTHONPATH="$PWD/src" python -m mre_engineer.reactor_diagnostics run --name diagnostics-v1 --freeze-name diagnostics-v1 --allow-api-call
PYTHONPATH="$PWD/src" python -m mre_engineer.reactor_diagnostics report
```

Run this in a key-enabled terminal while no other paid job is active. Freeze/run names
are immutable: choose new names for a new run. Reuse a freeze only if its protocol matches.

### Troubleshooting

| Symptom | Action |
| --- | --- |
| `No module named mre_engineer` | Return to the repository root, activate `.venv`, and use the documented `PYTHONPATH="$PWD/src"` command. Reinstall with `python -m pip install -e .` if needed. |
| Assess disabled: missing key | Export `MODEL_API_KEY` in Terminal A, then restart the backend. |
| API connection/proxy error | Confirm backend port `8769` and frontend port `5173` are running. |
| Address already in use | Stop the earlier server with Ctrl+C in its terminal. Run one backend instance. |
| Previous request has unknown billing | Review the failed request and provider usage; use the explicit acknowledgement flow only if accepting the unknown charge. Do not delete the ledger to unblock. |
| Another operation is active | Let the existing job finish or request stop; avoid simultaneous paid runs across tabs/terminals. |
| Meta timeout or HTTP error | Inspect the saved failure. No automatic retry is performed; a new attempt may cost credits. |
| SAM returns no matching object | Use a closer crop and a short visible-object description; inspect masks before comparison. |
| Fresh clone has no saved reviews | Expected: local `outputs/` and the SQLite workspace are not bundled. Create a new run. |

For deeper methods and examples see [researcher workflow](docs/RESEARCHER_WORKFLOW.md)
and [source-data setup](docs/DATA_SETUP.md). This README is the primary current setup guide.

## Scope and correctness

This is an evidence-review and experiment-planning prototype, not a calibrated failure
predictor or NASA-qualified controller. Independent Decimal/Fraction calculations
check numerical accounting, while source-grounded references check bounded published
claims. New experiment inputs have no known correct engineering answer by default.
The UI therefore shows evidence gaps and verification scope rather than a general
accuracy/health percentage. Hypotheses and next-test utility remain drafts.

See [proposal alignment, remaining limits and integration roadmap](docs/SCOPE_ALIGNMENT.md),
[accounting methods](docs/ACCOUNTING_METHODS.md) and
[actual dataset usage](docs/DATASET_USAGE.md). Public papers are historical evidence,
not raw telemetry. No NASA affiliation or worldwide-first claim is made.

## Recorded evaluation

The owner completed six development and six evaluation tasks under T12 freeze
`t12-v2`: `dev-t12-v3` / `eval-t12-v3`. On evaluation, checklist and resampling were
6/6, one-pass and challenge/revision 5/6, with full output coverage; available
numerical fields matched 2/2. Revision made one correction and one regression.
These small dependent source tasks do not establish general engineering superiority.
The new input adapter is separately tested; earlier T12 results do not automatically
validate it. Existing frozen implementations, outputs and failed attempts are preserved.

The separate **Validation & methods** page retains source references, independent
checks, two recorded engineering evidence workflows and benchmark comparisons.
The `versioned-v3` engineering collection deliberately discloses separately versioned
components. It is not a single fixed-version prospective reactor experiment.

Reference documentation: [T12 protocol](benchmarks/t12/v1/PROTOCOL.md),
[ground-truth sources](benchmarks/t12/v1/SOURCES.md),
[engineering sources](engineering_cases/v1/VALIDATION_SOURCES.md),
[baseline evaluation](docs/EVALUATION.md) and [legacy validation UI](docs/T12_UI_WORKFLOW.md).

## Reproducibility

Use the setup and verification commands above. Keep keys, private records and the
local ledger out of Git. Published-source attribution and acquisition instructions
are recorded in `sources/manifest.json` and `docs/DATA_SETUP.md`. Local cost estimates
are not a provider-enforced spending cap.

## Structured performance assessment upgrade

Manual inputs support measured resistance histories, wall recession with an explicit exposure clock, thermal cycles/crack evidence, observed endurance, energy boundaries, purity, and integrated-system records. Meta generates six separate evidence-linked findings; the UI and HTML/JSON export show each finding's inputs, formulas, independent arithmetic checks, source applicability and actual tool receipts. No overall reactor grade or prewritten case discussion is supplied.

An optional NASA 2026 LEIA Topic 2 profile distinguishes the selected required demonstration duration, encouraged pilot throughput, notional contaminant references and scaling evidence. It is a partial source comparison, not universal reactor acceptance or NASA certification.

- [Performance methods, sources and limitations](docs/PERFORMANCE_ASSESSMENT.md)
- [Owner-run tests and UI walkthrough](docs/PERFORMANCE_TEST_WORKFLOW.md)

Existing frozen T12 results do not automatically validate later schema changes. Run the current checks and an explicitly authorized live assessment before presenting a changed implementation.


## Persistent local workspace and reviewed evidence library

The SQLite workspace (`data/workspace/mre.sqlite3`) retains the draft, selected report and versioned source references. Existing report/event files remain canonical, immutable evidence. Reopening restores the draft and saved review without rerunning Meta. Credit consent and API keys are never stored in the draft.

The Evidence library distinguishes selected NASA requirements from published experimental observations. Condition-matched publication differences are descriptive comparisons, not universal reactor acceptance limits. Purity quantity bases, processed-feedstock mass and available-oxygen inventory are explicit; there are now 22 performance metric entries plus charge accounting.

[Persistence, full capability audit and owner-run reopening checks](docs/PERSISTENCE_AND_REFERENCE_LIBRARY.md) explains the one-time upgrade and normal use. No dependency reinstall, tests, build or paid assessment is required for every reopening. A local backend must be running; the built React UI can be served by that single process.


Each new finding and critic comment now includes a short reason and resolved evidence references in the UI and exports. The optional measurement-record field concerns the user's data provenance; scientific formulas and reviewed reference records are already supplied by the backend. See [Decision and critic evidence](docs/DECISION_AND_CRITIC_EVIDENCE.md). The critic is a separate model call/role, not independent expert validation.
