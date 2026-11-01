import test from 'node:test';
import assert from 'node:assert/strict';
import {toForm,hasSavedDesignRequirements} from '../src/assessment-form.js';
import {parseCurrentTrace} from '../src/manual-trace.js';
import {selectReviews} from '../src/saved-review-list.js';

test('saved input restoration retains measurements, zeros, choices and provenance without mutation',()=>{
 const input={experiment_name:'Saved run',duration_s:7200,current_A:.6,collected_o2_g:0,voltage_V:3.2,configuration:'hollow_ysz_pt',calibration_status:'unknown',time_alignment:'reported_same_interval',wall_loss_um:30,thermal_exposure_h:4,energy_scope:'total_system',records_reference:'notebook 7',resistance_trace:[{time_s:0,resistance_ohm:1.5,source:'instrument'},{time_s:7200,resistance_ohm:1.8,source:'instrument'}],composition:{analysis_id:'A',source:'Assay',rows:[{oxide:'SiO2',wt_percent:51.2}]}};
 const before=structuredClone(input),form=toForm(input);
 assert.equal(form.duration_h,2);assert.equal(form.current_A,.6);assert.equal(form.collected_o2_g,0);
 assert.equal(form.wall_loss_um,30);assert.equal(form.energy_scope,'total_system');assert.equal(form.records_reference,'notebook 7');
 assert.equal(form.composition_text,'SiO2,51.2');assert.equal(form.analysis_id,'A');assert.equal(form.composition_source,'Assay');
 assert.equal(form.resistance_text,'0,1.5,instrument\n7200,1.8,instrument');
 assert.deepEqual(input,before);assert.equal(form.consent,undefined);
});
test('saved measured trace returns to editable text without inventing scalar current or voltage',()=>{
 const trace=[{time_s:0,current_A:.4,voltage_V:null,source:'log'},{time_s:3600,current_A:.6,voltage_V:null,source:'log'}];
 const form=toForm({duration_s:3600,current_A:null,voltage_V:null,trace});
 assert.deepEqual(parseCurrentTrace(form.current_trace_text),trace);assert.equal(form.current_A,'');assert.equal(form.voltage_V,'');
});
test('only an explicitly stored design requirement reopens advanced requirement fields',()=>{
 assert.equal(hasSavedDesignRequirements({target_reference:null,target_energy_scope:'unknown',projection_model:'not_requested'}),false);
 assert.equal(hasSavedDesignRequirements({target_max_wall_loss_um:0}),true);
 assert.equal(hasSavedDesignRequirements({projection_model:'constant_wall_loss'}),true);
});
test('saved review search and sorting preserve duplicate names and original collection',()=>{
 const rows=[{id:'a',name:'Same experiment',status:'failed',created_at:'2026-10-30T10:00:00Z'},{id:'b',name:'Same experiment',status:'completed',created_at:'2026-11-01T10:00:00Z'},{id:'c',name:'Other',status:'completed',created_at:'2026-10-31T10:00:00Z'}];
 assert.deepEqual(selectReviews(rows,{query:'  SAME  '}).map(r=>r.id),['b','a']);
 assert.deepEqual(selectReviews(rows,{status:'completed',newestFirst:false}).map(r=>r.id),['c','b']);
 assert.equal(selectReviews(rows,{query:'missing'}).length,0);
 assert.deepEqual(rows.map(r=>r.id),['a','b','c']);
});
