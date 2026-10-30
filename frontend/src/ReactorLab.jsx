import React,{useEffect,useRef,useState} from 'react';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {simulateScenario} from './api.js';
import './reactor-lab.css';

const labels={inner_radius_mm:'Cathode radius (mm)',outer_radius_mm:'Melt outer radius (mm)',height_mm:'Active height (mm)',conductivity_S_m:'Bulk conductivity (S/m)',thermal_conductivity_W_mK:'Thermal conductivity (W/m·K)',current_A:'Scenario current (A)',inner_temperature_C:'Inner boundary (°C)',outer_temperature_C:'Outer boundary (°C)'};
// Explicit, editable scenario assumptions; no claimed NASA material properties.
const demo={inner_radius_mm:3,outer_radius_mm:12,height_mm:25,conductivity_S_m:10,thermal_conductivity_W_mK:2,current_A:.5,inner_temperature_C:1600,outer_temperature_C:1500};
const pretty=n=>Number(n).toLocaleString(undefined,{maximumSignificantDigits:5});
const stageKeys=['input_validated','arithmetic_verified','original_review','critique','final_review'];
const stageLabels=['Input','Calculations','First review','Critic','Final review'];
const components={vessel:'Outer alumina containment',wall:'YSZ containment / solid electrolyte',anode:'Exterior Pt anode / collector',cathode:'Central Mo cathode',melt:'Regolith melt',gas:'Gas outlet',records:'Measurement records (not a physical part)'};

