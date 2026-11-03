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

### 6. Verify the build

```bash
cd frontend
npm run build
cd ..
```

Use an explicitly authorized UI assessment for a live end-to-end check. Development
test suites and extended walkthroughs were moved to an external cleanup backup;
those files are not required for normal application startup.

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

This README is the primary setup guide. Source metadata and reuse notes remain in `sources/manifest.json`.

## Hackathon contributions

The following describes the submitted implementation, rather than claiming ownership
of third-party models, libraries, papers or measurements. Git history is the record
for contribution timing; identify any pre-event work separately before submission.

- Manual experiment-entry React UI, persistent local drafts and saved-review table.
- Python charge/oxygen, composition, energy, resistance and measurement-readiness checks.
- Meta Muse Wonder tool selection, first review, critic and final review with linked evidence.
- Additive result-linked hypotheses, reconsideration of prior hypotheses and next-evidence requests.
- Bounded numerical scenario comparisons, material recession projections and interactive Three.js component views.
- Cloud SAM segmentation and calibrated before/after projected-silhouette comparison, with separate image reviewer and critic.
- HTML/JSON exports, source reference library, local request/cost ledger and synthetic diagnostic evaluation.

These are evidence-review MVP features. The model is not a physically calibrated
reactor digital twin, certified fault detector, validated lifetime predictor or reactor controller.
Synthetic scenarios do not establish real-world accuracy or saved engineering time.

## Attribution, data and asset rights

| Item | Credit and reuse scope |
| --- | --- |
| Published hollow-anode configuration and scalar observations | Yu et al., *Improving Molten Regolith Electrolysis with Zirconia-Based Hollow Anode Technology* (2025), [NASA NTRS 20250004626](https://ntrs.nasa.gov/citations/20250004626). Published arrangement informs an approximate visual model; not measured CAD. Public download does not grant blanket figure-reuse rights. |
| Other NASA/research references | Exact source URLs, versions and rights notes are retained in `sources/manifest.json` and the versioned benchmark/reference records. NASA hosting does not imply NASA endorsement or that all included works are public domain. |
| Uploaded photographs and SAM masks | User-supplied local records. Preserve the original source/permission note. Segmentation does not create permission to redistribute the source photograph. Use owned/licensed images or labelled synthetic images in the public demo. |
| Synthetic QA images and numerical scenarios | Software-test fixtures, not NASA measurements or evidence of actual reactor damage. Their synthetic status must remain visible. |
| Reactor visualization | Project-authored approximate geometry and Three.js rendering, informed by the cited configuration. No claim of SAM 3D reconstruction or engineering-grade geometry. |
| Meta models and SDKs | Muse Wonder and SAM are Meta services; model/SDK use remains subject to their applicable terms. They are not project-authored models. |
| Export charts | [amCharts 5](https://www.amcharts.com/) libraries are bundled for offline HTML reports. The default amCharts logo is retained. The bundle includes a script-path fallback for inline exports. |
| Third-party software | Python jsonschema, React, Vite, Three.js and Meta SAM packages are external dependencies. Preserve their included licences/notices; dependency versions are described by `pyproject.toml` and `frontend/package-lock.json`. |

Local acquired papers under `data/raw/`, uploaded photos, saved outputs and the workspace
are not intended for redistribution with source code. Check specific rights before
including any source figure in the submission video. The source manifest is an attribution
record, not a blanket licence clearance. Repository code licensing must be chosen by the owner;
this README does not assign a licence to other people's work.

## Files retained for operation

- `src/`, `frontend/`, `pyproject.toml`: backend, UI, dependencies and build configuration.
- `cases/`, `sources/`, `benchmarks/`, `evaluation/`, `engineering_cases/`: runtime reference inputs and evaluation protocols. Some Markdown files are machine-read and hash-checked; retain them.
- `scripts/`: optional Blender asset-generation utilities.
- `data/`, `outputs/`: existing local workspace, sources, evidence, results and budget state. Preserve these to keep saved work.
- `.venv/`, `frontend/node_modules/`: installed local runtimes/dependencies, ignored by Git.
- `.git/`, `.gitignore`, `README.md`: repository metadata and setup documentation.


## References

- [NASA NextSTEP-3 solicitation — SAM.gov](https://sam.gov/opp/812c81b0f0b84943be12a5f29615d3c8/view#attachments-links)
