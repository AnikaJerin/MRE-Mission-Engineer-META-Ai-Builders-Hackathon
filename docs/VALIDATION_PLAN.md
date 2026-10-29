# Validation boundaries

Day 1 tests validate data contracts and provenance references only.

Later layers:
1. Numerical correctness: hand-worked unit cases, including zero/invalid inputs and
   fractional versus percent efficiency. Physics checks are separate from model prose.
2. Historical reproduction: published values with source locations, rounding and unknown
   measurement uncertainty retained. Reproducing an arithmetic result is not predicting it.
3. Evidence-gap cases: explicitly constructed missing-field/contradiction variants;
   these are not real laboratory faults.
4. Decision evaluation: fixed checklist and one-pass Meta baseline versus the full
   challenge/revision loop, using identical available evidence and tool budgets.
5. Practical usefulness: qualified review and eventually prospective laboratory cases.

The initial case includes published outcomes and is DEVELOPMENT ONLY. Do not use it
as a blind holdout. Future evaluation must record which outcomes were withheld and
group variants by original experimental source; paper familiarity can leak through
model pretraining even if outputs are withheld from prompts.

Measured oxygen is not necessarily all oxygen generated. Source-specific causal
interpretations are evidence-backed references, not universal fault labels. A next-test
recommendation can be relevant without being proven optimal. No calibrated failure
probability, hardware qualification or NASA adoption is established by this benchmark.