function Scene({mode,field,fieldScales,report,hypotheses,onSelect,selected,cutaway,asset,partMap,isolate}){
 const host=useRef(null),[error,setError]=useState('');
 useEffect(()=>{
  if(!host.current)return;let renderer,frame,controls,observer;const disposables=[];
  try{
   renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));host.current.appendChild(renderer.domElement);
   const scene=new THREE.Scene();const camera=new THREE.PerspectiveCamera(38,1,.01,100);camera.position.set(4,3.2,4.5);
   controls=new OrbitControls(camera,renderer.domElement);controls.target.set(0,.1,0);controls.enableDamping=true;
   scene.add(new THREE.HemisphereLight(0xd4f9ff,0x17202b,2));const light=new THREE.DirectionalLight(0xffffff,3);light.position.set(3,5,4);scene.add(light);
   const bubbles=[];const meshes=[],theta=cutaway?Math.PI*1.5:Math.PI*2,start=cutaway?Math.PI*.25:0;
   function add(id,geometry,color,opacity=1,fieldColor=false){
    const concern=hypotheses.some(h=>h.components.includes(id));
    const material=new THREE.MeshStandardMaterial({color:fieldColor?color:selected===id?0x9af5e5:concern?0xffa653:color,metalness:.25,roughness:.5,transparent:opacity<1,opacity,side:THREE.DoubleSide});
    const mesh=new THREE.Mesh(geometry,material);mesh.userData.id=id;scene.add(mesh);meshes.push(mesh);disposables.push(geometry,material);return mesh;
   }
   const radius=field?.input.outer_radius_mm||12,inner=field?.input.inner_radius_mm||3,ratio=inner/radius;
   // Normalized source-based arrangement; tube height is illustrative.
   add('vessel',new THREE.CylinderGeometry(1.35,1.35,2.7,64,1,true,start,theta),0x697e91,.17);
   add('wall',new THREE.CylinderGeometry(1.08,1.08,2.5,64,1,true,start,theta),0xd6d8c4,.55);
   add('anode',new THREE.CylinderGeometry(1.10,1.10,.9,48,8,true,start,theta),0xbacbd1,.55).position.y=-.65;
   add('cathode',new THREE.CylinderGeometry(ratio,ratio,2.7,32),0x748f9d).position.y=.2;
   const melt=add('melt',new THREE.CylinderGeometry(1,1,.85,64,1,false,start,theta),0xe87e35,.55);melt.position.y=-.72;
   add('gas',new THREE.CylinderGeometry(.065,.065,.7,16),0x9cb9c3).position.set(.7,1.55,0);
   const sheath=add('cathode',new THREE.CylinderGeometry(ratio*1.15,ratio*1.15,1.45,32),0xc7cec2);sheath.position.y=.82;
   for(const y of [-1.34,1.34]){const rim=add('vessel',new THREE.TorusGeometry(1.35,.045,8,64,theta),0x6f8b9b);rim.rotation.x=Math.PI/2;rim.position.y=y;}
   if(mode==='structure')for(let i=0;i<9;i++){
    const b=add('gas',new THREE.SphereGeometry(.035,8,8),0xb7f5ff,.6);b.position.set(Math.cos(i*.7)*1.17,-.8,Math.sin(i*.7)*1.17);bubbles.push(b);
   }
   if(field&&['thermal','current'].includes(mode)){
    const values=field.samples.map(x=>mode==='thermal'?x.temperature_C:x.current_density_A_m2/10000),lo=fieldScales?.[mode]?.[0]??Math.min(...values),hi=fieldScales?.[mode]?.[1]??Math.max(...values);
    // Radial finite-volume samples extruded in azimuth and height. No invented 3-D gradients.
    field.samples.forEach((s,i)=>{
     const r=s.radius_mm/radius;const geom=new THREE.CylinderGeometry(r,r,.82,64,1,true,start,theta);
     const c=new THREE.Color().setHSL(.66*(1-(values[i]-lo)/(hi-lo||1)),.9,.52);
     const m=add('melt',geom,c,.72,true);m.position.y=-.72;
    });
    if(mode==='current')for(let j=0;j<12;j++){
     const angle=start+(j+.5)*theta/12;const p=new THREE.Vector3(Math.cos(angle),0,Math.sin(angle));
     const arrow=new THREE.ArrowHelper(p.clone().negate(),p.clone().multiplyScalar(.92).setY(-.72),Math.max(.05,.82-ratio),0x9ee9ff,.08,.035);scene.add(arrow);
     disposables.push(arrow.line.geometry,arrow.line.material,arrow.cone.geometry,arrow.cone.material);
    }
   }
   if(mode==='wear'&&report?.input.wall_loss_um!=null){
    // Uniform ring overlay communicates scalar measured recession, not localized/predicted damage.
    const ring=add('wall',new THREE.CylinderGeometry(1.09,1.09,.9,64,1,true,start,theta),0xff9f5c,.8);ring.position.y=-.65;
   }
   if(asset&&mode==='structure'){
    meshes.forEach(m=>m.visible=false);meshes.length=0;
    const model=asset.scene.clone(true);const box=new THREE.Box3().setFromObject(model),size=box.getSize(new THREE.Vector3()),center=box.getCenter(new THREE.Vector3());
    const group=new THREE.Group();model.position.sub(center);group.add(model);group.scale.setScalar(2.8/Math.max(size.x,size.y,size.z,.001));scene.add(group);
    model.traverse(node=>{if(!node.isMesh)return;node.geometry=node.geometry.clone();disposables.push(node.geometry);
     const id=partMap[node.name];node.userData.id=id||null;
     const mats=Array.isArray(node.material)?node.material:[node.material];const clones=mats.map(m=>{const c=m.clone();if(id===selected)c.color?.set(0x9af5e5);else if(id&&hypotheses.some(h=>h.components.includes(id)))c.color?.set(0xffa653);disposables.push(c);return c;});
     node.material=Array.isArray(node.material)?clones:clones[0];if(id)meshes.push(node);
    });
   }
   if(isolate)meshes.forEach(m=>{m.visible=m.userData.id===selected;});
   const ray=new THREE.Raycaster(),pointer=new THREE.Vector2();
   const click=e=>{const box=renderer.domElement.getBoundingClientRect();pointer.set((e.clientX-box.left)/box.width*2-1,-(e.clientY-box.top)/box.height*2+1);ray.setFromCamera(pointer,camera);const hit=ray.intersectObjects(meshes).find(h=>h.object.userData.id && (!h.object.material.opacity || h.object.material.opacity>.25));if(hit)onSelect(hit.object.userData.id);};
   renderer.domElement.addEventListener('click',click);disposables.push({dispose:()=>renderer.domElement.removeEventListener('click',click)});
   observer=new ResizeObserver(()=>{const w=host.current?.clientWidth||600,h=420;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();});observer.observe(host.current);
   let last=0;function animate(t){if(t-last>30){controls.update();if(!matchMedia('(prefers-reduced-motion: reduce)').matches)bubbles.forEach((b,i)=>{b.position.y=-.9+((t/5000+i/9)%1)*2.1;});renderer.render(scene,camera);last=t;}frame=requestAnimationFrame(animate);}frame=requestAnimationFrame(animate);
  }catch(e){setError('3D rendering is unavailable in this browser. The numerical results and evidence remain readable.');}
  return()=>{cancelAnimationFrame(frame);observer?.disconnect();controls?.dispose();disposables.forEach(x=>x.dispose?.());renderer?.dispose();renderer?.domElement.remove();};
 },[mode,field,fieldScales,report,hypotheses,selected,cutaway,onSelect,asset,partMap,isolate]);
 return <div className='reactor-canvas' ref={host} role='img' aria-label='Interactive source-based hollow-anode cutaway; drag to rotate, scroll to zoom'>{error&&<p>{error}</p>}</div>;
}

