import test from 'node:test';
import assert from 'node:assert/strict';
import {readBackup,writeBackup,chooseDraft} from '../src/draft-storage.js';
const draft={form:{experiment_name:'Constructed draft'},origin:null,tab:'manual',view:'input',selected_assessment_id:null};
function memory(){const values=new Map();return {getItem:k=>values.get(k)||null,setItem:(k,v)=>values.set(k,v)};}
test('browser backup round-trip excludes API work',()=>{const storage=memory();assert.equal(writeBackup(storage,'control',draft,2,true),true);assert.deepEqual(readBackup(storage,'control').draft,draft);assert.equal(readBackup(storage,'control').draft.consent,undefined);});
test('dirty backup at matching revision is recoverable',()=>{assert.deepEqual(chooseDraft({revision:2,draft:null},{draft,dirty:true,serverRevision:2}).draft,draft);});
test('a newer server revision is not overwritten by another tab',()=>{const choice=chooseDraft({revision:3,draft},{draft:{form:{}},dirty:true,serverRevision:2});assert.equal(choice.conflict,true);assert.deepEqual(choice.draft,draft);});
test('clean backup does not cause a conflict on reopen',()=>{assert.equal(chooseDraft({revision:3,draft},{draft,dirty:false,serverRevision:2}).conflict,false);});
test('unavailable local storage does not throw',()=>{assert.equal(readBackup(null,'control'),null);assert.equal(writeBackup(null,'control',draft,0),false);});
