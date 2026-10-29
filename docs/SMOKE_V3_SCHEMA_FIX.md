# Confirmed root cause and correction

Saved smoke-v3 event: HTTP 400, invalid_request_error, param=schema,
"JSON schema keyword `uniqueItems` is not supported for structured outputs".
This is request-schema rejection, not evidence of incorrect scientific reasoning.
The previous diagnostic patch exposed the cause; offline mocks had not validated
Meta's supported JSON Schema subset.

The evaluation now sends only structural schema fields to constrained generation,
and includes the full local contract as prompt data. Local checks, labels and
scoring remain unchanged; duplicate items and oversized strings still fail.
Decision and critique both use this adapter. Two regression tests were added.
Assistant performed syntax inspection only, no tests, project or API execution.

Owner commands:

```sh
python -m pip install --no-deps -e .
python -m unittest discover -s tests -v
python -m mre_engineer acknowledge-unknown-cost --request-id d1ec897beab141879e4bfc07e83dc047 --accept-unknown-cost
python -m mre_engineer eval-freeze --name pilot-v4
python -m mre_engineer eval-run --run-name smoke-v4 --freeze-name pilot-v4 --case-id historical-3h --allow-api-call
```

Acknowledgement retains unknown billing and the full $0.25 local reservation;
it does not assert zero cost or independently settle billing. The last command
makes up to five paid attempts, with a $1.25 local reservation envelope. Stop on
any failure and inspect it. Historical runs and ledgers are not rewritten by this
patch. Live acceptance is not yet verified.
