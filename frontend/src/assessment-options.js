// Optional design limits must never be silently inherited as NASA criteria.
export function applyAssessmentOptions(input,{customTargets=false}={}) {
  const result={...input};
  if(!customTargets){
    for(const key of Object.keys(result)) if(key.startsWith('target_')) result[key]=null;
    result.retirement_wall_loss_um=null;result.projection_model='not_requested';result.reported_projected_lifetime_h=null;result.projection_reference=null;
    result.target_energy_scope='unknown';result.target_purity_quantity_basis='unknown';
  }
  // Diagnostic planning costs are outside the streamlined assessment form.
  result.available_hours=null;result.budget_usd=null;result.test_estimates={};
  return result;
}
