import React,{useEffect,useRef,useState} from 'react';
import {get,action} from './api.js';

function Overlay({result,onInspect}){
 const [metrics,setMetrics]=useState(null);const maskExport=useRef(null);
 function download(){if(!maskExport.current)return;const blob=new Blob([JSON.stringify(maskExport.current)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='sam-mask-'+result.id+'.json';a.click();URL.revokeObjectURL(url);}
 const canvas=useRef(null),[status,setStatus]=useState('Reading saved SAM response…');
 useEffect(()=>{
  let active=true,renderer;
  (async()=>{
   try{
    const {parseImageStream,recordsOfKind,decodeMaskToRaster,decodeMaskToRLE}=await import('@meta-sam/parser');
    const {SegmentationRenderer}=await import('@meta-sam/graphics');renderer=new SegmentationRenderer();
    async function* events(){for(const event of result.events)yield event;}
    const parsed=await parseImageStream(events()).finalResult;
    if(parsed.outcome.status!=='completed')throw new Error('SAM output is incomplete; no complete mask is claimed.');
    if(parsed.diagnostics.some(d=>d.severity==='error'))throw new Error('SAM output contains parser errors; inspect the saved response.');
    const image=new Image();image.src=result.image_data_url;await image.decode();if(!active)return;
    const c=canvas.current;c.width=result.width;c.height=result.height;const ctx=c.getContext('2d');ctx.drawImage(image,0,0);
    await renderer.update(parsed);if(!active)return;
    renderer.render(ctx,{media:'image',source:{x:0,y:0,width:result.width,height:result.height},target:{x:0,y:0,width:c.width,height:c.height}});
    const masks=recordsOfKind(parsed.records,'mask');if(masks.length){const all=masks.map(m=>{const pixels=decodeMaskToRaster(m.mask),rle=decodeMaskToRLE(m.mask);return {pixels:Array.from(pixels),width:rle.size[1],height:rle.size[0],area:pixels.reduce((a,b)=>a+b,0)};}).sort((a,b)=>b.area-a.area);const m=all[0];setMetrics({count:masks.length,area:m.area,coverage:100*m.area/(result.width*result.height),aligned:m.width===result.width&&m.height===result.height});maskExport.current={...m,sam_id:result.id,component:result.component_id,source:result.source,interpretation:'Actual SAM pixels; not corrosion depth or physical surface area.'};}setStatus(masks.length?`${masks.length} SAM mask(s) returned. Check alignment visually; a mask is not a diagnosis or a new 3D mesh.`:'SAM returned no matching object. No mask or geometry has been fabricated.');
   }catch(e){if(active)setStatus(e.message);}
  })();return()=>{active=false;renderer?.dispose();};
 },[result]);
 return <><canvas ref={canvas} className='sam-overlay' aria-label='Actual saved SAM segmentation overlay'/><p>{status}</p>{metrics&&<><ul><li>Detected masks: {metrics.count}</li><li>Largest mask: {metrics.area} pixels</li><li>Image coverage: {metrics.coverage.toFixed(2)}% (not physical loss)</li></ul><button type='button' className='button secondary' onClick={()=>{window.dispatchEvent(new CustomEvent('mre-component-evidence',{detail:{component:result.component_id,summary:`SAM segmented ${metrics.area} pixels (${metrics.coverage.toFixed(2)}% of image). Shape evidence only, not confirmed damage.`,source:result.source?.source_url||'Owner reference'} }));document.querySelector('.reactor-lab')?.scrollIntoView({behavior:'smooth'});}}>Inspect segmented component in 3D</button><button type='button' className='text-button' onClick={download}>Download actual SAM mask</button><a href={result.image_data_url} download={'sam-reference-'+result.id+'.png'}>Download reference image</a></>}<p className='small'>Component mapping: {result.component_id}. Use the mask as a Blender modelling reference, not a measured 3D surface.</p></>;
}

export default function SamInspection({token,job,busy,canBuild,onRefresh}){
 const [image,setImage]=useState(null),[component,setComponent]=useState('vessel'),[concept,setConcept]=useState('ceramic tube'),[url,setUrl]=useState(''),[locator,setLocator]=useState(''),[rights,setRights]=useState(''),[consent,setConsent]=useState(false),[saved,setSaved]=useState(null),[notice,setNotice]=useState(''),[pending,setPending]=useState(false);
 useEffect(()=>{let active=true;get('/api/sam-segmentation').then(v=>active&&setSaved(v.latest)).catch(e=>active&&setNotice(e.message));return()=>{active=false;};},[job?.result?.sam_id]);
 async function choose(e){
  setConsent(false);const file=e.target.files?.[0];if(!file)return;
  try{if(file.type!=='image/png'||file.size>750000)throw new Error('Choose a PNG up to 750 KB, 16–1200 pixels per side.');
   const data=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsDataURL(file);});
   const img=new Image();img.src=data;await img.decode();if(img.width<16||img.height<16||img.width>1200||img.height>1200)throw new Error('Crop the reference to 16–1200 pixels per side.');setImage(data);setNotice('Reference selected. Check its source and permission before sharing.');
  }catch(e){setNotice(e.message);setImage(null);}
 }
 async function segment(){setPending(true);try{
  await action(token,{action:'sam_segment',consent:true,capture:{image_base64:image.split(',')[1],component_id:component,concept,source_url:url,source_locator:locator,rights_note:rights}});setConsent(false);await onRefresh();setNotice('SAM request queued. Your engineering reviews remain unchanged.');
 }catch(e){setNotice(e.message);}finally{setPending(false);}}
 return <details className='panel sam-inspection'><summary>Reference assets · Meta SAM 3.1 cloud</summary>
  <p>Use a published photograph or diagram of the selected Yu hollow-anode design. SAM identifies visible parts; Blender constructs the source-based mesh. This does not generate geometry from a hypothesis.</p>
  <a href='https://ntrs.nasa.gov/citations/20250004626' target='_blank' rel='noreferrer'>Reference: Yu 2025 · Figure 1(b), supplementary Figure S1 ↗</a>
  <div className='fields'><label>Reference PNG<input type='file' accept='image/png' onChange={choose}/></label><label>Component<select value={component} onChange={e=>setComponent(e.target.value)}>{['vessel','wall','anode','cathode','melt','gas'].map(v=><option key={v}>{v}</option>)}</select></label>
  <label>Visible object · one short noun phrase<input value={concept} onChange={e=>setConcept(e.target.value)} maxLength={100}/></label><label>Original publication URL<input type='url' value={url} onChange={e=>setUrl(e.target.value)} placeholder='https://…'/></label><label>Figure / page<input value={locator} onChange={e=>setLocator(e.target.value)} maxLength={300}/></label><label>Image permission / licence note<input value={rights} onChange={e=>setRights(e.target.value)} maxLength={500}/></label></div>
  {image&&<img src={image} className='sam-preview' alt='Source reference selected for SAM'/>}
  <label className='consent'><input type='checkbox' checked={consent} disabled={busy||pending||!canBuild} onChange={e=>setConsent(e.target.checked)}/>Send this reference to Meta SAM · one request · $0.25 local reservation, not a provider cap.</label>
  <button type='button' className='button primary' disabled={!consent||!image||!url||!locator||!rights||busy||pending||!canBuild} onClick={segment}>Segment reference with SAM ↗</button>
  <p role='status'>{notice}</p>{job?.action==='sam_segment'&&<p>{job.state==='running'?'SAM cloud request running…':job.error||job.result?.error||'SAM request finished.'}</p>}
  {saved&&<><p>Saved {saved.model} · {new Date(saved.created_at).toLocaleString()} · {saved.api_attempts} recorded request. No new request on reopening.</p>{saved.status==='completed'?<Overlay result={saved}/>:<p>{saved.error}</p>}</>}
  <p className='small'>Cloud SAM provides source-image segmentation and component-linked visual evidence. Existing Three.js geometry is retained; no SAM 3D reconstruction or damage-depth inference is claimed.</p>
  <p className='small'>SAM is 2D segmentation. No SAM 3D Objects endpoint is assumed. No local GPU needed. Geometry remains a documented approximation, not manufacturing CAD.</p>
 </details>;
}
