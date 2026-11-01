import test from 'node:test';
import assert from 'node:assert/strict';
import {hasSelectedSamMask, NO_SAM_MASK_MESSAGE} from '../src/sam-mask-state.js';

test('zero-mask SAM result cannot enable comparison and has actionable feedback', () => {
  assert.equal(hasSelectedSamMask({id:'empty', masks:[]}, 'empty'), false);
  assert.match(NO_SAM_MASK_MESSAGE, /no matching object/i);
  assert.match(NO_SAM_MASK_MESSAGE, /closer crop/i);
  assert.match(NO_SAM_MASK_MESSAGE, /No mask or measurement was generated/);
});

test('pending, stale and absent selected masks cannot enable comparison', () => {
  assert.equal(hasSelectedSamMask(undefined, 'new'), false);
  assert.equal(hasSelectedSamMask({id:'old', masks:[{index:0,area_px:50}]}, 'new'), false);
  assert.equal(hasSelectedSamMask({id:'new', masks:[{index:1,area_px:50}]}, 'new', 0), false);
  assert.equal(hasSelectedSamMask({id:'new', masks:[{index:0,area_px:0}]}, 'new'), false);
});

test('valid matching SAM selection remains available', () => {
  assert.equal(hasSelectedSamMask({id:'ready', masks:[{index:0,area_px:50354}]}, 'ready'), true);
  assert.equal(hasSelectedSamMask({id:'ready', masks:[{index:2,area_px:45373}]}, 'ready', 2), true);
});
