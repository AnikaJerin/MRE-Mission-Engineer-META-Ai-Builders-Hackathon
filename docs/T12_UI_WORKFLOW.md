# Start-to-finish UI test: T12 and factual correctness

Implementation was authored and syntax-inspected by the assistant. No project,
tests, local numeric tools, server or API requests were run by the assistant. The
owner must execute the verification below; T12 remains execution-pending until its
live reports actually satisfy the gate.

## 0. One-time terminal setup

From the MRE repository root, in its activated virtual environment:

```sh
PYTHONPATH="$PWD/src" python -m unittest discover -s tests -v
```

If this fails, send the failure before making paid requests. No editable reinstall
is needed with explicit PYTHONPATH. Existing reports are preserved. Then set the
key in this SAME terminal (zsh). Do not paste the key into chat or the browser:

```sh
read -r -s 'MODEL_API_KEY?Paste your Meta API key, then press Enter: '
export MODEL_API_KEY
PYTHONPATH="$PWD/src" python -m mre_engineer serve --port 8768 --source-run v2 --engineering-run versioned-v3
```

Open http://127.0.0.1:8768. Leave the terminal running. If 8768 is occupied, stop
its old server with Ctrl+C or choose another port and open the matching URL.
Starting the server, opening a page, changing tabs and refreshing NEVER start an API
request. Paid work starts only from a Run click with the credit checkbox selected.

## 1. Start & validate: inputs

The first view is **Start & validate**. This MVP accepts reviewed, supplied case
packets; it does not upload arbitrary reactor logs or certify arbitrary new papers.
Inputs are split, case/run scope, freeze name, run name, export name and consent.
The API key stays in the server environment; it never travels to the browser.

Choose **Development — 6 known readiness cases**, then **All 6 cases**. Expand a
case to see its actual question, source receipt, supplied records, source-family and
numeric-task assumptions. Two historical summaries and four constructed controls
are explicitly labelled. The supplied evidence determines the answer; reference
labels are held outside the model prompt. Constructed record flags are software
fixtures, not real calibration receipts.

## 2. Check sources & arithmetic locally — free

Click **Check sources & arithmetic locally**. Expect a passed local-contract result
and two numerical tasks showing production and independent Decimal/Fraction values.
The charge check uses the NTRS-reported nominal 5 A / 8 h batch under four-electron
ideal current allocation. The annual-target conversion uses a declared 8760-hour
year. Neither is a measured oxygen yield. If they disagree, do not run paid work.
No numeric task is requested for nonnumeric source/readiness questions: value must
be null, unit not_applicable. See Sources and ground-truth panel for all URLs/limits.

## 3. Freeze — free, once

Enter **t12-v1** in Freeze name and click **Create freeze — no API**. Expect the
freeze name/hash and development/evaluation pending gates. A freeze is immutable;
if it already exists, use the matching current freeze rather than recreating it.
If data or reasoning code changes, create a new freeze and preserve prior reports.
Do not adjust code/keys after seeing evaluation results and still call that a fresh
unseen holdout. Evaluation starts remain in an append-only local attempt journal.

## 4. Development run — explicitly paid

Keep Development / All 6 cases. Run name: **dev-t12-v1**. Check credit consent and
click **Run selected workflow with Meta** exactly once. Expect:
- The button disables; a live case ID/event status appears and polls saved local state.
- Up to **42 unique API requests**, **$10.50 local reservation envelope**.
- Each case has a selected check, original answer, same-model critic, revision and
  equal-call resampling control. Main client uses four calls; control uses three.
- A complete six-case report appears in Saved T12 report, with verdict and reference
  audit for each method, numeric task checks, missing records, sources and next request.

No request is retried automatically. A failed case stops later paid cases; invalid
and unattempted outcomes stay visible. **Stop before next request** does not cancel
or erase a request already in flight. The ledger retains uncertain costs. Read
errors and billing before starting another run; a new name is not permission to
hide failures. Accuracy can equal baseline or be lower; that is a result.

A single-case smoke scope is available, but adds cost and does not satisfy the
six-case split gate. To minimize calls, use All 6 after offline tests pass.

## 5. Evaluation run — explicitly paid, after development

After the complete development batch, choose **Evaluation — 6 new source-grounded
tasks**, **All 6 cases**. Keep the SAME **t12-v1** freeze. Enter **eval-t12-v1** as
new run name, select credit consent again and click Run once. The host requires a
complete live development batch under this freeze before evaluation.

Expect another maximum **42 requests / $10.50 reservation**, with case-level
references, all errors and grouped results. Both splits together: at most 84 requests
and $21 local reservations; actual token estimates may be lower. These are not
provider-enforced caps or account balance. Earlier project spending is additional.

T12 gate becomes **execution complete** ONLY if six development and six evaluation
workflows finish under one current freeze in live-api mode. This does not require
100% accuracy; errors remain scored. The development and evaluation splits test
different aspects and their accuracy is never pooled. Six evaluation tasks share
three source families; they are not six independent reactor experiments.

## 6. What to inspect as output

Select **eval-t12-v1** in Saved T12 report. Read:
1. Actual request count/cost and frozen protocol.
2. Checklist, one-pass, revision and resampling verdict accuracy, valid coverage,
   numeric numerator/denominator, unsupported endorsements and missed contradictions.
3. Each case's original/revised/control answer, reference verdict and written basis.
4. Actual tool receipt, critic, independent calculations and source references.
5. Paired corrections AND regressions; equal results do not prove critic advantage.

The original engineering investigations remain in **Engineering reviews** with their
separate historical code versions. Legacy five-request counter is not T12 activity.
No score validates every rationale sentence or proves an optimal next experiment.

## 7. Export — free

Enter a new export name, e.g. **t12-submission-v1**, and click **Create evidence
dossier — no API**. Download HTML and JSON from the links that appear. They contain
T12 split data, current completion gates, attempt history, sources/protocol and saved
case-level results alongside the earlier pilots/investigations. A report can be
exported while pending; its gate stays pending. Do not present it as completed.

Exports are stored at outputs/dossiers/<export-name>/evidence.html and evidence.json.
If a name already exists, choose a new name; old exports are immutable. Opening the
HTML is read-only. To reproduce CLI actions, use t12-preview, t12-freeze, t12-run
--split development/evaluation, and t12-report. Example:

```sh
PYTHONPATH="$PWD/src" python -m mre_engineer t12-report --run-name eval-t12-v1
```

## Acceptance and remaining boundary

Functional T12 inputs, independent arithmetic, references, baseline/control methods,
trace, UI actions and export are implemented. Live execution/accuracy waits for the
owner's runs. Factual correctness means bounded reference agreement. No interviews
are needed for these checks, but optimal-test utility, physical predictions and
production benefit remain unvalidated. T17 clean setup review and T18–T20 demo,
public repository/rights and submission checks remain separate tasks.
