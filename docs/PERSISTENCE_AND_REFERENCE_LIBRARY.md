# Persistent workspace, evidence library and assessment audit

## What the reported error means

The screenshot's 'Evidence could not be loaded' message was a generic GET-resource error, not proof of invalid form values. Inspection found a completed assessment `9611e84522054303ba3c3271c2fecf54` on disk: five API requests, six final dimensions. Read-only requests to the owner's already-running backend returned HTTP 200 for both that report and the workspace. Its local report/event hash chain verified and the then-current implementation matched. The original transient GET failure could not be reproduced; its exact historical cause is not established.

Two concrete UI issues were found: a successful report load did not clear an earlier error notice; the form and selected report lived only in React memory. This change clears stale notices on successful load, restores persisted state and opens the last saved report without rerunning it. Future read failures identify the requested route and incident ID; sanitized diagnostics contain code locations/exception type, not submitted inputs or API keys.

The completed example supplied oxygen/current/time but no resistance endpoints, wall loss, thermal-cycle or endurance measurements. Consequently, its material/electrical/endurance evidence gaps are appropriate. A database cannot supply measurements of the user's actual reactor.

## What persists

| State | Storage | Reload behaviour |
| --- | --- | --- |
| Current form, import/example provenance, selected report and view | `data/workspace/mre.sqlite3` | Autosaved after a short typing pause and restored after browser/backend restart |
| Unsaved recent form changes | Browser local-storage backup | Recoverable when its server revision matches; another tab cannot silently overwrite a newer server draft |
| Completed/failed assessment and exact input | `outputs/assessments/<id>/report.json` | Immutable replay; no paid request to open |
| Original answer, tool calls, critic and revision | Same report and `events.jsonl` | Hash-chain verification before replay |
| Reviewer's recorded decision | Separate review receipt | Does not rewrite model output |
| Versioned reviewed source library | SQLite evidence versions | Seeded locally from packaged reviewed references at backend startup; historical versions retained |
| Unknown billing reservations and accounted usage | Existing API ledger | Remains intact; not reset or settled by the new database |

The database contains drafts and reference evidence, not credentials or prewritten case verdicts. API credit consent is never restored. A new paid assessment always needs a new explicit action. It does not automatically repeat after refresh, restart, a failed display request or database initialization. The application makes no source-download or Meta call to initialize the database.

SQLite requires no database server or extra pip package. The database directory is excluded from Git. Keep both `data/workspace` **and** `outputs` when backing up or moving the application. For a simple file backup, stop the backend first, then copy those directories; do not delete them to fix a display problem. Older reports retain their original schema/version; the software does not fabricate new conclusions for an old run.

## Reference evidence, not universal reactor ground truth

The **Evidence library** UI reads a versioned catalog of primary-source records, the selected NASA 2026 LEIA requirements profile, and three Yu 2025 published scalar observations from Tables 2, 4 and 5. Each record retains source URL, locator, units and applicability. Source documents remain linked rather than redistributed wholesale.

Requirements, encouraged pilot references, notional cleanliness values, published observations and lifetime projections remain separate categories. The source registry is reviewed/versioned, not an unverified live web feed. Updating reviewed packaged references installs a new library version at backend startup while retaining prior versions. Each new investigation pins one registry snapshot so its tools, source context and exported record refer to the same version.

Condition-matched comparisons expose reported versus published values and their differences. Matching declared configuration, LHS-1, temperature, current and electrolysis duration is only an initial screen; it does not establish identical geometry, methods, calibration or hardware. Resistance and wall comparisons also require applicable measurement/exposure records. A difference from a published observation is **not** a failure threshold. No matched context means no numerical publication comparison, rather than silently selecting a misleading reactor example.

The library does not contain fault-labelled telemetry or a calibrated probability that a new reactor is healthy. Existing source-grounded benchmark labels and independent arithmetic support bounded checks; they do not certify all new engineering interpretations or optimal next experiments.

## System audit: implemented and remaining scope

