import {demoPhotos} from './demo-inputs.js';
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
    const masks=recordsOfKind(parsed.records,'mask');if(masks.length){const all=masks.map(m=>{const pixels=decodeMaskToRaster(m.mask),rle=decodeMaskToRLE(m.mask);return {pixels:Array.from(pixels),width:rle.size[1],height:rle.size[0],area:pixels.reduce((a,b)=>a+b,0)};}).sort((a,b)=>b.area-a.area);const m=all[0];setMetrics({count:masks.length,area:m.area,coverage:100*m.area/(result.width*result.height),aligned:m.width===result.width&&m.height===result.height});maskExport.current={...m,sam_id:result.id,component:result.component_id,source:result.source,interpretation:'Actual SAM pixels; not corrosion depth or physical surface area.'};}setStatus(masks.length?`SAM found ${masks.length} regions. Select the one that matches your component.`:'SAM returned no matching object. No mask or geometry has been fabricated.');
   }catch(e){if(active)setStatus(e.message);}
  })();return()=>{active=false;renderer?.dispose();};
 },[result]);
 return <><canvas ref={canvas} className='sam-overlay' aria-label='Actual saved SAM segmentation overlay'/><p>{status}</p>{metrics&&<><ul><li>Detected masks: {metrics.count}</li><li>Largest mask: {metrics.area} pixels</li><li>Image coverage: {metrics.coverage.toFixed(2)}% (not physical loss)</li></ul></>}</>;
}

export default function SamInspection({token,job,busy,canBuild,onRefresh}){
 const [image,setImage]=useState(null),[component,setComponent]=useState('vessel'),[concept,setConcept]=useState('ceramic tube'),[consent,setConsent]=useState(false),[saved,setSaved]=useState(null),[notice,setNotice]=useState(''),[pending,setPending]=useState(false);
 useEffect(()=>{let active=true;get('/api/sam-segmentation').then(v=>active&&setSaved(v.latest)).catch(e=>active&&setNotice(e.message));return()=>{active=false;};},[job?.result?.sam_id]);
 async function choose(e){
  setConsent(false);const file=e.target.files?.[0];e.target.value='';if(!file)return;
  try{if(file.type!=='image/png'||file.size>750000)throw new Error('Choose a PNG up to 750 KB, 16–1200 pixels per side.');
   const data=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsDataURL(file);});
   const img=new Image();img.src=data;await img.decode();if(img.width<16||img.height<16||img.width>1200||img.height>1200)throw new Error('Crop the reference to 16–1200 pixels per side.');setImage(data);setNotice('Image selected. Confirm sharing to analyse it.');
  }catch(e){setNotice(e.message);setImage(null);}
 }
 async function segment(){setPending(true);try{
  await action(token,{action:'sam_segment',consent:true,capture:{image_base64:image.split(',')[1],component_id:component,concept,source_url:'',source_locator:'',rights_note:''}});setConsent(false);await onRefresh();setNotice('Image analysis started. Your engineering reviews remain unchanged.');
 }catch(e){setNotice(e.message);}finally{setPending(false);}}
 return <details className='panel sam-inspection'><summary>Reference assets · Meta SAM 3.1 cloud</summary>
  <p>Upload a clear reference photo and name the part you want SAM to find.</p><button type='button' className='text-button' disabled={busy||pending} onClick={async()=>{try{const r=await fetch(demoPhotos.before);if(!r.ok)throw Error('Demo image unavailable.');const blob=await r.blob();const data=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsDataURL(blob);});setImage(data);setComponent('anode');setConcept('metal plate');setConsent(false);setNotice('Synthetic plate selected. Click Segment when ready.');}catch(e){setNotice(e.message);}}}>Load demo reference image</button>
  <div className='fields'><label>Reference PNG<input type='file' accept='image/png' onChange={choose}/></label><label>Component<select value={component} onChange={e=>setComponent(e.target.value)}>{['vessel','wall','anode','cathode','melt','gas'].map(v=><option key={v}>{v}</option>)}</select></label>
  <label>Visible object · one short noun phrase<input value={concept} onChange={e=>setConcept(e.target.value)} maxLength={100}/></label></div>
  {image&&<img src={image} className='sam-preview' alt='Source reference selected for SAM'/>}
  <label className='consent'><input type='checkbox' checked={consent} disabled={busy||pending||!canBuild} onChange={e=>setConsent(e.target.checked)}/>Allow Meta SAM to analyse this image using credits.</label>
  <button type='button' className='button primary' disabled={!consent||!image||!concept.trim()||busy||pending||!canBuild} onClick={segment}>Segment reference with SAM ↗</button>
  <p role='status'>{notice}</p>{job?.action==='sam_segment'&&<p>{job.state==='running'?'SAM is analysing the image…':job.error||job.result?.error||'Image analysis finished.'}</p>}
  {saved&&<><p>Saved · {new Date(saved.created_at).toLocaleString()}</p>{saved.status==='completed'?<Overlay result={saved}/>:<p>{saved.error}</p>}</>}
  
  
 </details>;
}
