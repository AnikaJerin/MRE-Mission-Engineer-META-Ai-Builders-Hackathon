"""Reviewed parameter definitions, not reactor grades or model-written conclusions."""

SOURCES=[
 {'id':'nasa-leia-b2-2026','title':'NASA NextSTEP-3 Appendix A — Topic 2 performance measures','year':2026,'url':'https://sam.gov/opp/812c81b0f0b84943be12a5f29615d3c8/view','download_url':'https://sam.gov/api/prod/opps/v3/opportunities/resources/files/949c35bd6fac414691588c8b3d666c77/download?api_key=null&token=','sha256':'e57ecd8236d4f5bc9a08bb3a1fb9a674905770bac4502214a897331c0bcc6cc9','checked_on':'2026-10-29','locator':'Attachment B2, pages 1–3, requirements 1.1.1–1.12.2; public attachment dated 2026-09-08','kind':'solicitation requirements','applicability':'Selected Topic 2 integrated-system demonstration; not a universal laboratory reactor standard or flight qualification','fact':'Required reporting includes oxygen mass/rate, energy productivity, regolith extraction, output composition and consumables. Integrated continuous operation minimum is 48 h. A roughly 0.2 kg/h pilot is encouraged; 10 t/year is a scalability requirement. Non-condensables below 1% and condensables below 0.5% are notional downstream-cleanliness targets, not general oxygen qualification.'},
 {'id':'yu-electrical','title':'Yu et al. 2025 — electrical behaviour','year':2025,'url':'https://ntrs.nasa.gov/citations/20250004626','locator':'Section 3.5.2; Table 5','kind':'published experiment','applicability':'YSZ/Pt hollow-anode cells; no universal resistance threshold','fact':'Resistance reduction is discussed alongside electronic conduction in YSZ; it is not by itself evidence of improved oxygen efficiency.'},
 {'id':'yu-materials','title':'Yu et al. 2025 — wall loss and thermal cycling','year':2025,'url':'https://ntrs.nasa.gov/citations/20250004626','locator':'Table 4; Sections 3.5.1 and 4.3','kind':'published experiment','applicability':'YSZ in molten LHS-1 under the reported test conditions','fact':'Wall recession is associated with time exposed to hot melt. Cooling-related cracks and composition changes require material-specific interpretation.'},
 {'id':'yu-endurance','title':'Yu et al. 2025 — lifetime assumptions','year':2025,'url':'https://ntrs.nasa.gov/citations/20250004626','locator':'Sections 4.2–4.4','kind':'published projection','applicability':'Declared geometry and constant-rate assumptions; not an endurance qualification','fact':'Lifetime is extrapolated using material loss and replacement assumptions; continued production and recession rates need validation.'},
 {'id':'ksc-performance','title':'NASA KSC 2025 — LR-1 demonstration','year':2025,'url':'https://ntrs.nasa.gov/citations/20250004983','locator':'Background and summary; December 2024 experiment','kind':'NASA experimental summary','applicability':'LR-1 vacuum demonstration; not a reference limit for another reactor','fact':'The report includes feedstock batch, temperature, power and oxygen throughput, with post-test material characterization and observed anode degradation. Oxygen production and degradation can coexist.'},
 {'id':'bubble-model-2024','title':'Burke et al. 2024 — reduced-gravity electrolysis model','year':2024,'url':'https://www.frontiersin.org/journals/space-technologies/articles/10.3389/frspt.2024.1304579/full','locator':'Sections 3.2 and 4.3–4.5','kind':'computational study','applicability':'Model of bubble behaviour; not measured lifetime or validated diagnosis for user hardware','fact':'Gravity, electrode orientation and surface properties affect modelled bubble detachment. A reduced-gravity simulation cannot qualify a terrestrial or lunar reactor.'},
]

