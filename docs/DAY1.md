# Day 1: evidence and scope foundation

## What is implemented

1. Installable `src` package and local read-only CLI.
2. A resource manifest covering the owner's four resources, the hollow-anode study,
   its supplement, a NASA vacuum-test poster and optional property-model code.
3. Strict schemas and semantic checks for source IDs, duplicate IDs, units, evidence
   type, uncertainty status and the fraction convention for efficiency.
4. One development case: the published Yu et al. one-hour inverted hollow-anode experiment.
   A separate ten-oxide CSV transcribes the paper's LHS-1 composition, preserving its
   source and original percentage basis. Its chemistry checks belong to Day 2.
5. Validation tests and an acquisition guide. These have not been executed by the assistant.

## User-run acceptance checklist

- Install succeeds in a separate Python 3.11+ virtual environment.
- `python -m unittest discover -s tests -v` passes.
- `python -m mre_engineer doctor` lists the intended interpreter.
- `python -m mre_engineer sources` reports eight metadata entries.
- `python -m mre_engineer validate-case` reports valid structure/provenance and 7 evidence entries.
- Read `docs/DATA_SETUP.md`; acquire the main study and supplement if desired. Do not
  commit source PDFs without checking their redistribution terms.

`agent_run_ready: false` is expected. It means the agent/tools have not been built,
not that a raw log is secretly required to install the project. Missing calibration and
gas time series will constrain future inferences; do not fill them with invented data.

Day 1 is not scientifically validated merely because JSON validates. A human should
check the cited paper sections and Table 2 against the fixture. No numerical model,
property model, API access, cost or engineering recommendation is validated here.

## Day 2 handoff

Implement composition integrity and charge/oxygen accounting with explicit required
inputs, units and source-linked outputs. Use reported oxygen mass as an input for a
historical arithmetic check; do not claim to have predicted that measured mass.
Maintain reported Faradaic efficiency as a comparison target, with a rounding-aware
tolerance decided before running. A subsequent agent layer will choose these tools.

The existing ECLIPSE project remains unchanged. No paid API work belongs in Day 1.
