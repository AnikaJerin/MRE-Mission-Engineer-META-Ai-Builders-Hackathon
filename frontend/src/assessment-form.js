import {formatCurrentTrace} from './manual-trace.js';

export const numbers = ['current_A','collected_o2_g','temperature_C','voltage_V','sample_mass_g','oxygen_uncertainty_g','current_uncertainty_A','duration_uncertainty_s','available_hours','budget_usd'];
export const texts = ['experiment_name','question','feedstock','anode_material','cathode_material','calibration_reference','gas_measurement_method','records_reference','observations','source_label'];

// Convert the immutable input record to editable form values. No API work.
export function toForm(data = {}) {
  const result = {...data, duration_h: data.duration_s == null ? '' : data.duration_s / 3600, trace: [], resistance_trace: [], current_trace_text: formatCurrentTrace(data.trace || []), resistance_text: (data.resistance_trace || []).map(r => `${r.time_s},${r.resistance_ohm},${r.source || ''}`).join('\n'),
    configuration: data.configuration || 'unknown', calibration_status: data.calibration_status || 'unknown', time_alignment: data.time_alignment || 'unknown',
    analysis_id: data.composition?.analysis_id || '', composition_source: data.composition?.source || '', composition_text: data.composition?.rows.map(r => `${r.oxide},${r.wt_percent}`).join('\n') || '', test_estimates: data.test_estimates || {}};
  [...numbers,...texts].forEach(key => result[key] = data[key] ?? '');
  return result;
}

export function hasSavedDesignRequirements(input) {
  return Object.entries(input).some(([key,value])=>key.startsWith('target_') && !['target_reference','target_energy_scope','target_purity_quantity_basis'].includes(key) && value!=null)
    || input.retirement_wall_loss_um!=null || input.reported_projected_lifetime_h!=null || input.projection_model==='constant_wall_loss';
}
