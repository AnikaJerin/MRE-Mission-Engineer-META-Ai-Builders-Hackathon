import React,{useEffect,useState} from 'react';
import {get} from './api.js';
export default function ReactorDiagnostics(){
 const [report,setReport]=useState(null),[notice,setNotice]=useState('');
 async function refresh(){try{const v=await get('/api/reactor-diagnostics');setReport(v.report);setNotice(v.report?'Saved results loaded. No API request made.':'No diagnostic run saved yet. Run the owner evaluation commands in README.md.');}catch(e){setNotice(e.message);}}
 useEffect(()=>{refresh();},[]);
 return <details className='panel'><summary>Known-cause synthetic diagnostic evaluation</summary><button type='button' className='text-button' onClick={refresh}>Refresh saved evaluation</button><p>{notice}</p>{report&&<><p>{report.scope}</p><div className='table-scroll'><table><thead><tr><th>Method</th><th>Correct / available</th><th>Coverage</th></tr></thead><tbody>{Object.entries(report.methods).map(([k,v])=><tr key={k}><td>{k.replaceAll('_',' ')}</td><td>{v.correct}/{v.available}</td><td>{v.available}/{v.selected}</td></tr>)}</tbody></table></div>{report.cases.map(c=><article key={c.case_id}><h4>{c.case_id.replaceAll('-',' ')}</h4><p>Construction reference: {c.reference.cause.replaceAll('_',' ')} · {c.reference.next_test.replaceAll('_',' ')}</p><ul>{Object.entries(c.methods).filter(([k])=>k!=='checklist').map(([k,v])=><li key={k}><strong>{k.replaceAll('_',' ')}:</strong> {v.cause.replaceAll('_',' ')} — {v.basis}</li>)}</ul>{c.error&&<p>{c.error}</p>}</article>)}</>}</details>;
}
