# Validation without personal interviews or expert scoring

Public observations can supply reference answers for bounded tasks. They cannot
supply an oracle for every engineering recommendation. No interview is required
to run a source-grounded benchmark, and expert review is not a universal exit gate
for this MVP. Expert/prospective evidence would still be needed for broader claims.

See benchmarks/source_ground_truth/v1/catalog.json for inspected primary sources,
locators, measurement rows, exclusions and four draft reference checks. This is a
resource catalog, not a completed benchmark or runnable API command. No new dataset,
test or Meta investigation has been executed by creating these files.

What we can objectively test:

1. Source extraction: recover quantities, units, configuration, measurement method
   and source locator from a supplied document.
2. Tool-grounded checks: correctly calculate changes or accounting values, keeping
   rounding separate from measurement uncertainty.
3. Evidence reasoning: separate measured results from extrapolations, detect
   explicitly constructed contradictions, and refrain from diagnoses not identified
   by the supplied evidence.
4. Recovery after additional evidence: fix a documented wrong claim after receiving
   a source packet, measured against one-pass and equal-call resampling controls.

These reference answers must be fixed from source tables before paid requests.
Do not score arbitrary prose with keyword matching or let another LLM supply the
ground truth. Restrict automatic decisions to explicit fields and evidence IDs;
leave open-ended next-test usefulness unscored when no objective outcome is available.

The Yu source is already inspected and shares a source group with the six-case
pilot, so additional table tasks remain development cases, not an independent
holdout. The KSC reactor is different from Yu's hollow-anode cell, but the 2025
KSC poster and 2026 presentation describe related LR-1 work and must be grouped.
Public literature may also be in a model's training data. Document-grounded success
does not establish discovery or blind future prediction.

Do not conflate available evidence:

- A published measurement table supports a numerical/source reference answer.
- An author's explanation supports an attribution label, not universal causal truth.
- A figure is published graphical evidence, not raw telemetry. Any digitization
  must retain its own extraction uncertainty and cannot become original raw data.
- FactSage predictions or OxideProperties code can support model-to-model checks;
  they are not independently measured reactor ground truth.
- Astromat chemistry is feedstock evidence, not labelled reactor faults or outcomes.
- No verified public raw current/gas/calibration dataset with fault labels was
  established by this search. This is not a claim that none exists anywhere.

Current finding remains unchanged: the completed six-case pilot gave checklist
6/6 and all model approaches 5/6, with no measured correction benefit. Preserve that
result; do not revise its answer key or prompts retrospectively. The new benchmark
must measure a different, explicitly stated evidence-review capability. It may
also find no advantage; report that outcome instead of manufacturing a win.

Development sequence before Nov 4 (Dhaka time):

- Oct 28-29: repair deterministic release gates; finalize source packets and
  separate reference keys; add offline scoring and invalid-input checks.
- Oct 30-31: owner runs a new frozen comparison; inspect exact errors and compare
  source-grounding/contradiction recovery against baselines.
- Nov 1-2: integrate actual results and export into lunar UI; include abstentions
  and unsuccessful cases. Record timing only for comparable software workflows,
  not claimed researcher time saved.
- Nov 3: reproducibility checks and submission demo. No production deployment or
  NASA adoption claim.

This sequence does not guarantee a positive model advantage. Its purpose is to
establish which evidence-review capabilities are actually demonstrated without
depending on access to personal interviews or reactor hardware.
