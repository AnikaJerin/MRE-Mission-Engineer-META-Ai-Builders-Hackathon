# LR-1 selection failure and next run

The saved lr1-v2 response contained an empty object, many text blocks and a final
choice citing engtool-rate_comparison-placeholder, which was not returned by a tool.
The host correctly rejected it before tool execution. The settled local estimate
for that attempt is $0.051260. Do not treat it as an engineering decision error or
a successful investigation. It remains visible as a transport/contract failure.

The engineering selection step now uses a real engineering_tool_choice function
definition, with the permitted-tool enum and existing references as arguments.
Its stage-specific instructions request only a selection, avoiding the previous
all-six-claim review instructions at the choice stage. The host requires an actual
function call and still validates the full schema and allowed references before
local execution. It does not accept placeholder citations, execute prose or retry.
Review/critic structured output and reference labels/tolerances are unchanged.
This correction has not been live-tested by the assistant.

Owner commands, from repository root:

```sh
PYTHONPATH="$PWD/src" python -m unittest discover -s tests -v
PYTHONPATH="$PWD/src" python -m mre_engineer engineering-freeze --name engineering-v3
PYTHONPATH="$PWD/src" python -m mre_engineer engineering-run --run-name lr1-v3 --freeze-name engineering-v3 --case-id lr1-core-review --allow-api-call
```

Only the last command spends credits: at most eight requests/$2 local envelope,
not a provider-enforced cap. If it fails, inspect its saved events rather than
repeating automatically. No budget acknowledgement is needed for the settled lr1-v2
request. Do not rerun the successful hollow-v2 just to change code provenance.

After lr1-v3 completes, collect separately versioned results locally:

```sh
PYTHONPATH="$PWD/src" python -m mre_engineer engineering-combine --run-name versioned-v3 --from-run hollow-v2 --from-run lr1-v3 --accept-versioned-components
PYTHONPATH="$PWD/src" python -m mre_engineer serve --source-run v2 --engineering-run versioned-v3
PYTHONPATH="$PWD/src" python -m mre_engineer dossier --run-name engineering-versioned-v3 --source-run v2 --engineering-run versioned-v3
```

Use another terminal for the export while serve runs. The collection refuses changed
source/reference/protocol data, incomplete or tampered components, duplicate case
contexts and mixed test-double/live modes. It retains each original freeze and code
hashes, and is labelled separately versioned evidence, not a single fixed-system
experiment. Older component code is shown as archived. Case-wise scores remain
useful; cross-case results do not establish a fixed-implementation success rate.
Previous failed attempts must remain in reliability reporting; do not report only
the completed runs as a first-attempt success rate.
