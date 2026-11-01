import React,{useEffect,useMemo,useState} from 'react';
import {selectReviews} from './saved-review-list.js';
const pageSize=10;
function dateLabel(value){const date=new Date(value);return Number.isFinite(date.getTime())?date.toLocaleString():'Date unavailable';}
export default function SavedReviews({rows,onOpen,busy,loading}){
 const [query,setQuery]=useState(''),[status,setStatus]=useState('all'),[newestFirst,setNewestFirst]=useState(true),[page,setPage]=useState(1),[opening,setOpening]=useState(null);
 const statuses=useMemo(()=>Array.from(new Set(rows.map(row=>row.status))).sort(),[rows]);
 const filtered=useMemo(()=>selectReviews(rows,{query,status,newestFirst}),[rows,query,status,newestFirst]);
 const totalPages=Math.max(1,Math.ceil(filtered.length/pageSize)),currentPage=Math.min(page,totalPages),visible=filtered.slice((currentPage-1)*pageSize,currentPage*pageSize);
 useEffect(()=>setPage(1),[query,status,newestFirst]);
 async function open(id){setOpening(id);try{await onOpen(id);}finally{setOpening(null);}}
 return <section className='panel saved-reviews' aria-labelledby='saved-reviews-title'>
  <div className='section-head'><div><h2 id='saved-reviews-title'>Saved reviews</h2><p className='small'>Open a review to restore its inputs and inspect the saved results. No new Meta request.</p></div><span className='tag'>{rows.length} saved</span></div>
  <div className='review-list-controls'><label>Search experiments<input type='search' value={query} onChange={e=>setQuery(e.target.value)} placeholder='Search by experiment name'/></label><label>Status<select value={status} onChange={e=>setStatus(e.target.value)}><option value='all'>All statuses</option>{statuses.map(value=><option key={value} value={value}>{String(value).replaceAll('_',' ')}</option>)}</select></label></div>
  {loading?<p role='status'>Loading saved reviews…</p>:<><p className='small' role='status'>{filtered.length} matching {filtered.length===1?'review':'reviews'}</p>
  <div className='saved-reviews-table-wrap'><table className='saved-reviews-table'><caption className='sr-only'>Saved experiments and review status</caption><thead><tr><th scope='col'>Experiment</th><th scope='col'>Status</th><th scope='col' aria-sort={newestFirst?'descending':'ascending'}><button type='button' className='review-sort' onClick={()=>setNewestFirst(v=>!v)}>Saved date <span aria-hidden='true'>{newestFirst?'↓':'↑'}</span></button></th><th scope='col'>Action</th></tr></thead><tbody>
   {visible.map(row=><tr key={row.id}><td data-label='Experiment'><span className='saved-experiment-name'>{row.name||'Unnamed experiment'}</span></td><td data-label='Status'><span className={'review-status '+(row.status==='completed'?'completed':row.status==='failed'?'failed':'other')}>{String(row.status).replaceAll('_',' ')}</span></td><td data-label='Saved date'><time dateTime={row.created_at}>{dateLabel(row.created_at)}</time></td><td data-label='Action'><button type='button' className='button secondary review-open' disabled={busy||opening!==null} onClick={()=>open(row.id)} aria-label={'Open review: '+(row.name||'Unnamed experiment')}>{opening===row.id?'Opening…':'Open review'}</button></td></tr>)}
   {!visible.length&&<tr><td colSpan={4} className='saved-empty'>{rows.length?'No reviews match your search.':'No saved reviews yet. Assess an experiment to create one.'}</td></tr>}
  </tbody></table></div>
  <div className='review-pagination'><span className='small'>{filtered.length?`${(currentPage-1)*pageSize+1}–${Math.min(currentPage*pageSize,filtered.length)} of ${filtered.length}`:'0 reviews'}</span><div><button type='button' className='button secondary' disabled={currentPage===1} onClick={()=>setPage(currentPage-1)}>Previous</button><span className='small'>Page {currentPage} of {totalPages}</span><button type='button' className='button secondary' disabled={currentPage===totalPages} onClick={()=>setPage(currentPage+1)}>Next</button></div></div></>}
 </section>;
}
