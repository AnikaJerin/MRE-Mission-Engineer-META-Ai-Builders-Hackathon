"""Owner-run source reconstructions and constructed controls; no network or real API.
Source rows: Yu et al. 2025 Tables 2,4,5. These are not new reactor trials.
"""
import copy
import unittest
from unittest.mock import patch
from mre_engineer.evidence import EvidenceError
from mre_engineer.experiment_input import validate_input
from mre_engineer.experiment_math import accounting
from mre_engineer.performance import assess
from mre_engineer.performance_contract import contract
from mre_engineer.experiment_agent import verify_assessments,decision_evidence,tool,source_context


def control(**kwargs):
    return {'experiment_name':'Constructed software control','current_A':0.5,'duration_s':3600,'collected_o2_g':0.07,'time_alignment':'reported_same_interval',**kwargs}


def result(value):
    data=validate_input(value)
    return assess(data,accounting(data))


def metric(report,key):return report['metrics'][key]['value']


class PerformanceArithmeticTests(unittest.TestCase):
    def test_published_12h_values_use_14h_thermal_clock(self):
        value=control(duration_s=43200,collected_o2_g=0.749,configuration='hollow_ysz_pt',initial_resistance_ohm=1.46,final_resistance_ohm=0.78,thermal_exposure_h=14,wall_loss_um=85,wall_loss_uncertainty_um=19,wall_rate_basis='thermal_exposure',wall_measurement_reference='Yu2025 Table4',resistance_reference='Yu2025 Table5')
        r=result(value)
        self.assertAlmostEqual(metric(r,'resistance_change_percent'),-46.57534246575342)
        self.assertAlmostEqual(metric(r,'wall_loss_rate_um_h'),85/14)
        self.assertAlmostEqual(metric(r,'oxygen_rate_g_h'),0.749/12)
        self.assertNotAlmostEqual(metric(r,'wall_loss_rate_um_h'),85/12)
        self.assertEqual(r['resistance_basis'],'two_endpoints_only')
        self.assertIsNone(metric(r,'resistance_slope_ohm_h'))
        self.assertTrue(all(m['independent_check']['passed'] for m in r['metrics'].values()))
    def test_changed_input_changes_result(self):
        a=result(control(wall_loss_um=8,thermal_exposure_h=2,wall_rate_basis='thermal_exposure'))
        b=result(control(wall_loss_um=16,thermal_exposure_h=2,wall_rate_basis='thermal_exposure'))
        self.assertEqual(metric(b,'wall_loss_rate_um_h'),2*metric(a,'wall_loss_rate_um_h'))
    def test_unknown_wall_clock_does_not_guess_rate(self):
        self.assertIsNone(metric(result(control(wall_loss_um=85)),'wall_loss_rate_um_h'))
    def test_full_resistance_history_uses_all_points(self):
        # Constructed irregular sampling: endpoint slope 0, full-history OLS != 0.
        r=result(control(resistance_trace=[{'time_s':0,'resistance_ohm':1},{'time_s':900,'resistance_ohm':3},{'time_s':3600,'resistance_ohm':1}]))
        self.assertEqual(metric(r,'resistance_change_percent'),0)
        self.assertNotEqual(metric(r,'resistance_slope_ohm_h'),0)
        self.assertTrue(r['metrics']['resistance_slope_ohm_h']['independent_check']['passed'])
    def test_projection_is_not_observed_endurance(self):
        r=result(control(wall_loss_um=10,thermal_exposure_h=2,wall_rate_basis='thermal_exposure',retirement_wall_loss_um=50,projection_model='constant_wall_loss',wall_measurement_reference='Constructed thickness record',reported_projected_lifetime_h=214))
        self.assertEqual(metric(r,'conditional_remaining_wall_life_h'),8)
        self.assertEqual(metric(r,'reported_projected_lifetime_h'),214)
        self.assertIsNone(metric(r,'endurance_test_h'))
    def test_projection_requires_explicit_model_record_and_nonzero_rate(self):
        values=[control(wall_loss_um=10,thermal_exposure_h=2,wall_rate_basis='thermal_exposure',retirement_wall_loss_um=50),
                control(wall_loss_um=10,thermal_exposure_h=2,wall_rate_basis='thermal_exposure',retirement_wall_loss_um=50,projection_model='constant_wall_loss'),
                control(wall_loss_um=0,thermal_exposure_h=2,wall_rate_basis='thermal_exposure',retirement_wall_loss_um=50,projection_model='constant_wall_loss',wall_measurement_reference='Control')]
        for value in values:self.assertIsNone(metric(result(value),'conditional_remaining_wall_life_h'))
    def test_zero_oxygen_does_not_create_infinite_specific_energy(self):
        r=result(control(collected_o2_g=0,total_energy_kWh=1,voltage_V=2,energy_scope='total_system',energy_time_alignment='reported_same_interval'))
        self.assertIsNone(metric(r,'reported_specific_energy_kWh_kg'));self.assertIsNone(metric(r,'cell_specific_energy_kWh_kg'))
    def test_full_system_window_and_cell_window_stay_separate(self):
        r=result(control(system_operating_h=2,measurement_window_scope='full_system_operation',oxygen_measurement_location='system_output',time_alignment='different_interval',total_energy_kWh=1,energy_scope='total_system',energy_time_alignment='reported_same_interval',consumables_g=0))
        self.assertIsNone(metric(r,'oxygen_rate_g_h'))
        self.assertEqual(metric(r,'system_oxygen_rate_kg_h'),0.07/1000/2)
        self.assertEqual(metric(r,'oxygen_per_energy_kg_kWh'),0.07/1000)
        self.assertEqual(metric(r,'consumables_kg_per_kg_o2'),0)
    def test_cell_energy_is_not_total_system_energy(self):
        r=result(control(voltage_V=2,total_energy_kWh=0.001,energy_scope='total_system',energy_time_alignment='reported_same_interval'))
        self.assertAlmostEqual(metric(r,'cell_specific_energy_kWh_kg'),1/0.07)
        self.assertAlmostEqual(metric(r,'reported_specific_energy_kWh_kg'),1/0.07)
        r=result(control(voltage_V=2,total_energy_kWh=0.0001,energy_scope='total_system',energy_time_alignment='reported_same_interval'))
        self.assertIn('reported_total_energy_below_computed_cell_energy',r['input_consistency_flags'])
    def test_independent_disagreement_stops_assessment(self):
        data=validate_input(control());wrong={k:None for k in result(control())['metrics']}
        with patch('mre_engineer.performance.reference',return_value=wrong):
            with self.assertRaises(EvidenceError):assess(data,accounting(data))


