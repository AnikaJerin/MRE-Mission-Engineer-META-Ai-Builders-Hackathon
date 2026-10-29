# Full workflow test — SYNTHETIC, not NASA experimental data

This is a deterministic software fixture. All run values, records, calibration identifiers, inspection outcomes and design targets are invented test inputs. They must not be presented as measured reactor performance or NASA-authorized acceptance values. The existing NASA comparison profile remains a separate real reference.

## Manual-input route

1. Open the updated UI and choose New experiment. This guide uses manual input only.
2. Fill the scalar/select fields below. For Electrolysis duration enter 48 hours; the stored duration_s value is 172800 seconds.
3. Open Measured current and voltage history, and paste the three Trace lines below. Paste the three Resistance lines in its optional history field. Enter the five oxide rows in the composition field.
4. Leave Constant current and Cell voltage blank: the manually pasted current/voltage history supplies them. Leave initial/final resistance scalar fields blank: the resistance history supplies them. These are mutually exclusive representations, not missing data.
5. Enter the four diagnostic resource estimates below. Diagnostic cost is separate from Meta billing.
6. Authorize one new assessment only after resolving/accepting the prior unknown-billing block and when the Meta service is available.
7. Follow the actual five-request workflow, then inspect metrics, findings, per-comment Why/references, critic, final review and exports.
8. Refresh/reopen Saved reviews without clicking Assess again. No additional model request should be made.

## Resource estimates entered after upload

These are synthetic estimates, not quotes or real experiment costs. Available time = 3 h, diagnostic budget = USD 200. This budget is separate from Meta billing.

| Review option | Hours | USD | Expected numerical fit |
| --- | ---: | ---: | --- |
| Gas accounting | 1 | 100 | Fits both |
| Electrical record | 0.5 | 50 | Fits both |
| Material evidence | 4 | 300 | Exceeds both |
| Comparable runs | 6 | 500 | Exceeds both |

## All scalar/select values (for manual inspection)

The numbers below are inputs, except the separate expected-output table. Every unspecified/null field below is intentionally blank. Dropdown codes map to the visible labels in the form. The separate process field is internal and fixed to MRE; you do not need to type it. The form displays duration in hours. History time stamps are seconds.

