import React,{useEffect,useState} from 'react';
import {get} from './api.js';
const methodNames={checklist:'Rule-based check',one_pass:'First review',challenge_revision:'After critic review',resample_control:'Separate repeat review'};
const causeNames={collection_path:'Oxygen collection issue',material_change:'Material change',unresolved:'Cause still unclear'};
const label=value=>causeNames[value]||value?.replaceAll('_',' ');
function groupedReviews(methods){
 const groups=[];
 for(const [method,result] of Object.entries(methods).filter(([key])=>key!=='checklist')){
  const existing=groups.find(g=>g.result.cause===result.cause&&g.result.basis===result.basis);
  if(existing)existing.methods.push(methodNames[method]||method);else groups.push({methods:[methodNames[method]||method],result});
 }
 return groups;
}
export default function ReactorDiagnostics(){
 const [report,setReport]=useState(null),[notice,setNotice]=useState('');
 async function refresh(){try{const v=await get('/api/reactor-diagnostics');setReport(v.report);setNotice(v.report?'':'No saved test results yet.');}catch(e){setNotice(e.message);}}
 useEffect(()=>{refresh();},[]);
 return <section className='panel'><h3>Can the assistant spot the right issue?</h3>
 <p>We tested three made-up cases with known answers. These results test the software, not a real reactor.</p>
 {notice&&<p role='status'>{notice}</p>}
 {report&&<><div className='table-scroll'><table><thead><tr><th>Review method</th><th>Correct answers</th><th>Cases completed</th></tr></thead><tbody>{Object.entries(report.methods).map(([key,value])=><tr key={key}><td>{methodNames[key]||key}</td><td>{value.correct} of {value.available}</td><td>{value.available} of {value.selected}</td></tr>)}</tbody></table></div>
 
 {report.cases.map(c=><article key={c.case_id}><h4>{label(c.reference.cause)}</h4><p><strong>Expected answer:</strong> {label(c.reference.cause)}</p>{groupedReviews(c.methods).map((g,i)=><div key={i}><p><strong>{g.methods.join(' · ')}</strong></p><p><strong>Agent answer:</strong> {label(g.result.cause)}</p><p>{g.result.basis}</p></div>)}{c.error&&<p role='alert'>{c.error}</p>}</article>)}</>}
 </section>;
}