class TargetAndProfileTests(unittest.TestCase):
    def test_resistance_target_requires_comparable_records(self):
        value=control(initial_resistance_ohm=2,final_resistance_ohm=1,target_max_abs_resistance_change_percent=10,target_reference='Constructed requirement')
        self.assertEqual(result(value)['target_checks'][0]['status'],'insufficient_evidence')
        value.update(resistance_comparability='same_conditions',resistance_reference='Constructed matched record')
        self.assertEqual(result(value)['target_checks'][0]['status'],'outside_declared_target')
    def test_wall_bound_straddling_target_withholds_nominal_grade(self):
        r=result(control(wall_loss_um=10,wall_loss_uncertainty_um=2,target_max_wall_loss_um=11,target_reference='Control requirement',wall_measurement_reference='Control'))
        self.assertEqual(r['target_checks'][0]['status'],'insufficient_evidence')
    def test_energy_requirement_cannot_mix_boundaries(self):
        r=result(control(total_energy_kWh=1,energy_scope='cell_only',energy_time_alignment='reported_same_interval',energy_reference='Control',target_max_specific_energy_kWh_kg=100000,target_energy_scope='total_system',target_reference='Control requirement'))
        self.assertEqual(r['target_checks'][0]['status'],'insufficient_evidence')
    def test_no_selected_profile_means_no_official_grade(self):
        self.assertEqual(result(control())['official_profile_checks'],[])
    def test_missing_integration_is_missing_evidence_not_duration_failure(self):
        r=result(control(comparison_profile='nasa_leia_2026_topic2',endurance_test_h=12))
        duration=next(c for c in r['official_profile_checks'] if c['id']=='1.7.1')
        self.assertEqual(duration['status'],'evidence_needed')
        self.assertEqual(duration['value'],48)
    def test_duration_and_encouraged_throughput_have_different_meanings(self):
        value=control(comparison_profile='nasa_leia_2026_topic2',endurance_test_h=48,endurance_run_alignment='same_demonstration',system_operating_h=48,measurement_window_scope='full_system_operation',oxygen_measurement_location='system_output',integrated_flow_status='demonstrated',continuous_operation_status='reported_continuous',integration_reference='Constructed integration record',endurance_reference='Constructed observed-run record',repair_reference='Constructed repair record',repairs_count=1,consumables_g=0,consumables_reference='Constructed inventory',calibration_status='reported_available',calibration_reference='Constructed gas calibration',records_reference='Constructed full-window record')
        checks={c['id']:c for c in result(value)['official_profile_checks']}
        self.assertEqual(checks['1.7.1']['status'],'duration_criterion_numerically_met')
        self.assertEqual(checks['1.2.1']['status'],'below_encouraged_reference_not_a_required_failure')
        self.assertEqual(checks['1.5.2-NC']['status'],'context_only_notional_target')
        self.assertEqual(checks['1.1.1']['status'],'scaling_evidence_requires_review')
    def test_bad_structured_inputs_are_rejected(self):
        for changes in ({'thermal_cycles':1.5},{'oxygen_purity_percent':101},{'initial_resistance_ohm':0},{'thermal_exposure_h':0.5},{'failure_time_h':4,'endurance_test_h':3,'endurance_outcome':'failure_observed'}):
            with self.assertRaises(EvidenceError):validate_input(control(**changes))
    def test_parameter_catalog_is_not_case_result(self):
        catalog=contract();self.assertIn('fields',catalog)
        self.assertNotIn('final_review',catalog);self.assertNotIn('result',catalog)


