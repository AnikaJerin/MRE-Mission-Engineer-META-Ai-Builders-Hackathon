import test from 'node:test';
import assert from 'node:assert/strict';
import {applyAssessmentOptions} from '../src/assessment-options.js';
test('saved synthetic limits cannot become default public-reference requirements',()=>{
 const input={current_A:.5,target_max_wall_loss_um:10,target_reference:'SYNTHETIC',target_energy_scope:'total_system',target_purity_quantity_basis:'mole_fraction',comparison_profile:'none',available_hours:3,budget_usd:200,test_estimates:{x:{hours:1}}};
 const result=applyAssessmentOptions(input);
 assert.equal(result.current_A,.5);assert.equal(result.target_max_wall_loss_um,null);assert.equal(result.target_reference,null);assert.equal(result.target_energy_scope,'unknown');assert.equal(result.target_purity_quantity_basis,'unknown');assert.equal(result.comparison_profile,'none');assert.deepEqual(result.test_estimates,{});assert.equal(input.target_max_wall_loss_um,10);
});
test('custom requirements remain explicit opt-in; public profile is preserved',()=>{
 const input={target_max_wall_loss_um:10,target_reference:'Design specification',comparison_profile:'nasa_leia_2026_topic2'};
 const result=applyAssessmentOptions(input,{customTargets:true});assert.equal(result.target_max_wall_loss_um,10);assert.equal(result.target_reference,'Design specification');assert.equal(result.comparison_profile,input.comparison_profile);
});

test('unselected lifetime models are excluded rather than inherited from saved fixtures',()=>{
 const input={retirement_wall_loss_um:100,reported_projected_lifetime_h:400,projection_model:'constant_wall_loss',projection_reference:'SYNTHETIC',wall_loss_um:12,thermal_exposure_h:48};
 const result=applyAssessmentOptions(input);assert.equal(result.wall_loss_um,12);assert.equal(result.thermal_exposure_h,48);assert.equal(result.retirement_wall_loss_um,null);assert.equal(result.reported_projected_lifetime_h,null);assert.equal(result.projection_model,'not_requested');assert.equal(result.projection_reference,null);
});
