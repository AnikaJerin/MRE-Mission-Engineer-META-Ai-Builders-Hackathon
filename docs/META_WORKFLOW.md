# Meta integration and limits

## Verified API interface (28 October 2026)

- https://dev.meta.ai/docs/tool-calling
  Responses API flat function definitions; `function_call` output; matching
  `call_id` in `function_call_output`; `previous_response_id` for continuation.
  Only `tool_choice="auto"` is supported. The model may choose no tool.
- https://dev.meta.ai/docs/quickstart
  Endpoint https://api.meta.ai/v1/responses and environment variable MODEL_API_KEY.
- https://dev.meta.ai/docs/pricing-rate-limits
  Wonder standard input $4/M and output $20/M tokens. Cached inputs are
  conservatively accounted at full input price. Rates can change; recheck before
  live use. No provider web/image/voice tools or Contributor mode are enabled.

## Five model requests

1. Proposer chooses one of three allowed checks: historical charge accounting,
   oxide inventory for an explicit reference mass, or recorded measurement readiness.
2. Application validates/executes the check, returns its result; proposer submits
   an initial structured next-test draft with at least two unconfirmed explanations.
3. Separately prompted same-model critic selects a different allowed check.
4. Application returns that result; critic submits a structured challenge.
5. Proposer receives the initial draft, challenge and tool evidence; submits a
   revised draft or retains the card if justified. No change is forced for the demo.

The test-change indicator compares category, question, measurement and prerequisites.
New citations or explanatory rationale alone are not presented as a changed test.

Structured submit functions only capture schema-validated proposals. They do not
execute a physical test or control equipment. Only two actual local checks execute.
If tool_choice auto produces no check, the run is failed rather than pretending a
check occurred. Unexpected tools/arguments, duplicate/nonfinite JSON, more than one
tool, unknown citations and missing tool references are rejected before execution.

## Scope of genuine Meta reasoning

The model chooses checks, proposes rivals, identifies a weakness and drafts a
response to evidence. The application does the arithmetic, checks argument/citation
structure, records the trace and enforces cost/action limits. Linkage checks do not
establish whether a causal interpretation or diagnostic proposal is scientifically
sound. All plans are drafts requiring qualified engineer review; no risk scores,
operating setpoints or hardware actions are supported by the contract.

The readiness check inspects recorded missing-input fields; it does not discover
new calibration records. The scientific sources and reported outcomes are historical
development context and can be familiar to the model. Neither self-critique nor
historical replay is independent expert review or a new research discovery.

## Cost, data and interruption

The application allows one paid investigation at a time, up to five requests and
3,000 output tokens per request (including reasoning under provider semantics).
A conservative byte-envelope check limits context growth; this is a heuristic,
not the provider's tokenizer. Each request reserves $0.25 before transport and
settles from returned usage. Missing usage, transport uncertainty or charges over
reservation block subsequent spending until provider review. The run envelope is
$1.25 and local project estimated-cost limit $100. This cannot cap provider billing,
account for other software or survive deletion of its own ledger.

No automatic retries, model switching, URL redirects, tool-generated shell commands,
source-document uploads or arbitrary file/network tools are allowed. Keys are read
only from the owner's shell and not stored. HTTP error bodies/headers and hidden
reasoning are not persisted. A failed request can still be charged.

The UI is read-only; only the explicit CLI --allow-api-call starts this work. It
shows recorded steps rather than simulated activity. Source/evidence text is treated
as untrusted data in prompts, and model content is rendered with textContent in the
browser. Local trace hashes support consistency checks, not cryptographic attestation
against a user who can rewrite the entire trace and its hashes.
