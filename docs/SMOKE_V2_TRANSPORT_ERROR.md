# smoke-v2: request failure before any model submission

The saved trace ends after api_reserved with a generic request failure. No response,
HTTP status or provider error body was retained. It is therefore not possible to
tell retrospectively whether the failure was a schema rejection, authentication,
rate limit, connection failure or another provider error. Fast failure alone is not
proof of an HTTP 400. Do not interpret unavailable model outputs as wrong decisions.

The client now records HTTP status plus bounded error type/code/param/message, or
a non-HTTP error category. It excludes request bodies, HTTP headers and raw HTML,
redacts the current API credential and never retries automatically. This patch
improves diagnosis; it does not establish that the unknown original fault is fixed.

Owner should first install and run offline tests:

```sh
python -m pip install --no-deps -e .
python -m unittest discover -s tests -v
python -m mre_engineer api-budget
```

Review the Meta provider dashboard for the request at 2026-10-28 10:57:42 UTC.
If its actual charge can be established, reconcile that amount (USD) using:

```text
python -m mre_engineer reconcile-request --request-id 21da650f3d3147b2b2c154db57d19748 --actual-usd VERIFIED_AMOUNT --confirm-provider-review
```

VERIFIED_AMOUNT is a placeholder, not a command-ready number. Do not assume zero
or clear/delete the ledger if the request-specific amount is unknown. Local $0.25
is a reservation, not proof of a charge. Resolve billing before a new paid attempt.

After offline tests and billing review, new diagnostic attempt commands are:

```sh
python -m mre_engineer eval-freeze --name pilot-v3
python -m mre_engineer eval-run --run-name smoke-v3 --freeze-name pilot-v3 --case-id historical-3h --allow-api-call
```

It stops on the first failure; at most five requests/$1.25 local reservation envelope.
Inspect api_error in outputs/evaluations/smoke-v3/events.jsonl if it fails; do not
repeat again without interpreting that error. Old freezes and traces are retained.
Changing the shared client makes old reports stale relative to current code; it
does not alter or erase their historical evidence. Production prompts and scoring
criteria are unchanged. No tests, project execution or paid calls were run by the
assistant for this patch; syntax inspection only.
