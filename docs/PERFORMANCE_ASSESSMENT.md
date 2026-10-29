# Reactor performance assessment: evidence and scope

This module separates input-derived numbers, declared requirements, published observations, and model-generated interpretation. It does not assign an overall good/bad grade or certify a reactor. No case result or discussion is prewritten. Equations, units, field definitions, evidence-ID checks and explicitly selected source requirements are deterministic. The Meta model generates the six dimension findings, rival explanations, critique, revision and next-evidence request for each submitted input.

## Reviewed primary sources (29 October 2026)

| Source | Applicable evidence | Use in this MVP |
| --- | --- | --- |
| [NASA NextSTEP-3 LEIA](https://www.nasa.gov/directorates/stmd/nextstep-3-a-lunar-enabling-technology/), [official solicitation](https://sam.gov/opp/812c81b0f0b84943be12a5f29615d3c8/view), Attachment B2 dated 8 September 2026 | Topic 2 selected system-demonstration requirements, pp. 1–3 | Optional named comparison profile; required, encouraged and notional values stay distinct |
| [Yu et al. 2025, Acta Astronautica / NASA NTRS](https://ntrs.nasa.gov/citations/20250004626) | Tables 2, 4, 5; sections 3.5 and 4 | Hollow YSZ/Pt anode electrical/material observations and lifetime-model limitations; not limits for another design |
| [NASA KSC 2025 LR-1 poster](https://ntrs.nasa.gov/citations/20250004983) | December 2024 vacuum experiment and retrieved-core characterization | Oxygen throughput can coexist with observed material degradation; no universal healthy value |
| [Burke et al. 2024, Frontiers in Space Technologies](https://www.frontiersin.org/journals/space-technologies/articles/10.3389/frspt.2024.1304579/full) | Modelled gravity, electrode orientation and surface effects | Environment applicability context; no CFD solver or lunar qualification is claimed |

The official B2 PDF was downloaded from the public SAM attachment endpoint and all three rendered pages were inspected. SHA-256: `e57ecd8236d4f5bc9a08bb3a1fb9a674905770bac4502214a897331c0bcc6cc9`. The packaged profile records its version, source locator and hash. Full solicitation/amendment compliance is outside this partial comparison. Link to publications rather than redistributing their copyrighted figures or complete text.

## What an 'ideal' parameter means here

The reviewed sources do not establish one universal ideal temperature, resistance, wall-loss rate, efficiency or lifetime for all lunar MRE designs. A published successful operating point is an observation under its own material, geometry, pressure, feedstock and measurement conditions. A system's required values need an applicable requirement document or a justified design target.

The optional **NASA 2026 LEIA Topic 2** profile uses:

| Clause | Value / evidence | Classification |
| --- | --- | --- |
| 1.7.1 | At least 48 h of integrated continuous system operation, with consumables/repairs accounted for | Required demonstration duration in this solicitation context; duration comparison alone is not full compliance |
| 1.2.1 | Approximately 0.2 kg O2/h pilot throughput, based on the source's annual-operation assumptions | Encouraged pilot reference; falling below it is not failure of a mandatory throughput threshold |
| 1.1.1 | Architecture/process scalable to 10 metric tonnes O2/year | Requires scaling evidence; annualizing a laboratory rate is not sufficient |
| 1.5.2 | Notional non-condensables below 1%, condensables below 0.5%, for downstream liquefaction | Context only; requires species/abundance/reference-condition and downstream-specification review; not an inferred overall purity threshold |
| 1.4.1, 1.5.1 | Output oxygen mass, system-average rate, kg O2/kWh, kg O2/kg regolith, composition, consumables, and extraction yield relative to available oxygen | Reporting measures; no universal numerical acceptance limits supplied for these measures |
| 1.3, 1.8–1.12 | Integrated process, waste/feed handling, product composition, representative simulant, thermal characterization | Structured evidence records and explicit gaps; not automated certification |

The 48 h criterion is withheld when full-system scope, continuity/integration and supporting records are missing. Repairs are reported, not automatically prohibited. Batch processing can occur inside a continuously operating integrated system. Flight qualification and TRL-6 testing are not inferred from this demonstration profile.

## Inputs and six assessment dimensions

All optional values remain unknown when blank. Researchers can enter values manually or use the new value-only XLSX template. Core inputs remain electrolysis time and either constant current or a measured current trace. Collected oxygen is optional.

1. **Production:** collected oxygen, aligned time window, measurement point, gas measurement/calibration record, purity and dry/wet basis; optional batch composition/mass. Collected mass divided by feedstock mass is not extraction yield relative to available oxygen.
2. **Electrical:** I(t), V(t), active electrode area, measured resistance endpoints or R(t), matched temperature/method and original record. A resistance decrease is not automatically improved efficiency; the YSZ publication discusses electronic conduction.
3. **Energy:** metered energy, cell versus full-system boundary, matched oxygen interval and meter record. Furnace, auxiliaries and startup are not silently included in cell IV integration.
4. **Materials/thermal:** initial thickness, measured wall recession and its stated bound/method, hot-melt exposure, operating-temperature range, cycle count/definition, crack observations and post-test characterization. Missing inspection does not mean absence of cracks.
5. **Endurance:** observed continuous test duration, outcome, failure time where applicable, test conditions and record; external projected lifetime is separate. Cycles and projections do not demonstrate long-term survival.
6. **Measurement integrity:** provenance, calibration, windows, uncertainty and method limits. A record location or a user-selected 'available' flag does not authenticate a measurement.

Additional environment/system fields cover pressure, gravity, feedstock representativeness, integration, feed/waste handling, repairs, consumables, contaminant records and ground-to-flight modifications. These inform the review and gaps; they do not fabricate a calibrated failure-risk prediction.

## Numerical methods

Twenty-two metric entries expose availability, units, formula, exact input-field names and independent arithmetic agreement. Computation uses only the submitted input. A separate Decimal implementation checks the arithmetic before paid work. Tests and the application have not been executed by the assistant for this change; the owner must run the supplied checks.

- Oxygen/charge accounting uses four electrons per O2 molecule, Faraday's law and the project's declared molar-mass approximation. This is ideal charge accounting, not predicted collected mass or validated efficiency.
- Resistance endpoint change: `100*(Rfinal-Rinitial)/Rinitial`. An actual history also supports a descriptive OLS slope across **all** its points. Endpoints alone do not establish the history. Conditions must match before interpreting a trend.
- Wall-loss rate: measured loss divided by the explicitly selected hot-melt exposure or electrolysis time. In Yu Table 4, the 12 h electrolysis specimen has **14 h hot exposure**. Thus `85/14 µm/h` and `85/12 µm/h` describe different clocks; the latter must not silently replace the former.
- A remaining-wall-life projection is optional and requires an explicit constant-rate model, a positive measured rate, a measurement record and a user-declared retirement loss. It is a conditional extrapolation, not demonstrated safe life or statistical reliability.
- Cell specific energy integrates supplied IV power. Metered specific energy retains its declared boundary. Full-system output rate and oxygen-per-energy use the full operations window/system output; unmatched intervals withhold inappropriate metrics.
- Target comparisons require a stated requirement reference, available metric, and matching measurement/boundary records. Wall-loss bounds crossing a limit withhold a verdict. Other target comparisons are explicitly **nominal**; comprehensive uncertainty propagation is not implemented.

No universal resistance/corrosion/lifetime threshold has been invented. Published projections are not used as mandatory acceptance values. Reduced-gravity applicability, chemical selectivity, full mass/oxygen closure, failure probability, autonomous control, optimal experiment design and hardware qualification remain outside this version.

## Decision evidence and agent workflow

Input validation → independent arithmetic → Meta hypothesis/tool choice → actual first tool → original review → additional performance check → critic → final review → report export. A completed cycle includes an actual structured performance tool receipt; it may retain a correct original conclusion. Five paid requests maximum, no automatic retry. Page refresh and source metadata fetch make no Meta calls.

Each final dimension includes its model finding/status, improvement or evidence request, cited input fields, metric IDs and evidence IDs. The **Decision evidence** section exposes those exact inputs, formula/results, independent agreement, source URL/locator/applicability and executed-tool receipt/input hash. Unknown IDs or fabricated fields are rejected; conditional target verdicts must have an applicable returned numerical check.

These checks establish traceability and bounded arithmetic correctness. They do not automatically prove that every sentence follows from its citation, authenticate a new experiment, or measure the utility of an open-ended next test. Published test reconstructions are reference checks, not ground truth for unseen hardware.

## Validation/versioning

Existing frozen T12 data, answer keys and implementation files are preserved. Its prior results evaluate the prior bounded task set; they do **not** validate this new performance module. New owner-run tests distinguish source reconstructions from constructed software controls. Model-facing schema, input adapter and UI changed; run the new local tests and then a labelled new assessment. Old saved assessments remain immutable and show their original implementation version rather than receiving a fabricated retrospective performance assessment.


For persistent drafts, the versioned local reference library, matched publication comparisons and the new purity/feedstock measurement-basis checks, see [Persistence and reference library](PERSISTENCE_AND_REFERENCE_LIBRARY.md). Reopening an existing assessment does not require another paid run.
