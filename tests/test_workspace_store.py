"""Owner-run persistence/reference tests. No application server or paid requests."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from mre_engineer.evidence import EvidenceError
from mre_engineer.workspace_store import initialize,database_path,load_draft,save_draft,registry,publication_comparisons
from mre_engineer.experiment_input import validate_input
from mre_engineer.performance import assess
from mre_engineer.experiment_math import accounting


def draft():return {'form':{'experiment_name':'Constructed draft','current_A':'0.5','duration_h':'1','trace':[],'test_estimates':{}},'origin':None,'tab':'manual','view':'input','selected_assessment_id':None}
def sample(**changes):return validate_input({'experiment_name':'Constructed software control','current_A':0.5,'duration_s':3600,'collected_o2_g':0.07,'time_alignment':'reported_same_interval',**changes})


class WorkspaceStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def test_read_does_not_initialize_a_database(self):
        with self.assertRaises(EvidenceError):load_draft(self.root)
        self.assertFalse(database_path(self.root).exists())
    def test_draft_survives_reinitialization_without_replaying_work(self):
        initialize(self.root);save_draft(self.root,draft(),0);initialize(self.root)
        restored=load_draft(self.root);self.assertEqual(restored['revision'],1);self.assertEqual(restored['draft'],draft())
        self.assertFalse((self.root/'outputs/assessments').exists())
    def test_two_tabs_cannot_silently_overwrite_a_draft(self):
        initialize(self.root);save_draft(self.root,draft(),0)
        changed=draft();changed['form']['current_A']='2'
        with self.assertRaises(EvidenceError):save_draft(self.root,changed,0)
        self.assertEqual(load_draft(self.root)['draft'],draft())
    def test_unknown_fields_consent_and_keys_are_not_persisted(self):
        initialize(self.root)
        for field in ('consent','MODEL_API_KEY','run_automatically'):
            value=draft();value[field]=True
            with self.assertRaises(EvidenceError):save_draft(self.root,value,0)
    def test_nonfinite_or_oversized_draft_is_rejected(self):
        initialize(self.root)
        for field,value in (('current_A',float('nan')),('question','x'*1010000)):
            data=draft();data['form'][field]=value
            with self.assertRaises(EvidenceError):save_draft(self.root,data,0)
    def test_registry_is_versioned_and_published_values_are_not_verdicts(self):
        initialize(self.root);value=registry(self.root)
        self.assertEqual(value['storage'],'local-sqlite');self.assertEqual(len(value['version']),64)
        self.assertEqual(value['published_observations']['cases'][2]['thermal_exposure_h'],14)
        self.assertNotIn('final_review',value)
    def test_tampered_registry_stops_use(self):
        initialize(self.root)
        with sqlite3.connect(database_path(self.root)) as conn:conn.execute("UPDATE evidence_versions SET payload='{}'")
        with self.assertRaises(EvidenceError):registry(self.root)
    def test_mismatched_hardware_does_not_get_publication_grade(self):
        initialize(self.root);result=publication_comparisons(sample(),registry(self.root))
        self.assertEqual(result['comparisons'],[]);self.assertEqual(result['status'],'no_condition_matched_publication')
    def test_matched_declared_context_produces_descriptive_difference(self):
        initialize(self.root)
        value=sample(configuration='hollow_ysz_pt',feedstock='LHS-1',temperature_C=1600,collected_o2_g=0.08)
        result=publication_comparisons(value,registry(self.root))
        row=next(r for r in result['comparisons'] if r['field']=='collected_o2_g')
        self.assertAlmostEqual(row['difference'],0.01);self.assertNotIn('passed',row)
        self.assertIn('not_experimental_equivalence',result['status'])


class AdditionalMeasurementBasisTests(unittest.TestCase):
    def report(self,**changes):
        data=sample(**changes);return assess(data,accounting(data))
    def test_purity_target_cannot_mix_mass_and_mole_fraction(self):
        data={'oxygen_purity_percent':99,'purity_basis':'dry','purity_quantity_basis':'mass_fraction','purity_reference':'Constructed assay','target_min_oxygen_purity_percent':98,'target_purity_quantity_basis':'mole_fraction','target_reference':'Constructed mole-basis requirement'}
        self.assertEqual(self.report(**data)['target_checks'][0]['status'],'insufficient_evidence')
        data['target_purity_quantity_basis']='mass_fraction'
        self.assertEqual(self.report(**data)['target_checks'][0]['status'],'within_declared_target')
    def test_loaded_batch_is_not_processed_mass(self):
        data={'processed_regolith_g':10,'feedstock_mass_basis':'batch_loaded','feedstock_mass_reference':'Constructed record','measurement_window_scope':'full_system_operation','oxygen_measurement_location':'system_output'}
        self.assertIsNone(self.report(**data)['metrics']['oxygen_per_processed_regolith_kg_kg']['value'])
        data['feedstock_mass_basis']='processed_in_window'
        self.assertAlmostEqual(self.report(**data)['metrics']['oxygen_per_processed_regolith_kg_kg']['value'],0.007)
    def test_available_oxygen_needs_matched_inventory_and_is_not_clipped(self):
        data={'available_oxygen_g':0.05,'measurement_window_scope':'full_system_operation','oxygen_measurement_location':'system_output'}
        self.assertIsNone(self.report(**data)['metrics']['oxygen_extraction_yield_percent']['value'])
        data.update(available_oxygen_basis='matched_processed_feedstock',available_oxygen_reference='Constructed available oxygen inventory')
        report=self.report(**data);self.assertAlmostEqual(report['metrics']['oxygen_extraction_yield_percent']['value'],140)
        self.assertIn('reported_system_oxygen_exceeds_declared_available_oxygen',report['input_consistency_flags'])
    def test_temperature_requirement_needs_a_temperature_record(self):
        self.assertEqual(self.report(temperature_max_C=1600,target_max_temperature_C=1700,target_reference='Constructed limit')['target_checks'][0]['status'],'insufficient_evidence')

    def test_other_run_endurance_cannot_pass_this_demonstrations_requirement(self):
        data=sample(endurance_test_h=48,endurance_outcome='no_failure_reported',endurance_run_alignment='other_run',endurance_reference='Other experiment',target_endurance_h=24,target_reference='Constructed requirement')
        self.assertEqual(assess(data,accounting(data))['target_checks'][0]['status'],'insufficient_evidence')
