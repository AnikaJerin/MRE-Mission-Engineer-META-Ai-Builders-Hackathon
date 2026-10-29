import test from 'node:test';
import assert from 'node:assert/strict';
import {assessmentLabel} from '../src/review-labels.js';
test('observation label does not imply a performance pass',()=>assert.match(assessmentLabel('supported_observation'),/not a performance pass/));
test('target outcomes remain distinct',()=>assert.notEqual(assessmentLabel('supported_observation'),assessmentLabel('conditional_target_met')));