| Requested capability | Implementation / limit |
| --- | --- |
| Resistance trend | Supplied R(t) plot and all-point descriptive slope; scalar endpoints kept separate; matched-condition evidence required |
| Wall loss, thermal cycles, endurance | Structured measured values, clocks, methods, crack/outcome records; projections never become demonstrated lifetime |
| Broad MRE performance | 22 metric entries plus charge accounting: production, electrical, energy, material/thermal, endurance, measurement integrity |
| Official/research comparison | Named NASA profile, user requirements, versioned source library and scoped published comparisons |
| Useful numerics | Formulas, units, missing-input states, independent arithmetic, nominal requirement comparisons; no invented uncertainty |
| Gas-quality comparison | Wet/dry and mole/volume/mass-fraction bases; mismatched purity requirements withheld |
| Feedstock performance | Processed mass distinguished from loaded batch; extraction yield requires documented available oxygen in matching processed feedstock/system-output window |
| Explanation, next evidence, critic, final | Input-driven Meta loop with actual tool receipts; can retain a correct initial answer |
| Proof behind findings | Exact cited inputs, metric IDs/results/formulas, source locators/applicability and executed receipts; not automatic certification of every narrative sentence |
| Persistence/export | SQLite draft/reference state, browser backup, immutable report/trace replay, readable HTML and JSON |
| Live reactor/LIMS/DAQ connection | Planned adapter only; manual/Excel ingestion implemented; no equipment control or compatibility claim |
| Production qualification | Not demonstrated: prospective independent reactor validation, calibrated failure rates, expert/operational acceptance and broader security/deployment hardening |

Blank unknown values stay unknown. The software must not invent thermal cycles, calibration files, wall inspection results or a reaction mechanism to fill them. It evaluates available evidence and identifies the next missing measurement; it does not make all experimental uncertainty disappear.

## One-time upgrade checks — owner runs

The assistant inspected the saved files and read the existing local GET endpoints. It did not start the project, run tests/builds or make Meta calls for this change. Static Python/JSX parsing and blank-template structure/rendering are separate from functional verification.

From the activated repository-root environment:

```sh
PYTHONPATH="$PWD/src" python -m unittest discover -s tests -v
```

In the frontend directory:

```sh
npm test
npm run build
```

These checks use offline/test fixtures; they do not call Meta. Restart the old Python backend **once** to load this upgrade and create/migrate SQLite:

```sh
PYTHONPATH="$PWD/src" python -m mre_engineer serve --port 8769
```

After building, opening http://127.0.0.1:8769 uses the built React UI with this single backend process. Alternatively, keep the established second-terminal `npm run dev` workflow and open http://127.0.0.1:5173. Do not open a second backend on the same port.

Tests, pip installation, rebuilding and rerunning an assessment are **not** steps for every reopening. A local server still needs to be running to serve the application. If the backend terminal is closed, start the backend again; saved state remains. MODEL_API_KEY is a process environment variable, so an entirely new terminal needs the existing secure key-setting step for new paid work. The database does not store it. Saved reports and the library are readable without a key.

## Verify reopening without spending credits

1. Open the updated UI. The last completed saved review should be available; click **View saved result** or **Saved reviews**. Do not click Assess again merely to reopen it.
2. Edit a draft name/value. Wait for **Draft saved to this workspace**. Keep the credit checkbox unticked.
3. Refresh/close/reopen the page. Check the form and selected review restore. Stop/restart the backend and check again. Recorded API-attempt counts should remain unchanged.
4. Open **Evidence library**. Confirm local SQLite storage, source/version information and the distinct NASA/published-observation tables.
5. Open two tabs, edit both: a stale revision must show a conflict rather than silently replace the newer server draft. Browser backup is retained until the owner explicitly reloads the saved draft.
6. Reopen/export an old review. It should remain the same review with its original input, critic, final answer and trace. Older implementation labelling is expected after a code upgrade.
7. Only for a genuinely new/changed experiment, enter actual values, verify units/measurement bases and explicitly authorize a new assessment. Unknown measured values should remain missing. Use the new Excel template for the added fields.

New offline checks cover SQLite restart retention, two-tab conflicts, corrupted registry refusal, finite/bounded drafts, read-only library behaviour, protected draft saves, purity-basis mismatch, processed versus loaded mass and available-oxygen yield. Browser lifecycle and the new paid workflow remain owner-run verification, not claims of completed execution.

Endurance evidence must identify whether it belongs to the same demonstration. A duration from another run cannot automatically satisfy this demonstration’s requirement; a same-run endurance duration cannot exceed its full system window.

While the page is visible, periodic/focus-triggered read-only workspace refresh reconnects to a restarted backend and obtains its new local token. This never starts paid work. Draft saves pause on connection errors; newer revisions in another tab still require explicit conflict handling.
