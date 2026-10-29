import test from 'node:test';
import assert from 'node:assert/strict';
import {parseCurrentTrace,formatCurrentTrace} from '../src/manual-trace.js';
test('manual measured rows round-trip without inventing voltage',()=>{const rows=parseCurrentTrace('0,1,,control\n3600,1,,control');assert.equal(rows[0].voltage_V,null);assert.deepEqual(parseCurrentTrace(formatCurrentTrace(rows)),rows);});
test('blank history selects constant-current mode',()=>assert.deepEqual(parseCurrentTrace(''),[]));
test('units, nonfinite numbers and reversed rows are rejected',()=>{for(const value of ['0,1 A,2\n3600,1,2','0,Infinity,2\n3600,1,2','3600,1,2\n0,1,2'])assert.throws(()=>parseCurrentTrace(value));});
