# Validate whether challenge/revision adds value

Implementation prepared; not executed by the assistant. Existing Day 3 evidence has
been manually audited in `docs/CURRENT_RUN_AUDIT.md`. That audit does not establish
an improvement over a baseline. Do not present the test-card rewrite alone as proof.

## What is compared

The same evidence packet and local check outputs go to a fixed checklist, one-pass
Meta, three-request challenge/revision, and a three-request resampling/selection
control. The starting response is shared: five UNIQUE API requests per case.
This isolates revision on fixed evidence; it does not evaluate dynamic tool selection.
The frozen decision contract/prompts differ from the production controller: this is
a component probe, not end-to-end validation of the original agent's next-test drafts.
Token counts may differ; the control matches calls, not exact compute.

Six predeclared cases: two historical summaries (3 h and 12 h) from the SAME paper,
plus four clearly labelled constructed controls. They are not six independent lab
experiments. Fully supplied and missing-record controls prevent blanket abstention
from appearing correct on every case. All cases remain development stress cases.

Automatic scoring checks record-readiness, supported units/scope and exact missing
record sets. Next-test usefulness requires qualified human review and is NOT scored
by another language model or inferred from those automatic labels.

## 1. Offline checks and freeze - owner runs

From the repo root, in the existing virtual environment:

```sh
python -m pip install --no-deps -e .
python -m unittest discover -s tests -v
python -m mre_engineer eval-preview
python -m mre_engineer eval-freeze --name pilot-v1
```

The authored suite now contains 59 tests. The assistant has not executed them.

Freezing records hashes of inputs, the separate answer key, protocol and evaluation
code BEFORE paid comparisons. Files are under `evaluation/`. Do not edit prompts,
labels or scoring to make results look better. A freeze cannot be overwritten.
Code/data changes require a new freeze and must be disclosed when comparing runs.
The model never receives answer_key.json or expected outcomes. Descriptive case IDs
are replaced by opaque references in model prompts.

## 2. One-case paid smoke comparison first

With MODEL_API_KEY already exported in YOUR terminal:

```sh
python -m mre_engineer eval-preview --case-id historical-3h
python -m mre_engineer eval-run --run-name smoke-v1 --freeze-name pilot-v1 --case-id historical-3h --allow-api-call
python -m mre_engineer eval-report --run-name smoke-v1
```

Up to five unique requests, local maximum reservation $1.25. Inspect results before
running more. This one-case smoke comparison is not a general performance finding.
No automatic retries or paid continuation after a failure. Existing run names cannot
be overwritten. API uncertainties block further work through the shared MRE ledger.

## 3. Full paired pilot, when the smoke comparison works

```sh
python -m mre_engineer eval-run --run-name pilot-v1 --freeze-name pilot-v1 --allow-api-call
python -m mre_engineer eval-report --run-name pilot-v1
```

Six cases, at most 30 unique requests and $7.50 in local reservations. Actual usage
may be lower; this is not a provider billing cap or account-balance guarantee. This
uses the existing MRE ledger; other software's costs are not included. Do not combine
the earlier smoke case with this run as an additional independent observation.

## Saved outputs

`outputs/evaluations/<run-name>/` contains:

- `report.json`: case-wise outputs, exact automatic scores, corrections/regressions,
  invalid/unattempted counts and an explicit unvalidated next-test claim.
- `events.jsonl`: actual paid attempts and generated decisions.
- `review_packets.json`: randomized candidate IDs and evidence for human review.
- `review_key.json`: private method mapping; hide it from the reviewer.
- `review_template.json`: null review scores, never prefilled positive scores.

Use 0/1/2 anchored rubric in `evaluation/PROTOCOL.md` and retain reviewer competence,
notes and disagreements. The export alone is NOT a completed independent review.
No aggregate human score is computed until a later explicit review-import feature.

## Interpret the results honestly

`comparison_complete` means all selected method outputs are valid, not that any
method is scientifically correct. `decision_exact` matches this narrow predeclared
contract only. Invalid/failed or unattempted outputs remain visible in the selected
denominator. Cases share sources and constructed families; report grouping explicitly.

Equal performance means no measured gain on that task. Regressions count against the
loop. Beating one-pass while matching the resampling control can reflect additional
compute rather than critique-specific value. Matching a checklist on simple metadata
tasks does not establish novel scientific capability. Even positive narrow scores
leave next-test utility, time savings and reactor generalization unvalidated.

The existing Day 3 run and Day 2 hashes are preserved: this adds a separate evaluation
module rather than silently changing the agent that produced v1.
