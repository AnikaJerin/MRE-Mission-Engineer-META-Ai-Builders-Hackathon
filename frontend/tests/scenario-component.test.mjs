import test from 'node:test';
import assert from 'node:assert/strict';
import {scenarioComponent} from '../src/scenario-component.js';
test('allocation follows electrical hypothesis, collection follows gas',()=>{
 const scene={result:{hypotheses:[{components:['gas']},{components:['gas','anode']} ]}};
 assert.equal(scenarioComponent({model:'current_allocation',hypothesis_number:2},scene),'anode');
 assert.equal(scenarioComponent({model:'collection_accounting',hypothesis_number:1},scene),'gas');
 assert.equal(scenarioComponent({model:'current_allocation'},null),'melt');
 assert.equal(scenarioComponent({material_forecast:{component:'wall'}},scene),'wall');
});
