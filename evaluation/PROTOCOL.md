# Pilot-v1 protocol: does challenge/revision add value?

## Pilot-v4 structural-schema amendment (2026-10-28)

smoke-v3 recorded HTTP 400, param=schema: JSON schema keyword uniqueItems is not
supported for structured outputs. No model decision was produced. The wire schema
now contains only type/enum/object properties/required/additionalProperties/items;
enum-only string nodes receive explicit string types. The full unchanged local
contract is supplied as prompt data for every model condition and still validates
every submission, including uniqueness and length/cardinality. No deduplication,
normalization, auto-repair or relaxation of scoring is performed. Changes are
symmetric across conditions and require a new freeze. Live compatibility remains
owner-verifiable; offline doubles alone cannot establish provider acceptance.

## Pilot-v2 transport amendment (2026-10-28)

The preserved smoke-v1 API response completed, but its submitted decision failed the
local schema. That implementation did not retain the submission or field errors;
the exact offending field cannot be reconstructed. This is an execution failure,
not evidence that the scientific decision was incorrect.

For new freezes, every model condition uses Responses text.format with strict
json_schema constrained output, rather than pseudo-function submissions. See
https://dev.meta.ai/docs/structured-output . Local strict JSON, schema and citation
validation remain mandatory. No aliases, default answers, automatic repair or paid
retries are added. Cases, answer labels and acceptance criteria are unchanged.
Submitted output and field-level rejections are recorded without HTTP headers,
hidden reasoning or the active API credential. Counts distinguish failed outputs
from branches not attempted after an earlier failure; unavailable outputs still
receive no accuracy credit. Preserve pilot-v1/smoke-v1, and use a new freeze/run.

This is a development stress pilot, not an independent clinical/hardware/scientific
validation study. Freeze this protocol, six input packets, separate answer key and
evaluation code before new paid calls. Do not tune prompts/labels to make the loop win.

## Dataset and target

Two published historical summaries (3 h, 12 h) share the SAME Yu et al. 2025 paper,
reactor design and author group. Four constructed metadata/input controls are not
laboratory measurements. They include complete, missing-calibration, unsupported-unit
and out-of-scope conditions, so blanket abstention cannot pass every case. These are
six CASES, not six independent reactor trials. The existing one-hour run is already
inspected development evidence and is excluded from the scored pilot.

The automatic target is the review-readiness decision given the SUPPLIED record
presence flags, supported units and scope, plus exact missing-record identification.
Specifically, it asks whether record metadata permits starting an engineer-reviewed
reconstruction of measured gas/charge, not whether all nominal arithmetic must stop.
Flags do not certify a record's physical quality. True flags in constructed controls
are accepted as supplied only for this software contract probe. Missing flags in
historical packets describe our packet, not what NASA or the authors possess.

Required record categories: current record, gas measurement record, gas calibration,
reference conditions, measurement uncertainty and gas-to-mass documentation. Voltage
is not a compulsory input solely for oxygen/charge accounting; do not demand unrelated
records as a blanket ritual. Nominal scalar arithmetic remains possible with explicit
assumptions even when measured-trace reconstruction cannot be validated.

## Paired methods, same evidence

All methods receive the identical packet and deterministic local check outputs. No
condition gets additional data or a secret answer-key field. This pilot ablates the
reasoning/revision step; it does not measure the value of dynamic tool selection.
It uses a frozen evaluation decision contract and evaluation prompts, not the unmodified
production controller. Results from this component probe must not be described as an
end-to-end benchmark of the deployed agent or as validation of its original prose.

1. Fixed checklist: scope, explicit unit/numeric checks, required-record presence.
2. One-pass Meta: one structured decision.
3. Challenge/revision: reuse that EXACT initial decision, one separately prompted
   same-model critic, one revision. Three requests including the shared initial.
4. Compute-control: reuse the initial, obtain an independent second draft, then select
   a grounded decision from the two. Three requests including the shared initial.

Five UNIQUE paid requests per case, not seven: initial is shared. All conditions use
the same model, output schema, per-request output cap and data. Actual tokens/costs
may differ; this is call-count matching, NOT exact token/compute equivalence. Call
order and shared starting state are limitations; no statistical significance claim.

## Predeclared measurements

- Exact decision match against the record-presence/input/scope key.
- Exact missing-input set match (empty for rejected input/scope).
- Invalid output/workflow failures as failures, never silently excluded.
- Paired corrections and regressions versus one-pass, plus comparison with the
  three-call resampling control and the fixed checklist.
- Report by historical versus constructed group and source family. No p-values,
  population coverage, failure-probability calibration or independent scientific
  accuracy inferred from this small dependent sample.

These narrow tasks can be solved by a checklist. Matching it is not a scientific
breakthrough; outperforming a weak model baseline is insufficient to claim unique
value. Record equal/negative results without changing the scoring criterion.

## Human review needed for the actual next-test claim

Export blinded candidate decisions with evidence packet and local checks. A qualified
reviewer should score each on 0/1/2 anchored scales:

- Factual grounding: unsupported/wrong claims (0), material ambiguity (1), all claims
  justified and appropriately conditional (2).
- Diagnostic relevance: cannot distinguish rivals or misstates readiness (0), partly
  useful request (1), useful discriminating test OR justified evidence acquisition (2).
- Practical prerequisites: missing critical constraints (0), incomplete (1), clear,
  feasible prerequisites with no hardware clearance claim (2).
- Burden/omissions: unjustified demands or major omissions (0), some avoidable work
  (1), necessary evidence with no consequential omission (2).

Do not score by preferred prose, length, forced revision or the agent's own judgment.
Review items start with null scores; they are not zero and not completed reviews.
The operator should hide review_key.json from reviewers. Owner review is not blind
independent expert review if they know method identities. Disagreements and reviewer
qualifications must be retained. No automatic score substitutes for next-test utility.

## Decision rule for the claim

Without paid comparator results: NOT YET TESTED. With automatic results alone:
only the narrowly scoped software decision finding may be stated. With no qualified
review: next-test usefulness remains UNVALIDATED. A test-card rewrite or additional
citations alone do not establish improved decisions. More prospective lab cases are
required for production benefit or researcher time-saving claims.
