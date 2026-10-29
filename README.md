# MRE Mission Engineer

A Meta-powered evidence-review workbench for lunar oxygen reactor ground experiments.
Researchers enter a run manually or upload a value-only Excel template, then request
an input-driven review: checked accounting, competing explanations, model-selected
tools, critique, revision and a next-evidence request they can inspect and export.

## Start here

**[Complete researcher workflow and two-terminal setup](docs/RESEARCHER_WORKFLOW.md)**

- **Frontend:** React + Vite, `frontend/`, `npm run dev`, http://127.0.0.1:5173.
- **Backend:** Python, `python -m mre_engineer serve --port 8769` from the repository
  root. Keep `MODEL_API_KEY` only in this terminal's environment.
- **Input:** manual values or the downloadable `.xlsx` template. A declared constant
  current or a complete aligned current trace is supported. Optional composition,
  context, uncertainty bounds and diagnostic-resource estimates remain explicit.
- **Review:** first assessment → critic's actual second check → revised/retained
  assessment → researcher accepts, requests edits or rejects a draft → HTML/JSON export.
- **Planned:** read-only equipment/LIMS/historian adapters. No live reactor or official
  software connection is implemented in this demo.

The new input adapter and React UI are authored but **not executed by the assistant**.
Run the documented backend tests, frontend tests/build and UI acceptance checks yourself.
Opening, refreshing, Excel import, replay and export do not start paid API work.
Assess requires explicit credit authorization; a completed cycle uses five requests
and two local tool executions. Failed attempts remain visible, with no automatic retries.

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

Use Python 3.11+ (the owner's environment is 3.12). Install the package in the project
virtual environment, run tests, then start the backend. In `frontend`, run `npm install`,
`npm test`, `npm run build`, then `npm run dev`. Commit the generated package lock
after successful installation. No frontend build or dependency installation has
been run by the assistant. Full commands and sample input/output are in the walkthrough.

Outputs and imported records remain local under ignored `outputs/`. Do not commit
keys, private laboratory exports or the local ledger. The budget is a local estimate
and reservation policy, not a provider-enforced cap. Published data attribution and
acquisition instructions remain in `sources/manifest.json` and `docs/DATA_SETUP.md`.


## Structured performance assessment upgrade

Manual and value-only Excel inputs now support measured resistance histories, wall recession with an explicit exposure clock, thermal cycles/crack evidence, observed endurance, energy boundaries, purity, and integrated-system records. Meta generates six separate evidence-linked findings; the UI and HTML/JSON export show each finding's inputs, formulas, independent arithmetic checks, source applicability and actual tool receipts. No overall reactor grade or prewritten case discussion is supplied.

An optional NASA 2026 LEIA Topic 2 profile distinguishes the selected required demonstration duration, encouraged pilot throughput, notional contaminant references and scaling evidence. It is a partial source comparison, not universal reactor acceptance or NASA certification.

- [Performance methods, sources and limitations](docs/PERFORMANCE_ASSESSMENT.md)
- [Owner-run tests and UI walkthrough](docs/PERFORMANCE_TEST_WORKFLOW.md)

This upgrade was statically parsed and its blank XLSX template rendered. The assistant has not run the application, tests, build or Meta calls. Existing frozen T12 results do not establish correctness of the new performance schema; run the new checks and a labelled new assessment before presenting it.


## Persistent local workspace and reviewed evidence library

The SQLite workspace (`data/workspace/mre.sqlite3`) retains the draft, selected report and versioned source references. Existing report/event files remain canonical, immutable evidence. Reopening restores the draft and saved review without rerunning Meta. Credit consent and API keys are never stored in the draft.

The Evidence library distinguishes selected NASA requirements from published experimental observations. Condition-matched publication differences are descriptive comparisons, not universal reactor acceptance limits. Purity quantity bases, processed-feedstock mass and available-oxygen inventory are explicit; there are now 22 performance metric entries plus charge accounting.

[Persistence, full capability audit and owner-run reopening checks](docs/PERSISTENCE_AND_REFERENCE_LIBRARY.md) explains the one-time upgrade and normal use. No dependency reinstall, tests, build or paid assessment is required for every reopening. A local backend must be running; the built React UI can be served by that single process.


Each new finding and critic comment now includes a short reason and resolved evidence references in the UI and exports. The optional measurement-record field concerns the user's data provenance; scientific formulas and reviewed reference records are already supplied by the backend. See [Decision and critic evidence](docs/DECISION_AND_CRITIC_EVIDENCE.md). The critic is a separate model call/role, not independent expert validation.
