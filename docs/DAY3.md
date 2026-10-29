# Day 3: the first Meta investigation loop

The owner reported Day 2's 31 tests passing and demonstrated the saved historical
accounting report in the lunar UI. Day 3 code has been authored, not run by the
assistant. Tests use offline doubles, not actual model performance evidence.

## 1. Local checks first - no API costs

Stop an old server with Ctrl+C. In the MRE virtual environment, from the repo root:

```sh
python -m pip install --no-deps -e .
python -m unittest discover -s tests -v
python -m mre_engineer investigation-preview --accounting-run v1
python -m mre_engineer api-budget
```

The suite now contains 49 tests. Preview reads the current historical case, validated
Day 2 report and tool definitions. No key, network request or calculation is needed
for preview. It should report a maximum of five requests, two local checks and a
$1.25 local reservation envelope. A current Day 2 report is required.

Day 2 numerical code/inputs have not intentionally changed in this step. You should
not need to regenerate accounting. If your own edits made its report stale, run a
new accounting run name and use that name below instead of silently reusing v1.

## 2. Put the key in your own terminal

Do not paste your API key into chat, source files or the browser. For the Mac's zsh:

```sh
read -r -s 'MODEL_API_KEY?Paste Meta API key, then press Enter: '
export MODEL_API_KEY
```

Run the first line, paste the actual key at its hidden prompt, and press Enter.
Then run the export line. MODEL_API_KEY is the variable NAME; do not replace its
name with your key. No value is written to the repository. If already exported in
this shell, you do not need to enter it again.

## 3. One explicit paid investigation

```sh
python -m mre_engineer investigate --run-name v1 --accounting-run v1 --allow-api-call
```

This sends the public historical case facts and tool results to Meta. It does not
upload source PDFs, private documents, raw logs or your local source paths. It can
make at most FIVE requests to `muse-wonder-1.0`, reserving $0.25 per request locally.
Maximum local run envelope: $1.25. This is an estimated-cost safeguard, not a
provider-enforced billing cap or a guarantee about credit availability.

Expected successful status: `completed-draft-investigation`, five request attempts,
two locally executed checks. It may also stop as failed if the model does not select
a tool, violates a schema, returns invalid citations, times out or omits usage.
No tool call, plan change, new measurement or success is fabricated to hide a failure.
The revised test card may legitimately be retained rather than changed.

The run is stored under ignored `outputs/day3/v1/events.jsonl`. Existing run names
are never overwritten. For a manual retry AFTER reviewing failure and billing, use
a fresh run name such as v2. No automatic retry or paid continuation occurs.

## 4. Display the recorded run

```sh
python -m mre_engineer serve --accounting-run v1 --investigation-run v1
```

Open http://127.0.0.1:8766 and choose Investigation. The local page displays:

- Original draft, unconfirmed alternatives and source/tool references.
- Same-model critic's challenge and its separate tool evidence.
- Revised draft (or retained test card) and changed fields.
- Actual recorded API/tool steps and local hash-chain status.
- Partial/failed/stale status without inventing a final plan.

Refresh and export make NO new paid requests. The dashboard does not start paid runs
in this version; the explicit terminal command is the only live entry point. For a
run started from a second terminal, refresh after it finishes to inspect its record.
No API key is ever entered into the UI. Export evidence JSON includes the recorded
investigation and limits; it is not a scientific approval document.

## Billing uncertainty

```sh
python -m mre_engineer api-budget
```

An interrupted/timed-out request may still be billed. Its reservation remains
unresolved and blocks further requests. Review the Meta provider dashboard first.
Only after checking the actual charge, resolve the specific ledger entry:

```sh
python -m mre_engineer reconcile-request --request-id REPLACE_WITH_REQUEST_ID --actual-usd REPLACE_WITH_REVIEWED_AMOUNT --confirm-provider-review
```

Use the request ID shown by api-budget and the charge YOU verified. Do not enter
zero merely to unblock work. The reconciliation records an owner-entered estimate,
not independent verification. Do not delete the ledger or an active lock to reset
spending. OS file locks release when the process exits; an empty lock file is normal.

The $100 local MRE limit does not include ECLIPSE, other applications or deleted
ledgers. Actual account balance and pricing must be monitored with the provider.

## Day 3 exit gate

1. Offline contract, budget, replay and failure tests pass.
2. The owner completes at least one REAL Meta-selected local check and receives
   a source/tool-linked draft; offline doubles do not satisfy this gate.
3. The full loop records the critic's different check and a justified revision or
   retention. If it stops early, preserve that failure and fix the specific issue.
4. The UI/export show the real record with no scientific certification claim.

Next-test usefulness, consequential weaknesses beyond a baseline and researcher time
savings are NOT established by a completed loop. Independent cases, baseline
comparison and qualified review remain later validation work.