class DecisionEvidenceTests(unittest.TestCase):
    def plan(self):
        return {'assessments':[{'dimension':k,'status':'insufficient_evidence','finding':'Constructed offline response','improvement_or_next_evidence':'Review records','metric_ids':['oxygen_rate_g_h'] if k=='production' else [],'input_fields':['collected_o2_g'],'evidence_refs':['tool-placeholder']} for k in ('production','electrical','energy','materials','endurance','measurement_integrity')]}
    def test_unknown_inputs_and_unsupported_target_verdict_fail(self):
        data=validate_input(control());p=assess(data,accounting(data));plan=self.plan()
        for a in plan['assessments']:a['evidence_refs']=['experiment-tool-test']
        plan['assessments'][0]['input_fields']=['fabricated_measurement']
        with self.assertRaises(EvidenceError):verify_assessments(plan,data,p,['experiment-tool-test'])
        plan=self.plan()
        for a in plan['assessments']:a['evidence_refs']=['experiment-tool-test']
        plan['assessments'][0]['status']='conditional_target_met'
        with self.assertRaises(EvidenceError):verify_assessments(plan,data,p,['experiment-tool-test'])
    def test_proof_uses_actual_inputs_and_executed_receipts(self):
        data=validate_input(control());receipt=tool(data,'performance_assessment');plan=self.plan()
        for a in plan['assessments']:a['evidence_refs']=[receipt['evidence_id']]
        verify_assessments(plan,data,receipt['result'],[receipt['evidence_id']],[receipt])
        proof=decision_evidence(plan,data,receipt['result'],[receipt],source_context(data))
        self.assertEqual(proof[0]['inputs']['collected_o2_g'],0.07)
        self.assertEqual(proof[0]['references'][0]['tool'],'performance_assessment')
        self.assertTrue(proof[0]['metrics']['oxygen_rate_g_h']['independent_check']['passed'])