# key, display label, explicit unit, parameter group. Blank values remain unknown.
FIELDS=[
 ('processed_regolith_g','Regolith processed in full system window','g','system'),('feedstock_mass_reference','Processed feedstock mass / time-window record','','system'),('available_oxygen_g','Available oxygen in the matched processed feedstock','g','system'),('available_oxygen_reference','Available-oxygen assay / inventory method and scope','','system'),
 ('system_operating_h','Full system measurement-window duration','h','system'),('consumables_g','Other consumables used in matched system window','g','system'),('consumables_reference','Consumables inventory / matched-window record','','system'),
 ('noncondensables_percent','Reported non-condensables','percent','system'),('condensables_percent','Reported condensables','percent','system'),('contaminant_reference','Contaminant species, denominator and method record','','system'),
 ('repairs_count','Repairs incurred in continuous demonstration','count','system'),('integration_reference','Integrated operation / feed / waste test record','','system'),('repair_reference','Repair and downtime record','','system'),
 ('scalability_reference','Scaling model and architecture-change evidence','','system'),('simulant_limitations','Simulant / particle-size representativeness limits','','system'),('flight_modifications','Required ground-to-flight modifications','','system'),
 ('initial_resistance_ohm','Initial measured resistance','ohm','electrical'),('final_resistance_ohm','Final measured resistance','ohm','electrical'),
 ('active_anode_area_cm2','Active anode area','cm2','electrical'),('resistance_reference','Resistance measurement record','','electrical'),
 ('thermal_exposure_h','Total exposure to hot melt','h','materials'),('thermal_cycles','Completed thermal cycles','count','materials'),
 ('temperature_min_C','Reported minimum operating temperature','degC','materials'),('temperature_max_C','Reported maximum operating temperature','degC','materials'),
 ('initial_wall_thickness_um','Initial wall thickness','um','materials'),('wall_loss_um','Measured wall loss','um','materials'),('wall_loss_uncertainty_um','Wall-loss printed ± bound','um','materials'),
 ('retirement_wall_loss_um','Declared allowable cumulative wall loss','um','materials'),('wall_measurement_reference','Wall-loss method / record','','materials'),('thermal_reference','Thermal history / cycle definition record','','materials'),('crack_reference','Crack inspection method / record','','materials'),
 ('endurance_test_h','Longest observed continuous endurance run','h','endurance'),('reported_projected_lifetime_h','Externally projected lifetime','h','endurance'),
 ('failure_time_h','Observed failure time within endurance run','h','endurance'),('endurance_reference','Endurance record and test conditions','','endurance'),('projection_reference','External lifetime model / source','','endurance'),
 ('total_energy_kWh','Reported measured energy','kWh','energy'),('energy_reference','Energy meter / boundary record','','energy'),
 ('oxygen_purity_percent','Measured oxygen purity','percent','production'),('purity_reference','Purity method / reference conditions','','production'),
 ('pressure_Pa','Chamber absolute pressure','Pa','environment'),('gravity_m_s2','Test gravity','m_s2','environment'),('environment_reference','Environment / pressure record','','environment'),
 ('post_test_method','Post-test characterization method','','environment'),('post_test_findings','Observed post-test material findings','','environment'),('post_test_reference','Post-test evidence record','','environment'),
 ('target_oxygen_rate_g_h','Minimum reported oxygen rate target','g_h','targets'),('target_max_specific_energy_kWh_kg','Maximum specific energy target','kWh_kg','targets'),
 ('target_min_oxygen_purity_percent','Minimum oxygen purity target','percent','targets'),('target_max_wall_loss_um','Maximum measured wall-loss target','um','targets'),
 ('target_max_abs_resistance_change_percent','Maximum absolute resistance-change target','percent','targets'),('target_endurance_h','Required continuous test duration','h','targets'),
 ('target_max_temperature_C','Maximum operating temperature target','degC','targets'),('target_reference','Requirement document / target rationale','','targets'),
]
EXTRA_NUMERIC=tuple(k for k,_,unit,_ in FIELDS if unit)
EXTRA_TEXT=tuple(k for k,_,unit,_ in FIELDS if not unit)
EXTRA_UNITS={k:unit for k,_,unit,_ in FIELDS if unit}
CHOICES={
 'endurance_run_alignment':[('unknown','Not established'),('same_demonstration','Same documented system demonstration'),('other_run','Different run / conditions')],
 'feedstock_mass_basis':[('unknown','Not established'),('processed_in_window','Measured processed mass in matching window'),('batch_loaded','Loaded batch mass only')],
 'available_oxygen_basis':[('unknown','Not established'),('matched_processed_feedstock','Documented available oxygen in matching processed feedstock')],
 'purity_quantity_basis':[('unknown','Not established'),('mole_fraction','Mole fraction percent'),('volume_fraction','Volume fraction percent'),('mass_fraction','Mass fraction percent')],
 'target_purity_quantity_basis':[('unknown','Not established'),('mole_fraction','Mole fraction percent'),('volume_fraction','Volume fraction percent'),('mass_fraction','Mass fraction percent')],
 'comparison_profile':[('none','User-defined requirements only'),('nasa_leia_2026_topic2','NASA 2026 LEIA Topic 2 — scoped evidence comparison')],
 'measurement_window_scope':[('unknown','Not specified'),('electrolysis_only','Electrolysis interval only'),('full_system_operation','Full system operations window')],
 'oxygen_measurement_location':[('unknown','Not specified'),('cell_outlet','Cell outlet only'),('system_output','System output')],
 'integrated_flow_status':[('unknown','Not established'),('demonstrated','Reported demonstrated'),('not_demonstrated','Not demonstrated')],
 'continuous_operation_status':[('unknown','Not established'),('reported_continuous','Reported continuous integrated operation'),('interrupted','System operation interrupted')],
 'feed_system_status':[('unknown','Not established'),('demonstrated','Reported demonstrated'),('not_demonstrated','Not demonstrated')],
 'waste_discharge_status':[('unknown','Not established'),('demonstrated','Reported demonstrated'),('not_demonstrated','Not demonstrated')],
 'thermal_characterization_status':[('unknown','Not established'),('demonstrated','Reported documented'),('not_demonstrated','Not demonstrated')],
 'resistance_comparability': [('unknown','Not confirmed'),('same_conditions','Same temperature and measurement method'),('different_conditions','Different conditions')],
 'wall_rate_basis': [('unknown','Not established'),('thermal_exposure','Hot-melt exposure'),('electrolysis','Electrolysis time — explicitly justified')],
 'projection_model': [('not_requested','Do not project'),('constant_wall_loss','Conditional constant wall-loss extrapolation')],
 'crack_observation': [('not_assessed','Not inspected / unknown'),('detected','Cracks reported'),('not_detected','Not detected in supplied inspection'),('inconclusive','Inconclusive inspection')],
 'endurance_outcome': [('not_supplied','Not supplied'),('no_failure_reported','No failure reported over observed run'),('failure_observed','Failure observed'),('inconclusive','Inconclusive')],
 'energy_scope': [('unknown','Boundary unknown'),('cell_only','Cell only'),('total_system','Cell + furnace + auxiliaries')],
 'energy_time_alignment': [('unknown','Not confirmed'),('reported_same_interval','Same oxygen / energy interval'),('different_interval','Different intervals')],
 'target_energy_scope': [('unknown','Not specified'),('cell_only','Cell-only energy target'),('total_system','Total-system energy target')],
 'purity_basis': [('unknown','Not specified'),('dry','Dry gas basis'),('wet','Wet gas basis')],
 'leak_check': [('not_supplied','Not supplied'),('passed','Reported passed'),('failed','Reported failed'),('inconclusive','Inconclusive')],
}
ENUM_GROUPS={'endurance_run_alignment':'endurance','feedstock_mass_basis':'system','available_oxygen_basis':'system','purity_quantity_basis':'production','target_purity_quantity_basis':'targets','resistance_comparability':'electrical','wall_rate_basis':'materials','projection_model':'materials','crack_observation':'materials','endurance_outcome':'endurance','energy_scope':'energy','energy_time_alignment':'energy','target_energy_scope':'targets','purity_basis':'production','leak_check':'production'}
ENUM_GROUPS.update({k:'system' for k in ('comparison_profile','measurement_window_scope','oxygen_measurement_location','integrated_flow_status','continuous_operation_status','feed_system_status','waste_discharge_status','thermal_characterization_status')})
ENUM_LABELS={'endurance_run_alignment':'Endurance evidence belongs to this demonstration?','feedstock_mass_basis':'Feedstock mass basis','available_oxygen_basis':'Available oxygen basis','purity_quantity_basis':'Gas purity quantity basis','target_purity_quantity_basis':'Purity requirement quantity basis','resistance_comparability':'Are resistance measurements comparable?','wall_rate_basis':'Wall-loss rate time basis','projection_model':'Optional wall-life model','crack_observation':'Crack inspection outcome','endurance_outcome':'Observed endurance outcome','energy_scope':'Energy measurement boundary','energy_time_alignment':'Oxygen / energy windows','target_energy_scope':'Energy requirement boundary','purity_basis':'Purity reference basis','leak_check':'Gas collection leak-check outcome'}
ENUM_LABELS.update({'comparison_profile':'Optional official requirements context','measurement_window_scope':'Measurement-window scope','oxygen_measurement_location':'Oxygen measurement point','integrated_flow_status':'Integrated process flow','continuous_operation_status':'Integrated continuity evidence','feed_system_status':'Regolith feed system','waste_discharge_status':'Uninterrupted waste discharge','thermal_characterization_status':'Thermal component/interface characterization'})
DIMENSIONS=('production','electrical','energy','materials','endurance','measurement_integrity')
TARGET_FIELDS=tuple(k for k in EXTRA_NUMERIC if k.startswith('target_'))

def contract():
    return {'version':'mre-performance-v5','scope':'MRE research evidence; no universal pass/fail or operational clearance',
      'fields':[{'key':k,'label':label,'unit':unit,'group':group,'numeric':bool(unit)} for k,label,unit,group in FIELDS],
      'choices':{k:{'label':ENUM_LABELS[k],'group':ENUM_GROUPS[k],'values':v} for k,v in CHOICES.items()},
      'dimensions':list(DIMENSIONS),'sources':SOURCES,'official_profile':load_profile(),
      'note':'Research parameters are not universal acceptance limits. Targets are researcher-declared, source-linked requirements. Source applicability and input provenance remain visible.'}


def load_profile():
    import json
    from importlib.resources import files
    return json.loads(files('mre_engineer').joinpath('resources','nasa_leia_2026_topic2.json').read_text())
