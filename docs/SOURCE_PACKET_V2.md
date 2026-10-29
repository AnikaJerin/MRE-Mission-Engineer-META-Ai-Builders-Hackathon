# Thermal-clock smoke: model found an omitted premise

Owner reported 88 offline tests passing, a release audit with three code-corrected
decisions, and a completed five-request source smoke. The 3 corrections are the
three model methods' decisions on the same unsupported-unit case, not three
independent errors or proof of improved Meta reasoning.

Inspecting smoke-v1 shows the model returned 14 h correctly and declined to verify
1600 C because the packet had no temperature. The critic retained that distinction.
This is a defensible evidence-bound response. The raw supported/not_established
score was based on an incomplete task packet. Do not report it as a model failure.

Primary source rechecked online, 28 Oct 2026:
https://ntrs.nasa.gov/api/citations/20250004626/downloads/MRE_paper_revision_clean.pdf
Table 4 header explicitly specifies time at 1600 C. Table 5 explicitly identifies
the 12-hour row and resistance at 1600 C. The latter packet also omitted its
specimen-duration context, so v2 supplies that header/row information before a full
paid evaluation. Projection-status and rate-comparison packets retain their labels
and source limitations; they do not establish hardware qualification or degradation.

Versioned v1 files and old frozen scores remain intact. v2 lives under
benchmarks/source_ground_truth/v2. Archived source results are displayed with a
code-version label and an incomplete-context annotation when applicable. Raw model
scores are not retroactively changed. The original six-case pilot is unaffected.
Five offline regression tests were added. Assistant inspected syntax only and did
not run the project, tests or APIs.

Owner commands:

```sh
python -m pip install --no-deps -e .
python -m unittest discover -s tests -v
python -m mre_engineer source-report --run-name smoke-v1
python -m mre_engineer source-freeze --name sources-v2
python -m mre_engineer source-run --run-name smoke-v2 --freeze-name sources-v2 --task-id thermal-clock --allow-api-call
python -m mre_engineer source-report --run-name smoke-v2
```

Old-report inspection is local only. The smoke command permits at most five paid
requests/$1.25 local reservation envelope. Check the result before doing a full
run. Source-pilot-completed means execution completed, not that every answer is
correct or that revision helps. If the corrected task is well-posed and scores
still disagree, retain those results rather than changing the key to make Meta win.

After successful execution of the corrected smoke (and review of any mismatches):

```sh
python -m mre_engineer source-run --run-name v2 --freeze-name sources-v2 --allow-api-call
python -m mre_engineer source-report --run-name v2
python -m mre_engineer serve --accounting-run v1 --investigation-run v1 --source-run v2 --release-run v1
```

Full run permits twenty paid requests/$5 local reservation envelope. Read the new
Validation view and export with:

```sh
python -m mre_engineer dossier --run-name submission-v2 --source-run v2 --release-run v1
```

This supersedes sources-v1/v1 command names in FINISH_MVP.md. No need to repeat the
30-request six-case pilot or redo Day 1/Day 2 accounting. Do not rerun release-audit
with the existing v1 name; its saved audit is still available.