| Field | Input | Unit |
| --- | --- | --- |
| experiment_name (`experiment_name`) | SYNTHETIC FULL WORKFLOW TEST — NOT NASA DATA |  |
| question (`question`) | Software test only: assess all six dimensions against the supplied synthetic requirements and selected NASA context. Explain supported findings, concerns and missing evidence. Give a short reason and reference for every finding and critic comment. Do not treat this fixture as real measurements or claim NASA qualification. |  |
| process (`process`) | molten_regolith_electrolysis |  |
| configuration (`configuration`) | other_mre |  |
| feedstock (`feedstock`) | SYNTHETIC oxide mixture; not a real lunar sample |  |
| anode_material (`anode_material`) | SYNTHETIC material A; mechanism not characterized |  |
| cathode_material (`cathode_material`) | SYNTHETIC material B; mechanism not characterized |  |
| temperature_C (`temperature_C`) | 1600 | degC |
| current_A (`current_A`) | **Leave blank** | A |
| duration_s (`duration_s`) | 172800 | s |
| collected_o2_g (`collected_o2_g`) | 7 | g |
| voltage_V (`voltage_V`) | **Leave blank** | V |
| calibration_status (`calibration_status`) | reported_available |  |
| calibration_reference (`calibration_reference`) | SYNTHETIC-CAL-001 — software fixture only; not an actual calibration |  |
| gas_measurement_method (`gas_measurement_method`) | SYNTHETIC mass-collection record: 7 g over the same 48 h window; declared absolute bound 0.1 g. No physical calibration was performed. |  |
| time_alignment (`time_alignment`) | reported_same_interval |  |
| records_reference (`records_reference`) | SYNTHETIC-RUN-001 — manual software fixture, not a laboratory notebook |  |
| observations (`observations`) | SYNTHETIC software test: resistance rises from 1 to 1.1 ohm; wall loss 12 um; one defined temperature cycle; no detected cracks; no failure over a declared 48 h run. None are actual measurements. |  |
| source_label (`source_label`) | SYNTHETIC SOFTWARE FIXTURE. All run values, records and design targets are constructed. Not NASA data, real calibration, or reactor qualification. |  |
| sample_mass_g (`sample_mass_g`) | 100 | g |
| oxygen_uncertainty_g (`oxygen_uncertainty_g`) | 0.1 | g |
| current_uncertainty_A (`current_uncertainty_A`) | **Leave blank** | A |
| duration_uncertainty_s (`duration_uncertainty_s`) | **Leave blank** | s |
| available_hours (`available_hours`) | 3 | h |
| budget_usd (`budget_usd`) | 200 | USD |
| Regolith processed in full system window (`processed_regolith_g`) | 100 | g |
| Processed feedstock mass / time-window record (`feedstock_mass_reference`) | SYNTHETIC-MASS-001: 100 g processed in matching 48 h; complete hypothetical oxide analysis |  |
| Available oxygen in the matched processed feedstock (`available_oxygen_g`) | 45.40553797503922 | g |
| Available-oxygen assay / inventory method and scope (`available_oxygen_reference`) | SYNTHETIC-INVENTORY-001: complete nominal-oxide stoichiometric inventory; theoretical chemical oxygen, not demonstrated recoverable yield |  |
| Full system measurement-window duration (`system_operating_h`) | 48 | h |
| Other consumables used in matched system window (`consumables_g`) | 10 | g |
| Consumables inventory / matched-window record (`consumables_reference`) | SYNTHETIC-CONS-001: 10 g other consumables in same 48 h |  |
| Reported non-condensables (`noncondensables_percent`) | 1.5 | percent |
| Reported condensables (`condensables_percent`) | 0.5 | percent |
| Contaminant species, denominator and method record (`contaminant_reference`) | SYNTHETIC-GAS-001: dry molecular-abundance percentages; 98% O2, 1.5% non-condensables, 0.5% condensables. No actual gas analysis. |  |
| Repairs incurred in continuous demonstration (`repairs_count`) | 0 | count |
| Integrated operation / feed / waste test record (`integration_reference`) | SYNTHETIC-INTEGRATION-001: declared continuous integrated feed/process/output/waste operation for 48 h; no hardware was operated |  |
| Repair and downtime record (`repair_reference`) | SYNTHETIC-REPAIRS-001: zero repairs/downtime declared in this software fixture |  |
| Scaling model and architecture-change evidence (`scalability_reference`) | NOT ESTABLISHED: no 10-tonne/year scaling evidence; do not annualize this fixture into a scalability claim |  |
| Simulant / particle-size representativeness limits (`simulant_limitations`) | SYNTHETIC mixture; no verified lunar-highlands mineralogy or representative particle-size distribution |  |
| Required ground-to-flight modifications (`flight_modifications`) | NOT ESTABLISHED: ground fixture only; thermal, gravity, vacuum and flight interfaces need separate engineering review |  |
| Initial measured resistance (`initial_resistance_ohm`) | **Leave blank** | ohm |
| Final measured resistance (`final_resistance_ohm`) | **Leave blank** | ohm |
| Active anode area (`active_anode_area_cm2`) | 10 | cm2 |
| Resistance measurement record (`resistance_reference`) | SYNTHETIC-R-001: three resistance samples at matched 1600 C and same hypothetical measurement method |  |
| Total exposure to hot melt (`thermal_exposure_h`) | 48 | h |
| Completed thermal cycles (`thermal_cycles`) | 1 | count |
| Reported minimum operating temperature (`temperature_min_C`) | 1590 | degC |
| Reported maximum operating temperature (`temperature_max_C`) | 1610 | degC |
| Initial wall thickness (`initial_wall_thickness_um`) | 1000 | um |
| Measured wall loss (`wall_loss_um`) | 12 | um |
| Wall-loss printed ± bound (`wall_loss_uncertainty_um`) | 1 | um |
| Declared allowable cumulative wall loss (`retirement_wall_loss_um`) | 100 | um |
| Wall-loss method / record (`wall_measurement_reference`) | SYNTHETIC-WALL-001: recession 12 +/- 1 um after 48 h, same-location gauge example; bound is not statistical confidence |  |
| Thermal history / cycle definition record (`thermal_reference`) | SYNTHETIC-THERMAL-001: one cycle means 1590 to 1610 to 1600 C during 48 h; not a cold restart or survival qualification |  |
| Crack inspection method / record (`crack_reference`) | SYNTHETIC-INSPECTION-001: no crack detected in a hypothetical visual inspection; method detection limits unvalidated |  |
| Longest observed continuous endurance run (`endurance_test_h`) | 48 | h |
| Externally projected lifetime (`reported_projected_lifetime_h`) | 400 | h |
| Observed failure time within endurance run (`failure_time_h`) | **Leave blank** | h |
| Endurance record and test conditions (`endurance_reference`) | SYNTHETIC-ENDURANCE-001: same declared 48 h demonstration; no observed failure in fixture; not a real endurance experiment |  |
| External lifetime model / source (`projection_reference`) | SYNTHETIC-MODEL-001: constant 0.25 um/h loss and 100 um retirement loss imply 400 h total; hypothetical model, not observed life |  |
| Reported measured energy (`total_energy_kWh`) | 12 | kWh |
| Energy meter / boundary record (`energy_reference`) | SYNTHETIC-ENERGY-001: full cell + furnace + auxiliaries energy 12 kWh over matching 48 h; not an actual meter record |  |
| Measured oxygen purity (`oxygen_purity_percent`) | 98 | percent |
| Purity method / reference conditions (`purity_reference`) | SYNTHETIC-GAS-001: 98 mole-percent O2 on dry basis; not a physical assay |  |
| Chamber absolute pressure (`pressure_Pa`) | 100000 | Pa |
| Test gravity (`gravity_m_s2`) | 9.80665 | m_s2 |
| Environment / pressure record (`environment_reference`) | SYNTHETIC-ENV-001: terrestrial reference gravity and 100000 Pa; not lunar validation |  |
| Post-test characterization method (`post_test_method`) | SYNTHETIC visual inspection and same-location wall gauge |  |
| Observed post-test material findings (`post_test_findings`) | SYNTHETIC: wall recession 12 um; no cracks detected by stated hypothetical visual method. This is not experimental evidence. |  |
| Post-test evidence record (`post_test_reference`) | SYNTHETIC-INSPECTION-001; SYNTHETIC-WALL-001 |  |
| Minimum reported oxygen rate target (`target_oxygen_rate_g_h`) | 0.1 | g_h |
| Maximum specific energy target (`target_max_specific_energy_kWh_kg`) | 1500 | kWh_kg |
| Minimum oxygen purity target (`target_min_oxygen_purity_percent`) | 99 | percent |
| Maximum measured wall-loss target (`target_max_wall_loss_um`) | 10 | um |
| Maximum absolute resistance-change target (`target_max_abs_resistance_change_percent`) | 5 | percent |
| Required continuous test duration (`target_endurance_h`) | 48 | h |
| Maximum operating temperature target (`target_max_temperature_C`) | 1700 | degC |
| Requirement document / target rationale (`target_reference`) | SYNTHETIC-REQ-001: software-test requirements only; not NASA acceptance limits. Different requirement types have separate bases. |  |
| endurance_run_alignment (`endurance_run_alignment`) | Same documented system demonstration |  |
| feedstock_mass_basis (`feedstock_mass_basis`) | Measured processed mass in matching window |  |
| available_oxygen_basis (`available_oxygen_basis`) | Documented available oxygen in matching processed feedstock |  |
| purity_quantity_basis (`purity_quantity_basis`) | Mole fraction percent |  |
| target_purity_quantity_basis (`target_purity_quantity_basis`) | Mole fraction percent |  |
| comparison_profile (`comparison_profile`) | NASA 2026 LEIA Topic 2 — scoped evidence comparison |  |
| measurement_window_scope (`measurement_window_scope`) | Full system operations window |  |
| oxygen_measurement_location (`oxygen_measurement_location`) | System output |  |
| integrated_flow_status (`integrated_flow_status`) | Reported demonstrated |  |
| continuous_operation_status (`continuous_operation_status`) | Reported continuous integrated operation |  |
| feed_system_status (`feed_system_status`) | Reported demonstrated |  |
| waste_discharge_status (`waste_discharge_status`) | Reported demonstrated |  |
| thermal_characterization_status (`thermal_characterization_status`) | Reported documented |  |
| resistance_comparability (`resistance_comparability`) | Same temperature and measurement method |  |
| wall_rate_basis (`wall_rate_basis`) | Hot-melt exposure |  |
| projection_model (`projection_model`) | Conditional constant wall-loss extrapolation |  |
| crack_observation (`crack_observation`) | Not detected in supplied inspection |  |
| endurance_outcome (`endurance_outcome`) | No failure reported over observed run |  |
| energy_scope (`energy_scope`) | Cell + furnace + auxiliaries |  |
| energy_time_alignment (`energy_time_alignment`) | Same oxygen / energy interval |  |
| target_energy_scope (`target_energy_scope`) | Total-system energy target |  |
| purity_basis (`purity_basis`) | Dry gas basis |  |
| leak_check (`leak_check`) | Reported passed |  |

