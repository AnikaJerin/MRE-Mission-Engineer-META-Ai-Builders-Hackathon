# Researcher-input scope amendment and integration plan

Reference: **MRE Mission Engineer — Verified Proposal**, especially the intended
user/decision scope and workflow, methods/tools, architecture, validation and task
breakdown sections (pages 3, 6–8, 10–11 of the supplied 15-page PDF). The project
remains a bounded MRE experiment-evidence reviewer and next-evidence planning agent.
It does not become a calibrated corrosion/failure predictor or autonomous controller.

## Alignment with the proposal

| Capability | Implementation and evidence boundary |
| --- | --- |
| Researcher question and case | New blank form or template-based Excel import; historical reconstruction is an explicit selectable example, not the only accepted input |
| Data/measurement provenance | Original values, units, source labels, Excel workbook hash/cells and changes retained. Locators are not downloaded/authenticated lab records |
| Configuration-specific reasoning | Feedstock, electrodes, configuration and temperature supplied; Yu YSZ/Pt context only admitted for that selected configuration. No cross-reactor lifetime transfer |
| Oxygen/current accounting | Q = I·t for declared constant current or trapezoidal integration of supplied I(t); m(O2) = Q·31.998/(4F). Ratio withheld for unaligned/unknown windows |
| Electrical energy | Trapezoidal integration of sampled P(t)=I(t)V(t), or constant I,V calculation. No furnace/auxiliary energy or thermal-efficiency inference |
| Composition/inventory | Single supported oxide wt% analysis; represented oxygen from actual entered batch mass. No recoverable-yield claim, implicit normalization or total-iron speciation |
| Numerical correctness | Separate Decimal/Fraction implementation checks accounting and supplied-bound sensitivity before paid work. It does not independently validate reactor measurements |
| Rival explanations/tools | Actual Meta function submissions propose hypotheses and select bounded checks. Two local tool executions, including charge accounting, are recorded |
| Challenge/revision | Same Meta model selects a second check, critiques the original review, then revises or retains it. This is not independent expert review |
| Candidate diagnostics | Four record/diagnostic-review categories; explicit missing prerequisites and user-entered time/cost comparisons. Information gain/optimal experiment utility are unvalidated |
| Usable UI | React + Vite researcher flow; original/critic/final, saved history, source/tool detail, independent arithmetic and review controls. Benchmarks are separate |
| Engineer decision/export | Separate accept/request-edits/reject draft record, readable HTML/full JSON. Browser print can produce a PDF; no native PDF generator |
| Persistence | Versioned JSON, file hashes and event chains retained rather than adding SQLite during the hackathon. Hashes detect local modification; they are not an external signature/authenticity certificate |
| Reactor/LIMS connection | Explicit future integration only; no hardware or official-software connector is implemented or demonstrated |

The user-input adapter, tests and React implementation are **authored, pending owner
execution and UI review**. No tests/build/server/API were run by the assistant for
this change. Prior frozen benchmark source files and answer keys are not changed.

## Completed benchmark evidence versus new-case correctness

Owner-reported T12 batches: `dev-t12-v3` and `eval-t12-v3`, same freeze `t12-v2`.
Development had 6/6 bounded outcomes for each method. Evaluation had checklist 6/6,
one-pass 5/6, challenge/revision 5/6 and equal-call resampling 6/6; all had full output
coverage, and available numerical fields matched 2/2. Revision made one correction
and one regression. These are small dependent source tasks, not general decision
accuracy or production validation. The answer key is unavailable to the agent.

Published source labels and independent arithmetic provide ground truth for **specified
claim fields and calculations**. They do not establish true failure mechanisms for
a new reactor, correctness of every prose sentence, useful/optimal next experiments
or measured researcher time saved. No new-user-input confidence percentage is shown.

## Future read-only equipment/software integration

The requested production direction is to ingest approved experiment records from
a potentiostat, DAQ export, lab information management system or reactor historian.
No specific vendor or NASA system compatibility has been established. An approved
export can first be mapped into the working Excel contract; a live adapter is later work.

1. Agree with the equipment owner on a **read-only** export/API contract: run ID,
   configuration/electrodes, specimen/assay ID, timestamps, sign conventions and units.
   Credentials remain server-side with narrowly scoped access.
2. Preserve the unmodified source file/response, its version and an import receipt.
   Map explicitly into seconds, A, V, g and declared analysis bases. Log conversions;
   reject ambiguous units, missing windows, duplicate/reversed timestamps and gaps
   that would require unsupported extrapolation.
3. Identify calibration version, blank/background corrections, gas reference
   conditions, sample transport delays, measurement uncertainty and current/gas
   synchronization. Gas fraction/flow must not be treated as oxygen mass without
   a separately validated conversion method.
4. Add adapter-specific test fixtures, known accounting references, dropout/drift
   controls and a replay test. Independent checks validate numerical conversion;
   authentic measurement validity requires instrument records and a reviewed process.
5. Preview imported records and gaps before the researcher clicks Assess. Retain the
   same model/tool limits and separate human review. No writeback, actuator commands
   or unattended reactor control is planned for this MVP.

## Deliberate remaining scope limits

- Raw gas concentration/flow integration and calibration-file processing are not
  implemented. A user supplies reported oxygen mass and method/context; the software
  does not claim to reconstruct collected mass from arbitrary gas files.
- Trace input integrates supplied samples; it does not validate sampling sufficiency,
  transport lag, sensor calibration or unsampled transients. Scalar absolute bounds
  are sensitivity only; covariance/trace uncertainty propagation remains future work.
- Paper ingestion is a small reviewed source catalogue, not autonomous mining of all
  NASA archives. Known citation IDs do not automatically prove narrative entailment.
- Optimal test usefulness, causal diagnosis, reactor operating changes and production
  qualification require additional independent evidence. They are not exit claims
  for a working hackathon evidence-review MVP.

## Owner acceptance sequence

Run backend unit tests → frontend proxy tests/build → start both servers → unchanged
published-example assessment → inspect tools/checks/original/critic/final → save a
review/export → import a filled workbook and verify field/cell provenance. A bad-unit
or formula workbook must reject without an API request. Refresh and reopening saved
records must not increase API attempts. See [exact walkthrough](RESEARCHER_WORKFLOW.md).
