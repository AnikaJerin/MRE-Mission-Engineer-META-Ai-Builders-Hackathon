# Two engineering investigations and professional validation

This stage implements two complete, bounded workflows: the Yu hollow-anode review
and the KSC LR-1 core/report-comparability review. A completed workflow means source
context, original review, two genuine model-selected local checks, same-model critic,
revision/retention, equal-call control, reference audit and export are recorded.
It does not mean a real reactor was diagnosed correctly or a physical experiment ran.

The assistant authored implementation, fixtures and tests, and inspected syntax
only. No project, tests, numerical tool or paid request was executed by the assistant.
The owner must run the commands below. Do not mark T11 completed in execution until
both cases appear in the report's complete_case_ids under live-api execution mode.

## Ground truth and methods

Read engineering_cases/v1/VALIDATION_SOURCES.md and PROTOCOL.md. There are 12
constructed claims across TWO source contexts, not 12 independent cases. Several
facts and publications were previously inspected during development. The new claims
include source-qualified oxygen-balance assertions, XPS limitations, atomic versus
weight percentage, source-method ambiguity and unsupported causal conclusions.
All reference labels have source-block mappings and a stated basis. No model judges
its own prose, and no interview is required for these exact checks.

Three methods share the same original review: one-pass; critic plus additional check
and revision; and two fresh drafts plus selection as an equal-call control. Main
investigation uses five calls; control adds three unique calls. Each branch counts
five including two shared initial calls. The control gets the same returned checks,
including the critic-selected second check. This limits causal attribution to critique.
The report does not pool these results with previous pilots or silently rescore them.

Eight unique requests per case; sixteen for both; $2/$4 local reservation envelopes.
Actual token estimates may be lower. They are not provider-enforced caps. No retry
or concurrent paid run occurs automatically. Each main client permits five calls;
its control client uses three. Partial errors and unattempted cases remain visible.

Production calculations use project physics/ordinary arithmetic; the independent
reference uses Decimal/Fraction and exact SI elementary-charge/Avogadro constants,
without importing production physics. Agreement is checked before paid work. This
tests implementation consistency, not experimental accuracy. Output rounding
tolerances are frozen and are not sensor confidence intervals.

Metrics apply ONLY to the explicit ledger:
- Exact claim-label accuracy and required reference-block coverage.
- Unsupported endorsements, with denominator = claims labelled supported.
- Missed contradictions and contradiction recall, with reference contradiction count.
- False contradictions and unjustified abstentions on supported claims.
- Numeric absolute error, correct unit and frozen tolerance.
- Paired case corrections/regressions versus one-pass and matched-call control.

Null rates mean a zero denominator, not perfect performance. A known citation is
not enough: each claim must cite its mapped source blocks. This is still reference
selection, not automatic entailment of every sentence. Hypotheses and next-evidence
requests remain visible and unscored for optimality/practical usefulness.

Structured mismatches block endorsement of a review draft; raw output and its score
remain visible. Even a passing draft is released for document review only, never
hardware operation. A changed test request or fluent prose alone is not measured
engineering improvement. Preserve equal and negative results.

## 1. Owner offline checks

Stop the old server before restarting the updated UI. From the project root:

```sh
PYTHONPATH="$PWD/src" python -m unittest discover -s tests -v
PYTHONPATH="$PWD/src" python -m mre_engineer engineering-preview
PYTHONPATH="$PWD/src" python -m mre_engineer api-budget
```

Preview computes the local numeric consistency checks but makes no API calls. Both
cases should report independent_numeric_checks.passed=true. If not, fix before any
paid run. Explicit PYTHONPATH avoids the observed intermittent editable-package
discovery issue; it is not a diagnosis or permanent repair of that environment issue.

## 2. Freeze, then one complete case

```sh
PYTHONPATH="$PWD/src" python -m mre_engineer engineering-freeze --name engineering-v1
PYTHONPATH="$PWD/src" python -m mre_engineer engineering-run --run-name hollow-v1 --freeze-name engineering-v1 --case-id hollow-anode-review --allow-api-call
PYTHONPATH="$PWD/src" python -m mre_engineer engineering-report --run-name hollow-v1
```

At most eight API requests/$2 local reservation envelope. Inspect failures and
metrics before further paid work. Completed workflow does not guarantee all checks
pass; preserve mistakes rather than changing the reference key to reward the model.
To finish the second context without rerunning the first:

```sh
PYTHONPATH="$PWD/src" python -m mre_engineer engineering-run --run-name lr1-v1 --freeze-name engineering-v1 --case-id lr1-core-review --allow-api-call
PYTHONPATH="$PWD/src" python -m mre_engineer engineering-report --run-name lr1-v1
```

Another eight requests/$2 envelope. It is not necessary to also run both in a third
combined paid run. Each individual report contains a complete source-context workflow.
Combine the two verified reports locally, with no new API calls:

```sh
PYTHONPATH="$PWD/src" python -m mre_engineer engineering-combine --run-name v1 --from-run hollow-v1 --from-run lr1-v1
PYTHONPATH="$PWD/src" python -m mre_engineer engineering-report --run-name v1
```

The collection retains links to original report/trace hashes and refuses duplicate
contexts, different freezes or mixed live/test-double evidence.

## 3. UI and dossier

Inspect the combined report with --engineering-run v1 (or either individual run):

```sh
PYTHONPATH="$PWD/src" python -m mre_engineer serve --source-run v2 --release-run v1 --engineering-run v1
PYTHONPATH="$PWD/src" python -m mre_engineer dossier --run-name engineering-submission-v1 --source-run v2 --release-run v1 --engineering-run v1
```

The server command blocks until Ctrl+C; run exports in another terminal. Choose
Engineering reviews in the lunar UI. It shows actual plans, hypotheses, source and
claim mappings, independent numerical results, critic and tools. Dossier HTML has
human-readable engineering summaries, source links and expandable raw evidence.
No calls occur on page load, refresh, report or export.

The old release audit may show archived-release-policy-audit because exporter code
changed; its original pilot and deterministic policy still match. Its three code
corrections are preserved. Original submission-v2 files are not overwritten.

## Acceptance and honest status

Implementation is ready for owner verification; until the live reports exist the
two new workflows are NOT execution-complete. After each completes, record the
case ID, trace hash, reference scores and actual release status. Acceptance requires
both live workflows, not a successful test double. If a review fails a reference
check, it remains a completed but incorrect/blocked review for that metric.

T12's original six development + six independent evaluation cases remains unmet;
these twelve CLAIMS do not satisfy that independent-case requirement. A protocol
amendment may define this smaller honest MVP evaluation, but cannot retroactively
claim more data or blindness. T17 reproducibility review and T18-T20 recording,
public-repo/rights audit and submission checks are separate remaining activities.