## Current and voltage history — manually paste

| time_s | current_A | voltage_V | Source |
| ---: | ---: | ---: | --- |
| 0 | 1 | 2 | SYNTHETIC-I-001 sample 1 |
| 86400 | 1 | 2 | SYNTHETIC-I-001 sample 2 |
| 172800 | 1 | 2 | SYNTHETIC-I-001 sample 3 |

Paste exactly, with no header:
```text
0,1,2,SYNTHETIC-I-001 sample 1
86400,1,2,SYNTHETIC-I-001 sample 2
172800,1,2,SYNTHETIC-I-001 sample 3
```

## Resistance history — manually paste

| time_s | resistance_ohm | Source |
| ---: | ---: | --- |
| 0 | 1 | SYNTHETIC-R-001 sample 1 |
| 86400 | 1.05 | SYNTHETIC-R-001 sample 2 |
| 172800 | 1.1 | SYNTHETIC-R-001 sample 3 |

Paste exactly, with no header:
```text
0,1,SYNTHETIC-R-001 sample 1
86400,1.05,SYNTHETIC-R-001 sample 2
172800,1.1,SYNTHETIC-R-001 sample 3
```

## Composition — complete synthetic analysis entered manually

| Oxide | wt_percent |
| --- | ---: |
| SiO2 | 50 |
| Al2O3 | 20 |
| CaO | 15 |
| MgO | 10 |
| FeO | 5 |

