# Continue diagnosis without inventing a settled charge

Owner reported 66 offline tests passed after the HTTP diagnostics patch. That does
not establish live provider compatibility. The previous failed request has no
retained provider status/body, and dashboard totals cannot identify its charge.

The new local-only acknowledgement is an alternative to provider reconciliation.
It retains state=unresolved, the full $0.25 accounted reservation and all prior
events. It is NOT a statement that actual cost was $0.25 or zero. The reservation
is an estimate, not a guaranteed upper bound. Acknowledged unknown costs count
toward the local cap; new failures block again unless separately acknowledged.
Active reservations and known usage above reservations cannot use this path.
Actual charges can still be reconciled later if provider evidence becomes available.

Owner commands:

```sh
python -m pip install --no-deps -e .
python -m unittest discover -s tests -v
python -m mre_engineer acknowledge-unknown-cost --request-id 21da650f3d3147b2b2c154db57d19748 --accept-unknown-cost
python -m mre_engineer api-budget
python -m mre_engineer eval-freeze --name pilot-v3
python -m mre_engineer eval-run --run-name smoke-v3 --freeze-name pilot-v3 --case-id historical-3h --allow-api-call
```

The acknowledgement command makes no network/API call. Run it only if willing to
continue with the charge still unknown. The final command makes up to five paid
attempts, stops at first failure, and records api_error with HTTP status and bounded
provider error fields when available. If it fails, share the new output; do not
repeat blindly. No API, tests or project execution was performed by the assistant.
Only static Python syntax was inspected. Three new offline tests cover this policy.

This supersedes the provider-review-only continuation instruction in
SMOKE_V2_TRANSPORT_ERROR.md. Old runs/freezes are retained; current-code replay may
mark them stale after these edits, without erasing the historical evidence.
