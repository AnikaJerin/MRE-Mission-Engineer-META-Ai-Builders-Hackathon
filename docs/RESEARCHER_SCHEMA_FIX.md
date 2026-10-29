# Researcher review schema fix

The owner's first input-driven assessment, `842eff35cc2d4292aa3a9f6d34def2e2`,
retained correct conditional charge accounting but stopped on its second API
submission. The saved `submit_experiment_review` arguments contained the JSON
string `"False"` for `ready_for_hardware_operation`, whereas the local schema
required the boolean `false`. This was an output-contract failure, not a missing
user-input field or an arithmetic disagreement. The original failed trace remains.

Hardware authorization is now explicit application policy: reports have the
top-level boolean `ready_for_hardware_operation: false`. The model no longer
submits that flag. Its review contract instead requires the string
`review_scope: "document_review_only"`. The raw model output is still validated;
incorrect types/scopes are rejected, without coercion or automatic paid retries.
The UI progress description now explicitly distinguishes a stopped assessment
from a completed review with saved findings.

Two owner-run regression tests cover the code-owned authorization policy and
rejection of the wrong scope type. No project, tests, build, server or API was
run by the assistant. Restart the backend after installing this source change.
Use a fresh assessment to verify the live path; opening the old saved run should
continue to show its original failure, not a rewritten success.

For the same supplied values (0.5 A, 1 hour, 0.07 g, same interval), expected
conditional accounting remains 1800 C, approximately 0.149236 g ideal oxygen and
46.9055% collected/ideal. Optional unknown context remains an evidence gap. A
successful full cycle must also show first review, critic and final review.