Composition analysis ID: SYNTHETIC-ASSAY-001. Composition source: SYNTHETIC complete nominal oxide mixture; not measured.
Paste into Oxides as reported:
```text
SiO2,50
Al2O3,20
CaO,15
MgO,10
FeO,5
```

## Expected numerical outputs — do not enter these as inputs

These arithmetic references were calculated outside the application, without importing/running project code. This does not establish that the application or model successfully produced them. Small float-rounding differences are expected.

| Metric | Expected |
| --- | ---: |
| charge_C | 172800 |
| ideal_o2_g | 14.3266709 |
| collected_to_ideal_percent | 48.85992042 |
| cell_energy_Wh | 96 |
| represented_oxygen_g | 45.40553798 |
| oxygen_rate_g_h | 0.1458333333 |
| full_system_oxygen_rate_kg_h | 0.0001458333333 |
| oxygen_per_energy_kg_kWh | 0.0005833333333 |
| specific_energy_kWh_kg | 1714.285714 |
| cell_specific_energy_kWh_kg | 13.71428571 |
| current_density_A_cm2 | 0.1 |
| resistance_change_percent | 10 |
| resistance_slope_ohm_h | 0.002083333333 |
| wall_loss_rate_um_h | 0.25 |
| wall_loss_fraction_percent | 1.2 |
| conditional_remaining_wall_life_h | 352 |
| temperature_span_C | 20 |
| observed_endurance_h | 48 |
| external_projected_lifetime_h | 400 |
| oxygen_purity_percent | 98 |
| oxygen_per_processed_regolith_kg_kg | 0.07 |
| oxygen_extraction_yield_percent | 15.41662165 |
| consumables_kg_per_kg_o2 | 1.428571429 |

## Expected deterministic requirement comparisons

| Synthetic requirement | Expected nominal comparison |
| --- | --- |
| Oxygen rate ≥ 0.1 g/h | Within declared target |
| Total-system specific energy ≤ 1500 kWh/kg | Outside declared target |
| Dry mole-basis purity ≥ 99% | Outside declared target (98%) |
| Wall loss ≤ 10 µm | Outside declared target (12 ± 1 µm) |
| Absolute resistance change ≤ 5% | Outside declared target (10%) |
| Same-run no-failure duration ≥ 48 h | Within declared target (48 h) |
| Peak temperature ≤ 1700 °C | Within declared target (1610 °C) |

The selected NASA profile should separately show a numerical 48 h duration match under the supplied synthetic declarations, throughput below the encouraged ~0.2 kg/h reference without calling it a mandatory throughput failure, notional cleanliness values requiring downstream-basis review, and unestablished scalability. It must not issue a NASA-compliant/flight-qualified verdict.

All values remain synthetic. Meta can correctly withhold physical/engineering conclusions despite complete test metadata. Exact prose, next-test selection and whether the critic requests a change are not fixed expected answers. Validate per-comment evidence links, not a predetermined story.

Only independent arithmetic and bounded contract comparisons are tested here. No current/time uncertainty propagation for traces is implemented; blank scalar current/time bounds are deliberate. The oxygen bound remains labelled and does not become a calibrated confidence interval. The external 400 h lifetime is not the observed 48 h endurance; the 352 h remaining-wall projection is conditional.

## Real-source alternative

For a published-data reconstruction, use Yu 2025: 0.5 A, 12 h, 0.749 g collected O2; YSZ/Pt hollow anode, LHS-1, Mo cathode, 1600 C; resistance 1.46→0.78 ohm; wall loss 85±19 µm after 14 h hot exposure. Source: https://ntrs.nasa.gov/citations/20250004626 Tables 2/4/5. Leave unavailable calibration, actual raw histories, cycle counts and other measurements unknown. Do not mix these measurements with this synthetic fixture’s invented calibration or design targets.

## The prior HTTP 503

The saved test-3 trace records Meta HTTP 503 on request 4, with provider message persistence service error. It is not an input-validation error. Reservation 20731ca98d7d4c0daacfffa54fb8421f was unresolved when inspected. Do not change it to zero/settled without provider evidence. An explicit owner acknowledgement can permit continuation while retaining its reservation, but does not establish actual charge or resolve provider availability. No automatic paid retry is performed.
