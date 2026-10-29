# Schema failure in smoke-v1

The saved response completed successfully at the provider, then failed the local
decision schema. Its settled cost was $0.017852. The old trace did not retain the
submitted JSON or schema paths, so its exact field error is unavailable. The zero
model scores mean unavailable valid outputs, not three completed wrong decisions.
The server startup message is normal; the investigation UI shows the production
investigation, not this comparator pilot.

The evaluation now requests provider-constrained JSON and records submitted output
plus field-level rejection details. Local validation is retained. There are no
automatic paid retries or changes to labels to reward the agent.

Owner commands, from the activated project environment:

```sh
python -m pip install --no-deps -e .
python -m unittest discover -s tests -v
python -m mre_engineer eval-freeze --name pilot-v2
python -m mre_engineer eval-run --run-name smoke-v2 --freeze-name pilot-v2 --case-id historical-3h --allow-api-call
python -m mre_engineer eval-report --run-name smoke-v2
```

This smoke comparison permits five unique paid requests, with a $1.25 local
reservation envelope. This is not a provider-enforced billing cap. Stop after this
smoke test and inspect the result before a full pilot. If it fails, inspect
outputs/evaluations/smoke-v2/events.jsonl for model_submission,
submission_rejected and failed. Do not blindly repeat paid calls.

Do not overwrite the original freeze or failed run. Updating evaluation code makes
old reports stale against the current code by design; the original report and
events remain on disk. No ledger reconciliation is needed for the settled smoke-v1
request. No production investigation module or its successful v1 trace is changed.

Implementation was inspected statically only. Owner must run the tests and live
smoke command; neither live compatibility nor model improvement is established by
this patch. A completed pilot still measures narrow readiness labels, and expert
review remains necessary for a next-experiment usefulness claim.
