# Owner-run MVP completion and submission evidence

The owner previously reported 71 offline tests passing and a completed 30-request
six-case pilot: checklist 6/6; each Meta method 5/6; no paired decision corrections.
Those reports, keys, freezes and scores are preserved. This addition does not turn
code corrections or newly chosen easier tasks into evidence of model superiority.

## Repairs and completed implementation

- Deterministic release audit recomputes scope/unit/record gates for structured
  pilot decisions. It preserves raw answers and separately records effective
  decisions. This does not certify arbitrary free-text plans or control a reactor.
  Original physical tools already require supported inputs; retain those checks.
- Historical agent drafts with unchanged inputs and verified traces can be viewed
  as archived code-version replays. They no longer disappear merely because billing
  diagnostics changed. Changed source/accounting inputs still suppress results.
- Four published-source tasks, separate answer key, immutable protocol/code freeze,
  fixed checklist, one-pass, critic-selected local check + revision, and equal-call
  resampling control. Each task uses five unique paid requests. The original answer
  is shared; both longer methods see the identical returned check.
- Source-field accuracy, numerical tolerance, units, failures and paired corrections
  are reported. Open-ended explanation and next-experiment usefulness are unscored.
- Lunar UI Validation view shows original pilot, deterministic audit, source results,
  original/revised/control answers and actual critic/check events. Refresh is read-only.
- JSON and script-free HTML dossier exports include saved results and claim limits.
  Browser Print / Save as PDF is available for the generated HTML if wanted.

All of the above is authored, not executed by the assistant. Only static syntax
inspection is permitted in this session. Newly authored offline tests use doubles,
not actual Meta performance. Do not announce a completed validated MVP until the
owner's checks and recorded live run pass. There is no deployment in this step.

## 1. Offline checks and prior-work release audit

Stop the running server with Ctrl+C, activate this repo's virtual environment, then:

```sh
python -m pip install --no-deps -e .
python -m unittest discover -s tests -v
python -m mre_engineer release-audit --pilot-run full-pilot-v4 --run-name v1
python -m mre_engineer source-preview
python -m mre_engineer api-budget
```

These commands make no API calls. If tests or source preview fail, fix the reported
issue before freezing or spending credits. release-audit writes a new artifact and
never rewrites the six-case model results. Existing run names cannot be overwritten;
choose a fresh name and pass it through --release-run if you have already used v1.

## 2. Freeze, then one-task paid smoke test

MODEL_API_KEY must already be exported in this terminal. Do not share it.

```sh
python -m mre_engineer source-freeze --name sources-v1
python -m mre_engineer source-run --run-name smoke-v1 --freeze-name sources-v1 --task-id thermal-clock --allow-api-call
python -m mre_engineer source-report --run-name smoke-v1
```

Maximum five requests/$1.25 local reservation envelope. Actual usage estimates are
separate; reservations are not a provider billing cap. Stop at any failure. Inspect
the actual api_error/submission_rejected event, not just summary zeroes.

## 3. Full four-task run, only after smoke succeeds

```sh
python -m mre_engineer source-run --run-name v1 --freeze-name sources-v1 --allow-api-call
python -m mre_engineer source-report --run-name v1
```

Maximum twenty requests/$5 local reservation envelope for this command. Do not
rerun the old 30-request pilot. If model methods equal or trail the checklist, state
that result. Do not edit the answer key or discard unsuccessful tasks to claim a win.

## 4. Inspect and export the actual saved results

```sh
python -m mre_engineer serve --accounting-run v1 --investigation-run v1 --pilot-run full-pilot-v4 --source-run v1 --release-run v1
```

Open http://127.0.0.1:8766 and choose Validation. No live calls are triggered by
opening, refreshing or exporting. The Investigation view may show an archived
code-version draft; this is not validation of the current controller. Keep that
label in a demo rather than spending again merely to remove it.

In a second terminal, export:

```sh
python -m mre_engineer dossier --run-name submission-v1 --pilot-run full-pilot-v4 --source-run v1 --release-run v1
```

Outputs: outputs/dossiers/submission-v1/evidence.json and evidence.html. Open the
HTML directly; it includes no scripts or external dependencies. Confirm source
links, narrow claim scope, negative results and raw-versus-effective distinctions.

## Demonstration and defensible claims

Three-minute story: published experiment -> proposed claim -> Meta-selected source/
numerical check -> critique and revised or retained answer -> baseline comparison
and auditable export. Show the actual run; do not stage a correction if none occurs.

Ground truth here means exact published fields, arithmetic and bounded support
labels, not independent original telemetry. Three new tasks share the already used
Yu source; KSC publications are related reports, not independent trials. Public
literature may occur in pretraining. Transcribed +/- values are not automatically
confidence intervals. Source predictions and lifetime projections are not measurements.

No interview is required for this source-field benchmark. Its best possible result
demonstrates bounded evidence-review capability. Calibrated fault prediction, the
optimal next experiment, reduced researcher workload and NASA adoption are not
established by this workflow. Future stronger claims require relevant outcome data.

For a public submission, retain source attribution, expose actual contributions and
licenses, exclude .env, local source PDFs, raw downloads and private account data.
Review selected evidence exports before committing them; generated outputs remain
gitignored. This documentation does not publish or submit the repo automatically.