export default function ReactorLab({report=null,token,scenario,onScenario,busy=false,sceneHypotheses=null,simulatedField=null,simulatedOutputs=null,simulatedMaterial=null,simulatedComponent=null,fieldScales=null}){
 const [inspectionEvidence,setInspectionEvidence]=useState(null);
 const [asset,setAsset]=useState(null),[partMap,setPartMap]=useState({}),[isolate,setIsolate]=useState(false);
 const receipt=report?.tools?.find(t=>t.tool==='reactor_field_simulation')?.result;
 const [input,setInput]=useState(scenario||receipt?.input||report?.input.reactor_scenario||{}),[field,setField]=useState(receipt||null),[comparison,setComparison]=useState(null),[mode,setMode]=useState('structure'),[selected,setSelected]=useState('wall'),[cutaway,setCutaway]=useState(true),[stage,setStage]=useState(4),[notice,setNotice]=useState(''),[running,setRunning]=useState(false);
 useEffect(()=>{if(scenario)setInput(scenario);},[scenario]);
 useEffect(()=>{if(simulatedField){setField(simulatedField);setInput(simulatedField.input);setMode('thermal');}},[simulatedField]);
 useEffect(()=>{if(simulatedComponent)setSelected(simulatedComponent);},[simulatedComponent]);
 useEffect(()=>{const listener=e=>{if(!components[e.detail?.component])return;setSelected(e.detail.component);setInspectionEvidence(e.detail);setMode('structure');};window.addEventListener('mre-component-evidence',listener);return()=>window.removeEventListener('mre-component-evidence',listener);},[]);
 const onSelect=React.useCallback(id=>setSelected(id),[]);
 const hypotheses=React.useMemo(()=>stage===4?(sceneHypotheses?.result?.hypotheses||[]):[],[stage,sceneHypotheses]);
 const selectedHypotheses=hypotheses.filter(h=>h.components.includes(selected));
 const events=stageKeys.map((key,i)=>({key,label:stageLabels[i],exists:i===0?Boolean(report):i===1?Boolean(report?.accounting):Boolean(report?.[key])}));
 async function importMesh(event){
  const file=event.target.files?.[0];if(!file)return;
  try{
   if(!file.name.toLowerCase().endsWith('.glb')||file.size>20_000_000)throw new Error('Use an embedded GLB mesh no larger than 20 MB.');
   const buffer=await file.arrayBuffer();if(new DataView(buffer).getUint32(0,true)!==0x46546c67)throw new Error('This file is not a binary GLB mesh.');
   const manager=new THREE.LoadingManager();manager.setURLModifier(url=>{if(url.startsWith('blob:')||url.startsWith('data:'))return url;throw new Error('External mesh resources are not allowed. Export one embedded GLB file.');});
   const gltf=await new Promise((resolve,reject)=>new GLTFLoader(manager).parse(buffer,'',resolve,reject));
   const names=[];gltf.scene.traverse(n=>{if(n.isMesh){if(!n.name)n.name='mesh-'+names.length;if(names.includes(n.name))n.name+='-'+names.length;names.push(n.name);}});
   if(!names.length||names.length>300)throw new Error('Mesh must contain 1–300 named parts.');
   setAsset({scene:gltf.scene,names,filename:file.name});setPartMap(Object.fromEntries(names.filter(n=>components[n.split('__')[0]]).map(n=>[n,n.split('__')[0]])));setMode('structure');setNotice('Visual mesh loaded locally. Map its named parts below. It is not used as verified solver geometry or scientific evidence.');
  }catch(e){setNotice(e.message);}
 }
 async function solve(compare=false){
  setRunning(true);setNotice('');try{
   const value=Object.fromEntries(Object.keys(labels).map(k=>[k,input[k]===''||input[k]==null?null:Number(input[k])]));
   const next=await simulateScenario(token,value);
   if(compare&&field)setComparison({before:field,after:next});else setComparison(null);
   setField(next);setMode('thermal');onScenario?.(next.input);setNotice('Scenario calculated. These assumptions are attached to your next Meta assessment; no Meta request was made by this calculation.');
  }catch(e){setNotice(e.message);}finally{setRunning(false);}
 }
 return <section className='panel reactor-lab'><span className='eyebrow'>REACTOR LAB · BOUNDED NUMERICAL SCENARIO</span><h2>Inspect reactor</h2>
  {report&&report.input.configuration!=='hollow_ysz_pt'&&<p className='message'>This input uses another or unspecified configuration. This schematic is a reference illustration and does not represent your reactor geometry.</p>}<details><summary>Geometry source & limitations</summary><p className='small'>Yu et al. inverted hollow-anode arrangement: central Mo cathode, regolith inside YSZ, Pt collector outside, outer alumina enclosure. Normalized schematic; not an as-built CAD model or calibrated digital twin.</p></details>
  {report&&<details><summary>Source-based Blender visual mesh</summary><p className='small'>Import the named GLB exported by scripts/build_reactor_asset.py in Blender. Canonical part names map automatically. SAM reference masks guide appearance only; hidden geometry remains an approximation. The source-based schematic remains the default.</p><label>Embedded GLB visual asset<input type='file' accept='.glb' onChange={importMesh}/></label>
   {asset&&<><p>{asset.filename} · local session only; your assessment is unchanged.</p><div className='fields'>{asset.names.map(name=><label key={name}>{name}<select value={partMap[name]||''} onChange={e=>setPartMap(p=>({...p,[name]:e.target.value}))}><option value=''>Unmapped visual part</option>{Object.entries(components).filter(([id])=>id!=='records').map(([id,label])=><option key={id} value={id}>{label}</option>)}</select></label>)}</div><button type='button' className='text-button' onClick={()=>{setAsset(null);setPartMap({});}}>Return to source-based schematic</button><p className='small'>Component mapping is user-declared. Thermal/current fields remain available only on the idealized scenario geometry.</p></>}
  </details>}
  <div className='reactor-toolbar'>{[['structure','Cutaway'],['thermal','Temperature'],['current','Bulk current'],['wear','Wall observation']].map(([key,label])=><button type='button' key={key} aria-pressed={mode===key} disabled={['thermal','current'].includes(key)&&(!field||Boolean(asset))} onClick={()=>setMode(key)}>{label}</button>)}<label><input type='checkbox' checked={cutaway} disabled={Boolean(asset)} onChange={e=>setCutaway(e.target.checked)}/>Cut away shell{asset?' (asset has fixed cutaway)':''}</label><label><input type='checkbox' checked={isolate} onChange={e=>setIsolate(e.target.checked)}/>Isolate selected component</label></div>
  {simulatedMaterial&&<p className='input-origin'>Conditional {simulatedMaterial.component} recession: {pretty(simulatedMaterial.measured_loss_um)} → {pretty(simulatedMaterial.total_loss_um)} µm over an additional {pretty(simulatedMaterial.horizon_h)} h. Remaining thickness: {pretty(simulatedMaterial.remaining_thickness_um)} µm. No spatial damage map or validated corrosion law.</p>}
  {simulatedOutputs&&<div className='input-origin'><strong>Computed scenario outcome</strong><ul>{Object.entries(simulatedOutputs).map(([k,v])=><li key={k}>{k.replaceAll('_',' ')}: {pretty(v)}</li>)}</ul><small>No spatial damage map is inferred from these scalar outputs.</small></div>}
  <div className='reactor-layout'><div><Scene {...{mode,field,fieldScales,report,hypotheses,onSelect,selected,cutaway,asset,partMap,isolate}}/><p className='small'>Drag to rotate · scroll to zoom · click a part. Orange = hypothesis, not confirmed damage. Bubbles are illustrative.</p>{field&&['thermal','current'].includes(mode)&&<p className='field-legend'>Blue → red: {pretty(fieldScales?.[mode]?.[0]??Math.min(...field.samples.map(s=>mode==='thermal'?s.temperature_C:s.current_density_A_m2/10000)))} → {pretty(fieldScales?.[mode]?.[1]??Math.max(...field.samples.map(s=>mode==='thermal'?s.temperature_C:s.current_density_A_m2/10000)))} {mode==='thermal'?'°C':'A/cm²'} · radial scenario only. Inner boundary {pretty(field.input.inner_temperature_C)} °C; outer boundary {pretty(field.input.outer_temperature_C)} °C. Colours show cell centres, not the boundary surfaces.</p>}</div>
   <aside><label>Inspect component<select value={selected} onChange={e=>setSelected(e.target.value)}>{Object.entries(components).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></label><h3>{components[selected]}</h3>{inspectionEvidence?.component===selected&&<div className='input-origin'><p>{inspectionEvidence.summary}<br/>Source: {inspectionEvidence.source}</p>{inspectionEvidence.images?.map((src,i)=><figure key={i}><img src={src} alt={i===0?'Before test component':'After test component'} style={{maxWidth:'100%',maxHeight:200}}/><figcaption>{i===0?'Before test':'After test'}</figcaption></figure>)}</div>}{report&&<p className='small'>Submitted record: {report.input.current_A!=null?`${pretty(report.input.current_A)} A declared current`:'measured current history'} · {report.input.temperature_C!=null?`${pretty(report.input.temperature_C)} °C reported operating temperature`:'temperature not supplied'}. These are not spatial sensor readings.</p>}
    {selectedHypotheses.length?selectedHypotheses.map((h,i)=><article key={i} className='component-hypothesis'><span className='pill'>Unconfirmed hypothesis</span><p><strong>{h.explanation}</strong></p><p>{h.basis}</p><details><summary>Measurements, calculations & sources</summary><h4>Measurements</h4><ul>{h.input_fields.map(k=><li key={k}>{k.replaceAll('_',' ')}: {Array.isArray(report.input[k])?`${report.input[k].length} supplied samples`:typeof report.input[k]==='object'?'Recorded structured input':String(report.input[k]??'Not supplied')}</li>)}</ul>
      {h.metric_ids.length>0&&<><h4>Calculations</h4><ul>{h.metric_ids.map(k=>{const m=report.performance.metrics[k];return <li key={k}>{m.label}: {pretty(m.value)} {m.unit}<small>{m.formula}</small></li>;})}</ul></>}
      <h4>Research and applicability</h4><p className='small'>{h.applicability}</p>{h.research_refs.map(id=>{const source=report.sources.find(s=>s.id===id);return source?<p className='small' key={id}><a href={source.url} target='_blank' rel='noreferrer'>{source.title||source.id} ↗</a><br/>{source.locator}<br/>{source.fact}</p>:null;})}</details><h4>Next check</h4><p>{h.test_to_distinguish}</p></article>):<p className='small'>{sceneHypotheses?'No hypothesis links this component at this stage.':'No result-linked component hypotheses generated yet. The schematic is neutral.'}</p>}
    {mode==='wear'&&<p>{report?.input.wall_loss_um!=null?`Reported recession: ${pretty(report.input.wall_loss_um)} µm. Orange ring marks the affected component only; location and progression are not measured by this scalar.`:'Add a measured wall-loss record to assess recession. No damage value has been invented.'}</p>}
    {report?.critique&&stage===3&&<p>{report.critique.weakness}</p>}
   </aside></div>
  {report&&<div className='reactor-replay'><h3>Investigation replay</h3>{events.map((e,i)=><button key={e.key} type='button' disabled={!e.exists} aria-pressed={stage===i} onClick={()=>setStage(i)}>{e.label}</button>)}<p className='small'>Replays this saved investigation. No future physical outcome or new API request is implied.</p></div>}
  <details><summary>Calculate and compare a thermal / bulk-current scenario</summary><p>Enter geometry, constant properties and boundary temperatures. These are modeling assumptions, separate from your measured reactor record. The model solves steady radial heat conduction with ohmic heating; interfaces, chemistry, radiation and fluid flow are excluded.</p>
   {<button type='button' className='text-button' disabled={busy} onClick={()=>{setInput({...demo});setNotice('Editable demonstration assumptions loaded — not NASA measurements or recommended operating settings.');}}>Load clearly labelled demo assumptions</button>}
   <div className='fields'>{Object.entries(labels).map(([key,label])=><label key={key}>{label}<input type='number' step='any' disabled={busy} value={input[key]??''} onChange={e=>setInput(p=>({...p,[key]:e.target.value}))}/></label>)}</div>
   {token&&<div className='actions'><button type='button' className='button secondary' disabled={busy||running||!token} onClick={()=>solve(false)}>Calculate scenario</button><button type='button' className='button secondary' disabled={busy||running||!token||!field} onClick={()=>solve(true)}>Compare changed scenario</button><button type='button' className='text-button' disabled={busy} onClick={()=>{onScenario?.(null);setField(null);setComparison(null);setInput({});}}>Remove scenario</button></div>}
   <p role='status'>{notice}</p>
   {field&&<><div className='table-scroll'><table><thead><tr><th>Computed quantity</th><th>Scenario result</th></tr></thead><tbody>{[['Bulk ohmic resistance',field.bulk_resistance_ohm,'Ω'],['Bulk voltage (not full cell voltage)',field.bulk_voltage_V,'V'],['Joule heating',field.joule_power_W,'W'],['Peak radial temperature',field.peak_temperature_C,'°C'],['Analytic comparison error',field.verification.analytic_max_error_C,'°C'],['Heat balance residual',field.verification.energy_balance_error_W,'W']].map(([label,v,u])=><tr key={label}><td>{label}</td><td>{pretty(v)} {u}</td></tr>)}</tbody></table></div><p className='small'>Mesh refinement peak change: {pretty(field.verification.peak_mesh_change_C)} °C. Numerical checks establish consistency within this simplified model, not agreement with a measured reactor temperature field.</p></>}
   {comparison&&<p>Changed scenario: power {pretty(comparison.before.joule_power_W)} → {pretty(comparison.after.joule_power_W)} W; peak {pretty(comparison.before.peak_temperature_C)} → {pretty(comparison.after.peak_temperature_C)} °C. All edited assumptions, not just current, are included.</p>}
  </details>
  <p className='small'><a href='https://ntrs.nasa.gov/citations/20250004626' target='_blank' rel='noreferrer'>Geometry source: Yu et al. 2025 ↗</a> · <a href='https://tfaws.nasa.gov/wp-content/uploads/TFAWS2024-ID-04.pdf' target='_blank' rel='noreferrer'>NASA thermal/CFD study, 2024 ↗</a>. This radial solver does not reproduce NASA’s COMSOL model. A full reactor twin needs measured geometry, material properties, interface models and independent validation.</p>
 </section>;
}
