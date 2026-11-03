import {demoMaterialModels} from './demo-inputs.js';
import React,{useEffect,useState} from 'react';
import {get} from './api.js';
const fields={
 linear:{rate_um_h:'Measured rate · µm/h',horizon_h:'Scenario duration · h',initial_thickness_um:'Initial thickness · µm'},
 parabolic:{k_parabolic:'Parabolic coefficient · µm/√h',horizon_h:'Total exposure · h',initial_thickness_um:'Initial thickness · µm'},
 arrhenius:{A_pre:'Pre-exponential rate A · µm/h',Q_J_per_mol:'Activation energy · J/mol',temperature_K:'Temperature · K'},
 thermal_cycles:{delta_T_C:'Cycle temperature range · °C',C_constant:'Fitted cycle coefficient C',m_exponent:'Fitted exponent m'},
 thermal_stress:{E_Pa:'Elastic modulus · Pa',alpha_per_K:'Expansion coefficient · 1/K',delta_T_C:'Restrained temperature change · °C'},
 lifetime:{measured_loss_um:'Observed loss · µm',exposure_h:'Observed exposure · h',horizon_h:'Additional comparison horizon · h',initial_thickness_um:'Initial thickness · µm',uncertainty_percent:'Rate sensitivity · ±% (0–99.99)'},
};
const titles={linear:'Linear loss',parabolic:'Parabolic loss',arrhenius:'Arrhenius rate',thermal_cycles:'Empirical thermal-cycle life',thermal_stress:'Restrained thermal stress',lifetime:'Remaining thickness lifetime'};
export default function MaterialModels({report,token,busy}){
 const [model,setModel]=useState('linear'),[values,setValues]=useState({}),[law,setLaw]=useState('linear'),[result,setResult]=useState(null),[notice,setNotice]=useState(''),[pending,setPending]=useState(false),[temperature,setTemperature]=useState(report.input.operating_temperature_C??1600),[props,setProps]=useState(null);
 useEffect(()=>{let active=true;setResult(null);setValues({});get('/api/material-model?assessment_id='+encodeURIComponent(report.id)).then(v=>{if(active&&v.latest){setModel(v.latest.model);setValues(v.latest.parameters);setResult(v.latest);if(v.latest.parameters.model)setLaw(v.latest.parameters.model);}}).catch(e=>{if(active)setNotice(e.message);});return()=>{active=false;};},[report.id]);
 async function post(path,data){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-MRE-Token':token},body:JSON.stringify(data)});const v=await r.json();if(!r.ok)throw Error(v.error);return v;}
 async function run(){setPending(true);setNotice('');try{const parameters={};for(const key of Object.keys(fields[model])){if(values[key]==null||values[key]==='')throw Error('Enter '+fields[model][key]);parameters[key]=Number(values[key]);}if(model==='lifetime')parameters.model=law;setResult(await post('/api/material-model',{assessment_id:report.id,scenario:{model,parameters}}));setNotice('Scenario saved separately. Your agent reviews are unchanged.');}catch(e){setNotice(e.message);}finally{setPending(false);}}
 return <section className='panel'><h3>Material models</h3><button type='button' className='text-button' disabled={busy||pending} onClick={()=>{setValues({...demoMaterialModels[model]});setTemperature(1600);setLaw('linear');setNotice('Synthetic model coefficients loaded for this model; not research-fitted values. Click Calculate to run.');}}>Load demo model inputs</button>

 <details><summary>Temperature-dependent material estimates</summary><label>Scenario temperature · °C<input type='number' value={temperature} onChange={e=>setTemperature(e.target.value)}/></label><button type='button' disabled={!token||busy||pending} onClick={async()=>{try{setProps(await post('/api/material-properties',{temperature_C:Number(temperature)}));}catch(e){setNotice(e.message);}}}>Calculate material properties</button>{props&&<><ul><li>Solid YSZ conductivity: {props.ysz_conductivity_S_m.toPrecision(5)} S/m</li><li>Mo resistivity: {props.mo_resistivity_ohm_m.toExponential(5)} Ω·m</li></ul><p>{props.scope}</p></>}</details>
 <label>Model<select value={model} onChange={e=>{setModel(e.target.value);setValues({});setResult(null);}}>{Object.entries(titles).map(([k,v])=><option key={k} value={k}>{v}</option>)}</select></label>
 {model==='lifetime'&&<label>Observed kinetics<select value={law} onChange={e=>setLaw(e.target.value)}><option value='linear'>Constant rate</option><option value='parabolic'>Parabolic accumulated loss</option></select></label>}
 <div className='fields'>{Object.entries(fields[model]).map(([key,label])=><label key={key}>{label}<input type='number' step='any' value={values[key]??''} onChange={e=>setValues({...values,[key]:e.target.value})}/></label>)}</div>
 <p className='small'>{model==='thermal_cycles'?'Temperature-range power-law surrogate, not a strain-based Coffin–Manson calibration. C and m require material-specific cycle tests.':model==='thermal_stress'?'Fully restrained uniaxial elasticity; free expansion gives zero stress. No crack-growth prediction.':'Use measured or documented coefficients. Exhaustion of thickness is not a validated component-failure criterion.'}</p>
 <button type='button' className='button secondary' disabled={!token||busy||pending} onClick={run}>Calculate & save scenario</button><p role='status'>{notice}</p>{result&&<><ul>{Object.entries(result.result).filter(([,v])=>typeof v==='number'||typeof v==='boolean').map(([k,v])=><li key={k}>{k.replaceAll('_',' ')}: {typeof v==='number'?v.toPrecision(6):String(v)}</li>)}</ul></>}
 </section>;
}
