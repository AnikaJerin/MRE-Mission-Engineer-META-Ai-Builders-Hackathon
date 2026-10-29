import test from 'node:test';
import assert from 'node:assert/strict';
import {isAllowedMutation} from '../proxy-policy.js';

const local = {method:'POST',headers:{origin:'http://127.0.0.1:5173',host:'127.0.0.1:5173'}};
test('local UI POST may enter protected backend proxy', () => assert.equal(isAllowedMutation(local),true));
test('foreign origin cannot be rewritten into a trusted backend origin', () => assert.equal(isAllowedMutation({...local,headers:{...local.headers,origin:'https://other.example'}}),false));
test('missing origin cannot enter mutation proxy', () => assert.equal(isAllowedMutation({...local,headers:{host:local.headers.host}}),false));
test('foreign host and unsupported method are rejected', () => {
  assert.equal(isAllowedMutation({...local,headers:{...local.headers,host:'other.example'}}),false);
  assert.equal(isAllowedMutation({...local,method:'PUT'}),false);
});
