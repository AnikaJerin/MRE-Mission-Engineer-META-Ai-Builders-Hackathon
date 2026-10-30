import SamComparison from './SamComparison.jsx';
import React,{useEffect,useState} from 'react';
import {get,action} from './api.js';
import HypothesisTesting from './HypothesisTesting.jsx';
import SamInspection from './SamInspection.jsx';
import ReactorDiagnostics from './ReactorDiagnostics.jsx';

export default function HypothesisLayer({report,token,job,busy,canBuild,onRefresh}){
 const [pack,setPack]=useState(null),[versions,setVersions]=useState([]),[previous,setPrevious]=useState(''),[consent,setConsent]=useState(false),[pending,setPending]=useState(false),[notice,setNotice]=useState('');
 useEffect(()=>{
  let active=true;
  get('/api/reactor-hypotheses?assessment_id='+encodeURIComponent(report.id)).then(value=>{
   if(!active)return;setPack(value.latest);setVersions(value.versions);setPrevious('');setNotice('');
  }).catch(e=>active&&setNotice(e.message));return()=>{active=false;};
 },[report.id,job?.result?.scene_id]);
 async function build(){
  setPending(true);setNotice('');try{
   await action(token,{action:'reactor_hypotheses',assessment_id:report.id,previous_scene_id:previous||null,consent:true});
   setConsent(false);await onRefresh();setNotice('Hypothesis request submitted.');
  }catch(e){setNotice(e.message);}finally{setPending(false);}
 }
 async function openVersion(id){
  if(!id)return;try{setPack(await get('/api/reactor-hypothesis?id='+encodeURIComponent(id)));setPrevious(id);setNotice('Saved hypothesis version opened. No Meta request made.');}catch(e){setNotice(e.message);}
 }
 const matching=pack?.assessment_id===report.id;
 return <>
  <section className='panel hypothesis-builder'><h2>Reactor investigation</h2>
   <p className='small'>Wonder generates explanations and highlights parts. The reactor geometry is a reference model.</p>
   <p className='small'>Assessment: {report.input.experiment_name} · {new Date(report.completed_at).toLocaleString()}</p>
   {report.status==='completed'?<>
    <details><summary>Compare or open previous hypotheses</summary><div className='fields'><label>Reconsider an earlier hypothesis set — optional<select value={previous} disabled={busy||pending} onChange={e=>setPrevious(e.target.value)}><option value=''>New hypothesis set</option>{versions.map(v=><option key={v.id} value={v.id}>{v.experiment_name} · {new Date(v.created_at).toLocaleString()}</option>)}</select><small>A prior set is context, not ground truth. Meta must explain which hypotheses it retains, revises or rejects using this assessment’s evidence.</small></label>
    <label>Open an existing version for this result<select value={matching?pack?.id||'':''} onChange={e=>openVersion(e.target.value)}><option value=''>Select a saved version</option>{versions.filter(v=>v.assessment_id===report.id).map(v=><option key={v.id} value={v.id}>{new Date(v.created_at).toLocaleString()}</option>)}</select></label></div></details>
    <label className='consent'><input type='checkbox' checked={consent} disabled={busy||pending||!canBuild} onChange={e=>setConsent(e.target.checked)}/>Use Meta for one hypothesis request · $0.25 local reservation; not a provider billing cap.</label>
    <button type='button' className='button primary' disabled={!consent||busy||pending||!canBuild} onClick={build}>{previous?'Compare hypotheses':'Generate hypotheses'} ↗</button>
   </>:<p>A completed assessment is needed first. Partial reviews remain available in the other tabs.</p>}
   {job?.action==='reactor_hypotheses'&&job.state==='running'&&<p role='status'>Generating hypothesis version · {job.progress?.kind?.replaceAll('_',' ')||'Preparing'} · no automatic retry.</p>}
   {job?.action==='reactor_hypotheses'&&job.state!=='running'&&(job.error||job.result?.error)&&<p className='message'>{job.error||job.result.error}</p>}
   <p role='status'>{notice}</p>
   {!pack&&<p className='input-origin'>No component hypotheses generated for this assessment yet. The reactor is a neutral reference schematic until you create them.</p>}
   {matching&&<><p className='input-origin'>Saved hypothesis version · {new Date(pack.created_at).toLocaleString()} · {pack.api_attempts} recorded Meta request · linked to this assessment. Opening this tab makes no new request.</p><details><summary>Hypothesis summary</summary><p>{pack.result.summary}</p></details>
    {pack.result.changes.length>0&&<details><summary>Version changes</summary><ul>{pack.result.changes.map(c=><li key={c.previous_number}><strong>Previous hypothesis {c.previous_number}: {c.outcome}</strong> — {c.reason}</li>)}</ul></details>}
    <a href={'/api/reactor-hypothesis?id='+encodeURIComponent(pack.id)} download={'hypothesis-'+pack.id+'.json'}>Download hypothesis evidence</a>
   </>}
  </section>
  <HypothesisTesting key={report.id} report={report} scene={matching?pack:null} {...{token,job,busy,canBuild,onRefresh}}/>
  <SamComparison key={'sam-pair-'+report.id} {...{report,token,job,busy,canBuild,onRefresh}}/>
  <details className='panel'><summary>Asset preparation & diagnostic tests</summary><SamInspection {...{token,job,busy,canBuild,onRefresh}}/><ReactorDiagnostics/></details>
 </>;
}
