import HypothesisLayer from './HypothesisLayer.jsx';
import ReactorLab from './ReactorLab.jsx';
import {assessmentLabel} from './review-labels.js';
import React, {useCallback, useEffect, useRef, useState} from 'react';
import {get, action, saveDraft} from './api.js';
import {parseCurrentTrace,formatCurrentTrace} from './manual-trace.js';
import {applyAssessmentOptions} from './assessment-options.js';
import {readBackup,writeBackup,chooseDraft,browserStorage} from './draft-storage.js';

const options = {gas_accounting_review: 'Gas accounting', current_record_review: 'Electrical record', material_characterization_review: 'Material evidence', repeat_run_comparison: 'Comparable runs'};
const numbers = ['current_A','collected_o2_g','temperature_C','voltage_V','sample_mass_g','oxygen_uncertainty_g','current_uncertainty_A','duration_uncertainty_s','available_hours','budget_usd'];
const texts = ['experiment_name','question','feedstock','anode_material','cathode_material','calibration_reference','gas_measurement_method','records_reference','observations','source_label'];
const stages = [['input_validated','Read input'],['arithmetic_verified','Check calculations'],['original_review','First review'],['critique','Challenge'],['final_review','Final review']];
const fmt = value => typeof value === 'number' && Number.isFinite(value) ? value.toLocaleString(undefined, {maximumSignificantDigits: 7}) : 'Not available';
const fit = value => value == null ? 'Unknown' : value ? 'Yes' : 'No';
function toForm(data = {}) {
  const result = {...data, duration_h: data.duration_s == null ? '' : data.duration_s / 3600, trace: [], resistance_trace: [], current_trace_text: formatCurrentTrace(data.trace || []), resistance_text: (data.resistance_trace || []).map(r => `${r.time_s},${r.resistance_ohm},${r.source || ''}`).join('\n'),
    configuration: data.configuration || 'unknown', calibration_status: data.calibration_status || 'unknown', time_alignment: data.time_alignment || 'unknown',
    analysis_id: data.composition?.analysis_id || '', composition_source: data.composition?.source || '', composition_text: data.composition?.rows.map(r => `${r.oxide},${r.wt_percent}`).join('\n') || '', test_estimates: data.test_estimates || {}};
  [...numbers,...texts].forEach(key => result[key] = data[key] ?? '');
  return result;
}
function asNumber(value, key) {
  if (value === '' || value == null) return null;
  const number = Number(value);
  if (!Number.isFinite(number)) throw new Error(`Enter a finite number for ${key}.`);
  return number;
}
function payload(form,contract,settings = {}) {
  const result = {process: 'molten_regolith_electrolysis'};
  numbers.forEach(key => result[key] = asNumber(form[key], key));
  texts.forEach(key => result[key] = form[key]?.trim() || null);
  ['configuration','calibration_status','time_alignment'].forEach(key => result[key] = form[key]);
  const hours = asNumber(form.duration_h, 'duration'); result.duration_s = hours == null ? null : hours * 3600;
  result.trace = parseCurrentTrace(form.current_trace_text || '');
  if (result.trace.length) {result.current_A = null; result.voltage_V = null;}
  result.composition = null;
  if (form.composition_text.trim()) {
    const rows = form.composition_text.trim().split(/\r?\n/).filter(s => s.trim()).map(line => {
      const parts = line.split(',').map(s => s.trim());
      if (parts.length !== 2 || !parts[0] || !parts[1]) throw new Error('Composition format: one oxide,wt_percent per line.');
      return {oxide: parts[0], wt_percent: asNumber(parts[1], 'oxide wt%')};
    });
    result.composition = {analysis_id: form.analysis_id.trim(), source: form.composition_source.trim(), rows};
  }
  result.test_estimates = {};
  Object.keys(options).forEach(key => result.test_estimates[key] = {hours: asNumber(form.test_estimates[key]?.hours, key), cost_usd: asNumber(form.test_estimates[key]?.cost_usd, key)});
  contract.fields.forEach(f => result[f.key] = f.numeric ? asNumber(form[f.key],f.label) : String(form[f.key] ?? '').trim() || null);
  Object.entries(contract.choices).forEach(([key,spec]) => result[key] = form[key] ?? spec.values[0][0]);
  result.resistance_trace = (form.resistance_text || '').trim() ? form.resistance_text.trim().split(/\r?\n/).filter(s=>s.trim()).map(line => {
    const [time,resistance,...source] = line.split(',').map(s=>s.trim());
    if (!time || !resistance) throw new Error('Resistance rows: time_s,resistance_ohm,optional source');
    return {time_s:asNumber(time,'resistance time'),resistance_ohm:asNumber(resistance,'resistance'),source:source.join(',') || null};
  }) : [];
  if(form.reactor_scenario)result.reactor_scenario=form.reactor_scenario;
  return applyAssessmentOptions(result,settings);
}

const hiddenEvidenceKeys=new Set(['id','evidence_id','input_sha256','sha256','kind','exact_values_location']);
function ReadableEvidence({value}) {
  if(value==null)return <span>Not supplied</span>;
  if(typeof value==='boolean')return <span>{value?'Yes':'No'}</span>;
  if(typeof value!=='object')return <span>{typeof value==='number'?fmt(value):String(value).replaceAll('_',' ')}</span>;
  if(Array.isArray(value))return <ul>{value.map((item,i)=><li key={i}><ReadableEvidence value={item}/></li>)}</ul>;
  return <dl className='readable-evidence'>{Object.entries(value).filter(([key])=>!hiddenEvidenceKeys.has(key)).map(([key,v])=><React.Fragment key={key}><dt>{key.replaceAll('_',' ')}</dt><dd><ReadableEvidence value={v}/></dd></React.Fragment>)}</dl>;
}
function Field({form, setForm, name, label, unit, help, number = false, required = false, wide = false, disabled = false, textarea = false, choices}) {
  const id = `input-${name}`;
  const props = {id, name, value: form[name] ?? choices?.[0]?.[0] ?? '', required, disabled, onChange: e => setForm(previous => ({...previous, [name]: e.target.value}))};
  return <label htmlFor={id} className={wide ? 'wide' : ''}>{label}{required && <span className='required-mark' aria-label='required'> *</span>}{unit && <span className="unit">{unit}</span>}
    {choices ? <select {...props}>{choices.map(([value,text]) => <option key={value} value={value}>{text}</option>)}</select> : textarea ? <textarea {...props} rows={3} maxLength={['current_trace_text','resistance_text'].includes(name)?450000:name === 'observations'?1000:500}/> : <input {...props} type={number ? 'number' : 'text'} step={number ? 'any' : undefined} min={number ? '0' : undefined} maxLength={number ? undefined : 500}/>}
    {help && <small>{help}</small>}</label>;
}
function Detail({label, children}) {return <dl className="detail"><dt>{label}</dt><dd>{children ?? 'Not supplied'}</dd></dl>;}
const groups = {electrical:'Resistance, current density and measurement conditions',materials:'Measured wall loss, thermal exposure and cycles',endurance:'Observed endurance versus projected lifetime',energy:'Measured energy and system boundary',production:'Gas purity and collection evidence',environment:'Environment and post-test characterization',system:'Optional NASA system-demonstration context',targets:'Your source-linked engineering requirements'};
function FormTabs({id,items,selected,onSelect}) {
  function move(event,index){
    const keys={ArrowRight:1,ArrowLeft:-1,Home:'first',End:'last'};
    if(!(event.key in keys))return;event.preventDefault();
    const direction=keys[event.key],next=direction==='first'?0:direction==='last'?items.length-1:(index+direction+items.length)%items.length;
    onSelect(items[next][0]);event.currentTarget.parentElement.querySelectorAll('[role=tab]')[next]?.focus();
  }
  return <div className='form-tabs' role='tablist' aria-label={id==='setup'?'Experiment setup steps':id==='result'?'Assessment result sections':'Measurement categories'}>{items.map(([key,label],i)=><button key={key} type='button' role='tab' id={`${id}-tab-${key}`} aria-controls={`${id}-panel-${key}`} aria-selected={selected===key} tabIndex={selected===key?0:-1} onKeyDown={e=>move(e,i)} onClick={()=>onSelect(key)}><span className='tab-number'>{i+1}</span>{label}</button>)}</div>;
}
function ParameterGroup({group,contract,form,setForm,advanced=false}) {
  const advancedKeys=new Set(['retirement_wall_loss_um','projection_model','reported_projected_lifetime_h','projection_reference']);
  if(!contract)return <p>Loading measurement definitions…</p>;
  return <section className='parameter-group'><h3>{groups[group]}</h3><div className='fields'>
    {contract.fields.filter(f=>f.group===group && (advanced||!advancedKeys.has(f.key))).map(f=><Field key={f.key} form={form} setForm={setForm} name={f.key} label={f.label} number={f.numeric} unit={f.unit} wide={!f.numeric}/>)}
    {Object.entries(contract.choices).filter(([key,spec])=>spec.group===group && (advanced||!advancedKeys.has(key)) && key!=='comparison_profile').map(([key,spec])=><Field key={key} form={form} setForm={setForm} name={key} label={spec.label} choices={spec.values}/>)}
    {group==='electrical'&&<Field form={form} setForm={setForm} name='resistance_text' label='Measured resistance history — optional' wide textarea help='time_s,resistance_ohm,optional record. Use a history OR endpoints; measurements need comparable conditions.'/>}
  </div></section>;
}
function ComparisonOptions({form,setForm,customTargets,setCustomTargets}) {
  const official=form.comparison_profile==='nasa_leia_2026_topic2';
  return <details><summary>Optional comparison settings</summary><p className='small'>Published observations are always checked for applicability. Read their original values in the separate Reference data tab.</p>
    <label className='option-card'><input type='checkbox' checked={official} onChange={e=>setForm(p=>({...p,comparison_profile:e.target.checked?'nasa_leia_2026_topic2':'none'}))}/><span><strong>Include NASA 2026 integrated-system demonstration clauses</strong><small>Optional. Adds System measurements. Laboratory cells are not automatically applicable to full-system requirements.</small></span></label>
    <label className='option-card'><input type='checkbox' checked={customTargets} onChange={e=>setCustomTargets(e.target.checked)}/><span><strong>Use my own design requirements / lifetime assumptions</strong><small>Optional advanced mode. Adds a Design requirements measurement category. Your own targets are separate from read-only published reference data; saved targets are excluded until enabled.</small></span></label>
  </details>;

}

function ResistanceHistory({rows}) {
  if(!rows?.length)return null;
  const xs=rows.map(r=>r.time_s/3600),ys=rows.map(r=>r.resistance_ohm),minX=Math.min(...xs),maxX=Math.max(...xs),low=Math.min(...ys),high=Math.max(...ys),pad=(high-low)*.08 || Math.max(Math.abs(low)*.02,.001);
  const x=v=>55+(v-minX)/(maxX-minX)*650,y=v=>165-(v-(low-pad))/(high-low+2*pad)*125;
  const points=rows.map(r=>`${x(r.time_s/3600)},${y(r.resistance_ohm)}`).join(' ');
  return <figure className='resistance-history'><figcaption>Supplied resistance history — observations, not a forecast</figcaption><svg viewBox='0 0 760 215' role='img' aria-label={`Resistance history with ${rows.length} supplied points; measurement comparability must be checked`}><line x1='55' y1='165' x2='705' y2='165' stroke='currentColor'/><line x1='55' y1='30' x2='55' y2='165' stroke='currentColor'/><polyline points={points} fill='none' stroke='#89dfd0' strokeWidth='2'/><text x='8' y='25' fill='currentColor'>Ω</text><text x='4' y='48' fill='currentColor'>{fmt(high)}</text><text x='4' y='163' fill='currentColor'>{fmt(low)}</text><text x='55' y='190' fill='currentColor'>{fmt(minX)} h</text><text x='665' y='190' fill='currentColor'>{fmt(maxX)} h</text></svg><p className='small'>Lines connect supplied samples only. All rows are used in the reported descriptive slope; this is not evidence of improved efficiency or statistical significance.</p></figure>;
}
function EvidenceRefs({refs,report}) {
  return <div className='brief-references'>{refs.map(id=>{
    const source=report.sources.find(s=>s.id===id),receipt=report.tools.find(t=>t.evidence_id===id);
    return source?<p className='small' key={id}><a href={source.url} target='_blank' rel='noopener noreferrer'>{source.title || source.id} ↗</a> — {source.locator}</p>:<p className='small' key={id}>{receipt?`Executed ${receipt.tool.replaceAll('_',' ')} check`:id==='input-record'?'Your submitted measurement record':id}</p>;
  })}</div>;
}
function PerformanceResults({report:r}) {
  const p=r.performance;
  if (!p) return <p className="small">This archived assessment predates the structured performance module.</p>;
  const decisions=r.final_review?.assessments || [];
  return <>
    <section className="panel"><h2>Performance assessment</h2><p className="small">Calculated metrics, published observations, selected NASA clauses and your targets are distinct evidence layers. Model findings are drafts tied to this input. “Recorded observation” means supported by the supplied record or calculation; it does not mean good performance, an authenticated measurement or a requirement passed.</p>

      <ResistanceHistory rows={r.input.resistance_trace}/>
      <details open><summary>Calculated metrics — values, units and formulas</summary><div className="table-scroll"><table><thead><tr><th>Metric</th><th>Value</th><th>Basis / calculation</th><th>Arithmetic check</th></tr></thead><tbody>{Object.entries(p.metrics).filter(([,m])=>m.value!=null).map(([key,m])=><tr key={key}><td>{m.label}</td><td>{m.value==null?'Not available':`${fmt(m.value)} ${m.unit}`}</td><td>{m.formula}<small>{m.input_fields.join(', ')}</small></td><td>{m.value==null?'Not calculated':m.independent_check.passed?'Independent arithmetic agrees':'Needs review'}</td></tr>)}</tbody></table></div><p className="small">Resistance basis: {p.resistance_basis.replaceAll('_',' ')}. Comparable measurement conditions documented: {p.resistance_comparable?'Reported yes':'Not established'}. Wall-loss time basis: {p.wall_rate_time_basis.replaceAll('_',' ')}. Energy boundary: {p.energy_boundary.replaceAll('_',' ')}.</p></details>
      {Object.values(p.metrics).some(m=>m.value==null)&&<details><summary>Additional metrics need more inputs or a matching measurement basis</summary><ul>{Object.entries(p.metrics).filter(([,m])=>m.value==null).map(([key,m])=><li key={key}>{m.label}: check {m.input_fields.join(', ')}. Blank inputs are not zero; alternative trace/scalar inputs are evaluated by the backend.</li>)}</ul></details>}
      {p.publication_comparisons && <details open><summary>Research observations — applicability checked separately</summary><p className='small'>{p.publication_comparisons.status.replaceAll('_',' ')} · {p.publication_comparisons.scope}</p>{p.publication_comparisons.unmatched_context?.length>0&&<p>Context not matched: {p.publication_comparisons.unmatched_context.join(', ')}</p>}{p.publication_comparisons.reference_cases?.length>0&&<><p>Published examples remain visible for context. Their conditions do not match this input; no direct difference or health verdict is calculated.</p><ReadableEvidence value={p.publication_comparisons.reference_context}/><div className='table-scroll'><table><thead><tr><th>Published case</th><th>Collected O₂ / electrolysis time</th><th>Resistance endpoints</th><th>Wall loss / hot exposure</th></tr></thead><tbody>{p.publication_comparisons.reference_cases.map(c=><tr key={c.id}><td>{c.id}<small>{c.locator}</small></td><td>{c.collected_o2_g} g / {c.duration_h} h</td><td>{c.initial_resistance_ohm} → {c.final_resistance_ohm} Ω</td><td>{c.wall_loss_um} ± {c.wall_loss_printed_bound_um} µm / {c.thermal_exposure_h} h</td></tr>)}</tbody></table></div><a href={p.publication_comparisons.source_url} target='_blank' rel='noopener noreferrer'>Open original research ↗</a></>}{p.publication_comparisons.comparisons.length>0&&<div className='table-scroll'><table><thead><tr><th>Parameter</th><th>Your reported value</th><th>Publication</th><th>Difference / basis gap</th></tr></thead><tbody>{p.publication_comparisons.comparisons.map(c=><tr key={c.field}><td>{c.field.replaceAll('_',' ')}</td><td>{fmt(c.reported_input)} {c.unit}</td><td>{fmt(c.published_value)} {c.unit}<small>{c.locator}</small></td><td>{c.comparison_basis_gap || fmt(c.difference)}</td></tr>)}</tbody></table></div>}</details>}
      {p.input_consistency_flags.length>0 && <div className="message"><h3>Input consistency requires review</h3>{p.input_consistency_flags.map(f=><p key={f}>{f.replaceAll('_',' ')}</p>)}</div>}
      {p.target_checks.length>0 && <details open><summary>Your declared requirement comparisons</summary><div className="table-scroll"><table><thead><tr><th>Target</th><th>Actual / target</th><th>Conditional result</th><th>Evidence missing</th></tr></thead><tbody>{p.target_checks.map(c=><tr key={c.target_field}><td>{c.target_field.replaceAll('_',' ')}</td><td>{fmt(c.actual)} / {fmt(c.target)}<small>{c.direction}</small></td><td>{c.status.replaceAll('_',' ')}</td><td>{c.missing_prerequisites.join(', ')||'No prerequisite gap identified'}<small>{c.target_reference}</small></td></tr>)}</tbody></table></div></details>}
      {p.official_profile_checks?.length>0 && <details open><summary>NASA 2026 LEIA Topic 2 — selected-clause comparison</summary><p className="small">This is a scoped comparison, not full solicitation compliance, a universal reactor grade or flight qualification. Notional contaminant targets require downstream specification/basis review.</p><div className="table-scroll"><table><thead><tr><th>Clause / kind</th><th>Source reference</th><th>Your value</th><th>Outcome / remaining evidence</th></tr></thead><tbody>{p.official_profile_checks.map(c=><tr key={c.id}><td>{c.id}<small>{c.kind.replaceAll('_',' ')}</small></td><td>{c.value} {c.unit}<small>{c.basis}</small></td><td>{fmt(c.actual)}</td><td>{c.status.replaceAll('_',' ')}<small>{c.missing.join(', ')}</small></td></tr>)}</tbody></table></div><a href="https://sam.gov/opp/812c81b0f0b84943be12a5f29615d3c8/view" target="_blank" rel="noopener noreferrer">Official source: Attachment B2 ↗</a></details>}
      <h3>{r.local_preview?'Next: Meta interpretation after your authorization':'Meta interpretation of these comparisons'}</h3>
      {decisions.length ? <div className="assessment-grid">{decisions.map(a=><article key={a.dimension} className={'assessment-card '+a.status}><span className="eyebrow">{a.dimension.replaceAll('_',' ')}</span><p className="pill">{assessmentLabel(a.status)}</p><p>{a.finding}</p>{a.basis&&<Detail label='Why'>{a.basis}</Detail>}<EvidenceRefs refs={a.evidence_refs} report={r}/><h3>Improvement / next evidence</h3><p className="small">{a.improvement_or_next_evidence}</p><a href={'#decision-'+a.dimension}>Show decision evidence ↓</a></article>)}</div> : <p>{r.local_preview?'Local preview only. Meta findings and critic will appear after an authorized assessment.':'No final dimension assessment completed. Numerical comparisons remain available below; this is not a completed Meta review.'}</p>}
    </section>
    <section className="panel"><h2>{r.local_preview?"Evidence for this local preview":"Decision evidence — what supports each finding?"}</h2><p className="small">Input values, comparison conditions and calculation receipts support these findings; they are not proof of a physical diagnosis. Input authenticity, narrative entailment and optimal next-test usefulness are not automatically certified.</p>
      {(r.decision_evidence||[]).map(d=><details key={d.dimension} id={'decision-'+d.dimension}><summary>{d.dimension.replaceAll('_',' ')} — {assessmentLabel(d.model_status)}</summary><p>{d.model_finding}</p>{d.model_basis&&<Detail label='Why'>{d.model_basis}</Detail>}
        <h3>Exact inputs cited by Meta</h3><ReadableEvidence value={d.inputs}/>
        <h3>Numerical evidence</h3>{Object.entries(d.metrics).map(([key,m])=><div key={key}><Detail label={m.label}>{m.value==null?'Not available':`${fmt(m.value)} ${m.unit}`}</Detail><p className="small">{m.formula} · inputs: {m.input_fields.join(', ')} · independent implementation: {m.independent_check.passed?'agrees':'needs review'}</p></div>)}
        <h3>Sources and actual tool receipts</h3>{d.references.map(ref=><div key={ref.id}>{ref.source ? <><a href={ref.source.url} target="_blank" rel="noopener noreferrer">Open source ↗</a><p className="small">{ref.source.locator}</p><p className="small">{ref.source.fact}</p>{ref.source.applicability&&<p className="small">Applicability: {ref.source.applicability}</p>}</> : <p className='small'>{ref.tool?`Calculated with ${ref.tool.replaceAll('_',' ')}`:'Submitted measurement record'}. Complete receipt retained in the downloadable audit.</p>}</div>)}
        <Detail label="Improvement / next evidence">{d.improvement_or_next_evidence}</Detail><p className="small">{d.verification_scope}</p>
      </details>)}
    </section>
  </>;
}
function EvidenceLibrary({library}) {
  if(!library)return <section className="panel"><h2>Reference evidence library</h2><p>Loading the reviewed local library…</p></section>;
  const profile=library.official_profile,observations=library.published_observations;
  return <section className="panel"><h2>Reference evidence library</h2><p>Versioned published observations and official requirements stored locally. These are comparison references, not ground truth for the condition of a new reactor.</p><p className="small">Storage: {library.storage} · version: <span>{library.version}</span>. Reading this library spends no Meta credits.</p>
    <h3>NASA requirements context</h3><p>{profile.title}</p><div className="table-scroll"><table><thead><tr><th>Clause</th><th>Reference value</th><th>Meaning / scope</th></tr></thead><tbody>{profile.criteria.map(c=><tr key={c.id}><td>{c.id}</td><td>{c.value} {c.unit}</td><td>{c.kind.replaceAll('_',' ')}<small>{c.basis}</small></td></tr>)}</tbody></table></div><p className="small">{profile.scope}</p>
    <h3>Published laboratory observations</h3><p className="small">{observations.scope}</p><div className="table-scroll"><table><thead><tr><th>Electrolysis / hot exposure</th><th>Collected oxygen</th><th>Resistance endpoints</th><th>Wall recession / printed bound</th></tr></thead><tbody>{observations.cases.map(c=><tr key={c.id}><td>{c.duration_h} / {c.thermal_exposure_h} h</td><td>{c.collected_o2_g} g</td><td>{c.initial_resistance_ohm} → {c.final_resistance_ohm} Ω</td><td>{c.wall_loss_um} ± {c.wall_loss_printed_bound_um} µm<small>{c.locator}</small></td></tr>)}</tbody></table></div>
    <h3>Source records and applicability</h3>{library.sources.map(source=><details key={source.id}><summary>{source.title}</summary><a href={source.url} target="_blank" rel="noopener noreferrer">Open primary source ↗</a><p>{source.locator}</p><p>{source.fact}</p><p className="small">{source.applicability}</p></details>)}
  </section>;
}
function Plan({value}) {
  if (!value) return <p className="small">This stage did not complete.</p>;
  const next = value.next_test;
  return <><h3>{value.summary}</h3><span className="pill">{value.judgement.replaceAll('_',' ')}</span><h3>Proposed next evidence request</h3><p className="small">A draft starting point, not a validated priority ranking or proven best test.</p><p>{next.question}</p><p className="small">{next.measurement_or_record}</p><Detail label="Why this request / alternative trade-off">{next.reason}</Detail><Detail label="Evidence needed before interpreting the outcome">{next.prerequisites}</Detail>
    <details><summary>Explanations, prerequisites and limits</summary>
      {value.hypotheses.map((h,i) => <div key={i}><h3>{h.explanation}</h3><Detail label="Observation that could distinguish it">{h.discriminating_observation}</Detail><Detail label="Unresolved limit">{h.unresolved_limit}</Detail></div>)}
      <Detail label="Possible rival outcomes — not observed">{next.rival_outcomes}</Detail><Detail label="Prerequisites">{next.prerequisites}</Detail><Detail label="Why this draft choice">{next.reason}</Detail>
      {value.findings.map((f,i) => <Detail key={i} label={f.kind.replaceAll('_',' ')}>{f.text}{f.basis&&<small>Why: {f.basis}</small>}</Detail>)}{value.limitations.map((s,i) => <p className="small" key={i}>{s}</p>)}
      {value.assessments?.map(a=><Detail key={a.dimension} label={`${a.dimension}: ${assessmentLabel(a.status)}`}>{a.finding}{a.basis&&<small>Why: {a.basis}</small>} — {a.improvement_or_next_evidence}</Detail>)}
    </details></>;
}
function Results({value, busy, onReview, token, job, canBuild, onRefresh}) {
  const r = value.report, a = r.accounting;
  const [resultTab,setResultTab]=useState('summary'),[reviewTab,setReviewTab]=useState('final');
  const resultTabs=[['summary','Summary'],['measurements','Measurements'],['reviews','Review & critic'],['evidence','Evidence'],['hypotheses','Hypotheses & 3D'],['approval','Researcher review']];
  const [reviewer, setReviewer] = useState(''), [comment, setComment] = useState(''), [reviewState, setReviewState] = useState('accepted_draft');
  const ratio = a.apparent_collected_to_charge_ratio;
  const max = Math.max(a.ideal_o2_g, a.reported_collected_o2_g || 0);
  return <section id="results-panel"><div className="section-head"><div><span className="eyebrow">YOUR REVIEW</span><h2>{r.input.experiment_name}</h2><p>{r.status !== 'completed' ? 'Investigation incomplete; partial evidence retained.' : r.effective_review_status === 'evidence_needed' ? 'More evidence is needed before a physical interpretation.' : 'Records identified for engineer review.'}</p></div><div className="actions"><a className="button secondary" href={`/api/assessment-export?id=${r.id}&format=html`} target="_blank" rel="noopener noreferrer">Export report</a><a href={`/api/assessment-export?id=${r.id}&format=json`} download={`mre-${r.id}.json`}>JSON</a></div></div>
    <p className="input-origin">{r.execution_mode==='live-api'?'Live Meta run':'Recorded/test run'} · {r.api_attempts ?? 0} API requests · First review: {r.original_review?'received':'not completed'} · Critic: {r.critique?'received':'not completed'} · Final: {r.final_review?'received':'not completed'}. Opening this saved result makes no new request.</p>
    {r.error && <p className="message">{r.error}</p>}<FormTabs id="result" items={resultTabs} selected={resultTab} onSelect={setResultTab}/><div id="result-panel-summary" role="tabpanel" aria-labelledby="result-tab-summary" hidden={resultTab!=='summary'}>
    <div className="metrics">{[['Ideal four-electron oxygen',a.ideal_o2_g,'g'],['Reported collected oxygen',a.reported_collected_o2_g,'g'],['Reported collected / ideal',ratio == null ? null : ratio * 100,'%']].map(([label,v,unit]) => <div className="metric" key={label}><small>{label}</small><strong>{v == null ? 'Not available' : `${fmt(v)} ${unit}`}</strong></div>)}</div>
    <p className="small">{a.basis}. The ratio is conditional accounting, not validated efficiency or a reactor health score.</p>
    {a.reported_collected_o2_g != null && [['Ideal O₂',a.ideal_o2_g],['Reported collected O₂',a.reported_collected_o2_g]].map(([label,v]) => <div className="bar-row" key={label}><span>{label}</span><div className="bar-track"><div className="bar-fill" style={{width: `${max > 0 ? v / max * 100 : 0}%`}}/></div><span>{fmt(v)} g</span></div>)}
    {a.ratio_above_one && <p className="message">Reported collected oxygen exceeds the declared ideal charge budget. Check windows, units, calibration and charge assumptions; the ratio has not been clipped.</p>}
    {r.final_review&&<article className='panel'><h3>Final explanation</h3><p>{r.final_review.summary}</p><h3>Next evidence request</h3><p>{r.final_review.next_test.question}</p><p className='small'>{r.final_review.next_test.measurement_or_record}</p></article>}</div>
    <div id='result-panel-measurements' role='tabpanel' aria-labelledby='result-tab-measurements' hidden={resultTab!=='measurements'}>{resultTab==='measurements'&&<PerformanceResults report={r}/>}</div>
    <div id='result-panel-hypotheses' role='tabpanel' aria-labelledby='result-tab-hypotheses' hidden={resultTab!=='hypotheses'}>{resultTab==='hypotheses'&&<HypothesisLayer report={r} token={token} job={job} busy={busy} canBuild={canBuild} onRefresh={onRefresh}/>}</div>
    <div id='result-panel-evidence' role='tabpanel' aria-labelledby='result-tab-evidence' hidden={resultTab!=='evidence'}><article className="panel"><h3>What evidence is still needed?</h3>{r.readiness.gaps.length ? r.readiness.gaps.map(g => <p key={g.id} className="gap">{g.message}</p>) : <p className="small">Required record locations are identified by the user. Authenticity and measurement quality still require review.</p>}</article>
    </div><div id="result-panel-reviews" role="tabpanel" aria-labelledby="result-tab-reviews" hidden={resultTab!=='reviews'}><FormTabs id='review-detail' items={[['original','First review'],['critic','Critic'],['final','Final review']]} selected={reviewTab} onSelect={setReviewTab}/><div className="review-switch"><article className="panel" hidden={reviewTab!=='original'}><span className="eyebrow">FIRST REVIEW</span><Plan value={r.original_review}/></article><article className="panel" hidden={reviewTab!=='final'}><span className="eyebrow">AFTER THE CRITIC</span><Plan value={r.final_review}/></article></div>
    <article className="panel" hidden={reviewTab!=='critic'}><h3>What did the critic question?</h3>{r.critique ? <><p>{r.critique.weakness}</p>{(r.critic_evidence || []).map((c,i)=><article key={i} className='panel'><span className='eyebrow'>{c.dimension.replaceAll('_',' ')} · {c.position.replaceAll('_',' ')}</span><p>{c.comment}</p><Detail label='Why / supporting basis'>{c.basis}</Detail><EvidenceRefs refs={c.references.map(ref=>ref.id)} report={r}/><details><summary>Measurements supporting this comment</summary><ReadableEvidence value={c.inputs}/>{Object.values(c.metrics).map((m,i)=><Detail key={i} label={m.label}>{fmt(m.value)} {m.unit}</Detail>)}</details></article>)}<Detail label="Rival explanation">{r.critique.rival_explanation}</Detail><Detail label="Requested revision">{r.critique.requested_revision}</Detail></> : <p className="small">Critic stage did not complete.</p>}<p className="small">{r.changed_fields.length ? `Changed fields: ${r.changed_fields.join(', ')}. A changed answer is not automatically better.` : 'No change recorded. A correct original review can be retained.'}</p></article>
    </div><div hidden={resultTab!=='evidence'}><details className="panel"><summary>Diagnostic options and your constraints</summary><div className="table-scroll"><table><thead><tr><th>Review option</th><th>Missing prerequisites</th><th>Entered hours / USD</th><th>Fits time / budget</th></tr></thead><tbody>{r.diagnostic_options.map(c => <tr key={c.id}><td>{c.label}</td><td>{c.missing_prerequisites.join(', ') || 'None identified'}</td><td>{c.estimated_hours ?? 'Unknown'} / {c.estimated_cost_usd ?? 'Unknown'}</td><td>{fit(c.fits_time)} / {fit(c.fits_budget)}</td></tr>)}</tbody></table></div><p className="small">Transparent prerequisite/resource comparison. Diagnostic usefulness and the model’s selection are not independently validated.</p></details>
    <details className="panel"><summary>Inspect inputs, sources, tools and numerical verification</summary>
      <Detail label="Independent numerical check">{Object.values(a.independent_checks).every(c => c.passed) ? 'Algorithms agree within declared tolerances' : 'Needs review'}</Detail>
      <Detail label="Charge">{fmt(a.charge_C)} C</Detail><Detail label="Cell electrical energy">{a.electrical_energy_Wh == null ? 'Not supplied' : `${fmt(a.electrical_energy_Wh)} Wh; furnace and auxiliary energy excluded`}</Detail>
      <Detail label="Represented oxygen inventory">{a.inventory ? `${fmt(a.inventory.represented_oxygen_g)} g; not recoverable yield` : 'Not calculated: compatible composition and batch mass both required'}</Detail>
      <Detail label="Sensitivity">{a.sensitivity ? <ReadableEvidence value={a.sensitivity}/> : 'Full sensitivity not calculated; missing bounds remain unknown'}</Detail>
      <Detail label="Ground truth for this new input">{r.validation.engineering_ground_truth}</Detail><Detail label="Trace integrity">{value.trace_integrity}</Detail><Detail label="Workflow version">{value.current_code_matches ? 'Matches current implementation' : 'Recorded under an earlier implementation'}</Detail>
      <Detail label="Requests / estimated settled cost">{r.api_attempts} / ${fmt(r.settled_estimated_cost_usd)}</Detail><Detail label="Software workflow duration">{fmt(r.workflow_seconds)} s; not researcher time savings</Detail>
      {r.sources.map(s => <div key={s.id}><a href={s.url} target="_blank" rel="noopener noreferrer">{s.id} ↗</a><p className="small">{s.locator}</p><p className="small">{s.fact}</p></div>)}
      <p className="small">Complete inputs, tool receipts and event trace are retained in the JSON download. They are not shown as code in this review.</p>
    </details>
    </div><div id="result-panel-approval" role="tabpanel" aria-labelledby="result-tab-approval" hidden={resultTab!=='approval'}><article className="panel"><h3>Researcher review</h3><p className="small">Review the draft. This does not authorize reactor operation.</p>{r.status === 'completed' && value.review.state === 'awaiting_review' ? <form onSubmit={e => {e.preventDefault();onReview(r.id,reviewState,reviewer,comment);}}><div className="fields"><label>Your name<input value={reviewer} onChange={e => setReviewer(e.target.value)} maxLength={100} required/></label><label>Decision<select value={reviewState} onChange={e => setReviewState(e.target.value)}><option value="accepted_draft">Accept draft</option><option value="changes_requested">Request changes</option><option value="rejected_draft">Reject draft</option></select></label><label className="wide">Reason or requested edit<textarea value={comment} onChange={e => setComment(e.target.value)} maxLength={1500} required/></label></div><button disabled={busy} className="button secondary">Save researcher review</button></form> : value.review.state !== 'awaiting_review' ? <><Detail label="Recorded decision">{value.review.state.replaceAll('_',' ')}</Detail><Detail label="Reviewer">{value.review.reviewer}</Detail><p>{value.review.comment}</p></> : <p className="small">Finish an assessment before recording a review.</p>}</article>
  </div></section>;
}

export default function App() {
  const [workspace,setWorkspace] = useState(null), [form,setForm] = useState(toForm), [tab,setTab] = useState('manual'), [view,setView] = useState('input');
  const [setupStep,setSetupStep]=useState('experiment'),[measurementTab,setMeasurementTab]=useState('electrical'),[customTargets,setCustomTargets]=useState(false);
  const [consent,setConsent] = useState(false), [notice,setNotice] = useState(''), [error,setError] = useState(false), [saved,setSaved] = useState(null), [pending,setPending] = useState(false);
  const [connectionError,setConnectionError]=useState(''),[draftBlocked,setDraftBlocked]=useState(false);
  const [selectedId,setSelectedId]=useState(null),[library,setLibrary]=useState(null),[draftStatus,setDraftStatus]=useState('Connecting to saved workspace…'),[draftConflict,setDraftConflict]=useState(false),[saveEpoch,setSaveEpoch]=useState(0);
  const [hydrationReady,setHydrationReady]=useState(false);
  const hydrated=useRef(false),revision=useRef(0),lastSaved=useRef(''),savingDraft=useRef(false),latestDraft=useRef(null);
  const [origin,setOrigin] = useState(null), [contract,setContract] = useState(null), lastJob = useRef('');
  const message = useCallback((text, failed = false) => {setNotice(text);setError(failed);},[]);
  const refresh = useCallback(async () => {
    try {setWorkspace(await get('/api/experiment-workspace'));setConnectionError('');setDraftBlocked(false);} catch (e) {setConnectionError(e.message);}
  },[message]);
  const showAssessment = useCallback(async (id,restoreInputs=false) => {
    try {const value = await get('/api/assessment?id='+encodeURIComponent(id)); if (!value.report) throw new Error(value.reason || 'Saved assessment is missing or its integrity check failed; do not repeat paid work.'); setSaved(value);setSelectedId(id);if(restoreInputs){setCustomTargets(false);setSetupStep('experiment');setForm(toForm(value.report.input));setOrigin({label:'Restored saved experiment inputs. Editing creates a new input record; the saved review remains unchanged.'});}setView('input');setSetupStep('review');message('Saved result loaded. Opening it does not start another Meta request.');}
    catch (e) {message(e.message,true);}
  },[message]);
  useEffect(()=>{
    refresh();const onFocus=()=>refresh();window.addEventListener('focus',onFocus);
    const timer=setInterval(()=>{if(document.visibilityState==='visible')refresh();},30000);
    return()=>{window.removeEventListener('focus',onFocus);clearInterval(timer);};
  },[refresh]);
  useEffect(()=>{
    if(!workspace?.csrf)return;
    get('/api/performance-contract').then(setContract).catch(e=>message(e.message,true));
    get('/api/evidence-library').then(setLibrary).catch(e=>message(e.message,true));
  },[workspace?.csrf,message]);
  useEffect(()=>{
    if(!workspace || hydrated.current)return;
    hydrated.current=true;revision.current=workspace.draft?.revision || 0;
    const selected=chooseDraft(workspace.draft || {revision:0,draft:null},readBackup(browserStorage(),workspace.workspace_id));
    const state=selected.draft;
    if(state){setForm({...toForm(),...state.form,trace:[],resistance_trace:[],current_trace_text:state.form.current_trace_text ?? formatCurrentTrace(state.form.trace || [])});setOrigin(state.origin || null);setTab('manual');setView(state.view || 'input');setSelectedId(state.selected_assessment_id || null);lastSaved.current=selected.from==='browser backup'?'':JSON.stringify(state);}
    setHydrationReady(true);setDraftConflict(selected.conflict);setDraftStatus(!workspace.persistence?'Restart the updated backend once to enable persistent drafts. Existing saved reviews remain on disk.':selected.conflict?'Another tab has a newer saved draft. Browser backup retained.':state?`Restored from ${selected.from}.`:'Draft changes will be saved automatically.');
    // A previous completed job is history, never an instruction to run it again.
    if(workspace.job?.state!=='running')lastJob.current=JSON.stringify(workspace.job);
    const id=state?.selected_assessment_id || null;
    // Restore the draft without automatically displaying a prior result.
    // Saved reviews remain accessible explicitly from Saved reviews.
  },[workspace,showAssessment]);
  useEffect(()=>{
    if(!hydrationReady || !hydrated.current || !workspace?.csrf || draftConflict || draftBlocked || !workspace.persistence || workspace.persistence_error)return;
    const snapshot={form,origin,tab,view,selected_assessment_id:selectedId};const serial=JSON.stringify(snapshot);latestDraft.current={snapshot,serial};
    if(serial===lastSaved.current)return;
    const backedUp=writeBackup(browserStorage(),workspace.workspace_id,snapshot,revision.current,true);
    setDraftStatus(backedUp?'Changes backed up in this browser; saving workspace…':'Saving workspace… Browser backup is unavailable.');
    const timer=setTimeout(async()=>{
      if(savingDraft.current)return;
      savingDraft.current=true;
      try {const saved=await saveDraft(workspace.csrf,snapshot,revision.current);revision.current=saved.revision;lastSaved.current=serial;const latest=latestDraft.current;writeBackup(browserStorage(),workspace.workspace_id,latest?.snapshot || snapshot,saved.revision,latest?.serial!==serial);setDraftStatus('Draft saved to this workspace. Reopening does not repeat API calls.');}
      catch(e){if(!e.status || e.status===403 || e.status>=500)setDraftBlocked(true);else setDraftConflict(true);setDraftStatus(e.message);}
      finally{savingDraft.current=false;setSaveEpoch(v=>v+1);}
    },700);
    return()=>clearTimeout(timer);
  },[hydrationReady,form,origin,tab,view,selectedId,workspace?.csrf,workspace?.workspace_id,draftConflict,draftBlocked,saveEpoch]);
  async function reloadSavedDraft(){writeBackup(browserStorage(),workspace.workspace_id,{form:toForm(),origin:null,tab:'manual',view:'input',selected_assessment_id:null},revision.current,false);setHydrationReady(false);hydrated.current=false;setDraftConflict(false);await refresh();}
  useEffect(() => {
    if (workspace?.job?.state !== 'running') return;
    const timer = setTimeout(refresh,1200); return () => clearTimeout(timer);
  },[workspace,refresh]);
  useEffect(() => {
    const job = workspace?.job; if (!job) return;
    const signature = JSON.stringify(job); if (signature === lastJob.current) return; lastJob.current = signature;
    if (job?.state === 'failed') message(job.error,true);
    if (job.state !== 'completed') return;
    if(job.action==='acknowledge_unknown_cost'){message('Unknown cost accepted; reservation retained. You can now start an assessment if no other blocker remains.');return;}
    if(job.action==='reactor_hypotheses'){message(job.result?.status==='completed'?'Hypothesis version saved. Your assessment and critic are unchanged.':job.result?.error,job.result?.status!=='completed');return;}
    const result = job.result;
    if (job.action === 'import_excel' && result?.input) {setForm(toForm(result.input));setOrigin({import_id:result.import_id,label:`Imported ${result.filename}. Review the fields; edits will be recorded.`});message('Excel imported locally. No Meta call was made.');}
    if (['assess','review_assessment'].includes(job.action) && result?.assessment_id) {showAssessment(result.assessment_id);message(job.action === 'review_assessment' ? 'Researcher review saved.' : result.status === 'completed' ? 'Assessment saved. Review the findings below.' : `Assessment stopped: ${result.error}`,result.status === 'failed');}
  },[workspace,message,showAssessment]);
  const job = workspace?.job, busy = pending || job?.state === 'running';
  const backendCompatible=Boolean(workspace?.persistence && contract?.version==='mre-performance-v5');
  const budget = workspace?.budget, blocked = Boolean(budget?.blocking_unresolved_requests?.length);
  const recoverableBilling = budget?.recoverable_unknown_cost_requests || [];
  const activeReservations = budget?.active_reserved_requests || [];
  const budgetLow = budget && budget.accounted_or_reserved_usd + 1.25 > budget.local_limit_usd;
  async function submitAction(data) {
    setPending(true);
    try {await action(workspace.csrf,data);await refresh();return true;}
    catch (e) {message(e.message,true);return false;} finally {setPending(false);}
  }
  let currentInput=null,inputError='';
  try {if(contract)currentInput=payload(form,contract,{customTargets});} catch(e){inputError=e.message;}
  const currentSerial=currentInput ? JSON.stringify(currentInput):'';
  useEffect(()=>{setConsent(false);},[currentSerial]);
  async function assess(event) {
    event.preventDefault(); if (busy || !consent || !backendCompatible || workspace?.persistence_error) return;
    try {const data = payload(form,contract,{customTargets});message('Validating your input…');const ok = await submitAction({action:'assess',input:data,consent:true,import_id:origin?.import_id,example_id:origin?.example_id});if (ok) {message('Assessment started. Follow the live steps below; no need to click Assess again.');setConsent(false);setSaved(null);setSelectedId(null);}}
    catch (e) {message(e.message,true);}
  }
  async function example() {
    try {setSetupStep('experiment');setCustomTargets(false);setConsent(false);const data = await get('/api/experiment-example');setForm(toForm(data.input));setOrigin({example_id:data.example_id,label:'Published Yu et al. one-hour example, not a new lab experiment. Edits are recorded.'});setTab('manual');message('Published example loaded. Review it before authorizing assessment.');}
    catch (e) {message(e.message,true);}
  }
  function newExperiment() {
    if (busy) {message('Stop or finish the active assessment first.',true);return;}
    setSetupStep('experiment');setMeasurementTab('electrical');setCustomTargets(false);setForm(toForm());setOrigin(null);setSaved(null);setSelectedId(null);setConsent(false);setView('input');setTab('manual');message('');
  }
  const setupSteps=[['experiment','Experiment'],['measurements','Measurements'],['comparison','Reference data'],['review','Review & assess']];
  const stepIndex=setupSteps.findIndex(([id])=>id===setupStep);
  const measurementTabs=[['electrical','Electrical'],['gas','Oxygen & energy'],['materials','Materials'],['endurance','Endurance'],['environment','Environment'],['evidence','Records & inventory'],...(form.comparison_profile==='nasa_leia_2026_topic2'?[['system','Integrated system']]:[]),...(customTargets?[['targets','My design requirements']]:[])];
  useEffect(()=>{if((measurementTab==='system'&&form.comparison_profile!=='nasa_leia_2026_topic2')||(measurementTab==='targets'&&!customTargets))setMeasurementTab('electrical');},[measurementTab,form.comparison_profile,customTargets]);
  const field = (name,label,props = {}) => <Field key={name} form={form} setForm={setForm} name={name} label={label} {...props}/>;
  const done = new Set(job?.action==='assess' && job.state==='running' ? (job.progress?.completed_steps||[]) : (saved?.events||[]).map(e=>e.kind));
  if (saved?.events) saved.events.forEach(e => done.add(e.kind));
  return <><a className="skip" href="#main">Skip to experiment</a><div className="sky" aria-hidden="true"/>
    <header><a className="brand" href="/"><span className="moon" aria-hidden="true"/><span>MRE <small>MISSION ENGINEER</small></span></a><nav><button className={`nav ${view === 'input' ? 'active' : ''}`} onClick={newExperiment}>New experiment</button><button className={`nav ${view === 'history' ? 'active' : ''}`} onClick={() => setView('history')}>Saved reviews</button><a href="/validation" className="nav" target="_blank" rel="noopener noreferrer">Validation &amp; methods ↗</a></nav><span className="local">LOCAL WORKSPACE</span></header>
    <main id="main"><section className="intro"><span className="eyebrow">LUNAR OXYGEN · GROUND-TEST REVIEW</span><h1>What does your experiment support?</h1><p>Enter your test record. Let Meta choose checks, question the interpretation, and draft the next evidence request.</p></section>
      {connectionError&&<p className='message'>{connectionError} <button className='text-button' onClick={refresh}>Reconnect without rerunning</button></p>}{workspace?.warnings?.map(w=><p key={w} className='message'>{w}</p>)}<p className='draft-status' role='status'>{draftStatus} {saved&&<a href='#results-panel'>View saved result ↓</a>} {draftConflict&&<button className='text-button' onClick={reloadSavedDraft}>Reload saved draft</button>}</p>
      {view === 'references' ? <EvidenceLibrary library={library}/> : view === 'history' ? <section className="panel"><h2>Saved reviews</h2>{!workspace?.assessments?.length && <p>No input-driven reviews yet.</p>}{workspace?.assessments?.map(r => <button className="history-button" key={r.id} onClick={() => showAssessment(r.id)}>{r.name}<small>{r.status} · {new Date(r.created_at).toLocaleString()}</small></button>)}</section> : <>
      <section className="panel"><div className="section-head"><h2>Experiment workspace</h2><button className="text-button" onClick={example} disabled={busy}>Load published example</button></div>
        <p className='small'>* Required to start: experiment name, duration and either constant current or a current history. Additional measurements unlock the corresponding assessment.</p>
        <FormTabs id='setup' items={setupSteps} selected={setupStep} onSelect={setSetupStep}/>
        <form onSubmit={assess} noValidate>
          {origin&&<p className='input-origin'>{origin.label}</p>}
          <fieldset disabled={busy}>
          <section id='setup-panel-experiment' role='tabpanel' aria-labelledby='setup-tab-experiment' hidden={setupStep!=='experiment'}>
            <div className='fields'>
              {field('experiment_name','Experiment name',{required:true,wide:true})}
              {field('question','What should the review answer?',{wide:true,textarea:true,help:'Optional. Leave blank for a standard evidence and performance review.'})}
              {field('duration_h','Electrolysis duration',{number:true,unit:'h',required:true})}
              {field('current_A','Constant current',{number:true,unit:'A',required:!form.current_trace_text?.trim(),disabled:Boolean(form.current_trace_text?.trim()),help:'Use the measured history below instead when current varies.'})}
              {field('collected_o2_g','Collected oxygen',{number:true,unit:'g',help:'Needed for oxygen rate, collected/ideal ratio and specific energy. Leave blank if not measured.'})}
              {field('time_alignment','Oxygen / electrical measurement windows',{choices:[['unknown','Not confirmed'],['reported_same_interval','Same interval'],['different_interval','Different intervals']],help:'Select the actual relationship; the software cannot infer matching windows.'})}
            </div>
            <details><summary>Use measured current / voltage history instead</summary>{field('current_trace_text','Current and voltage samples',{wide:true,textarea:true,help:'time_s,current_A,voltage_V,optional record per line. Start at 0; end at duration in seconds. Leave every voltage blank if unavailable.'})}{form.current_trace_text?.trim()&&<button type='button' className='text-button' onClick={()=>setForm(p=>({...p,current_trace_text:'',trace:[]}))}>Clear history and use constant current</button>}</details>
            <h3>Reactor context for matching research</h3><p className='small'>Configuration, feedstock and temperature are needed for a condition-matched publication comparison. Unknown values remain unknown.</p><div className='fields'>
              {field('configuration','Configuration',{choices:[['unknown','Not specified'],['hollow_ysz_pt','Inverted YSZ/Pt hollow anode'],['other_mre','Other MRE configuration']]})}
              {field('feedstock','Feedstock / simulant')}{field('temperature_C','Operating temperature',{number:true,unit:'°C'})}
              {field('anode_material','Anode / current collector')}{field('cathode_material','Cathode')}
            </div>
            <ComparisonOptions form={form} setForm={setForm} customTargets={customTargets} setCustomTargets={setCustomTargets}/>
          </section>
          <section id='setup-panel-measurements' role='tabpanel' aria-labelledby='setup-tab-measurements' hidden={setupStep!=='measurements'}>
            <p className='small'>Add only measurements you have. These are your experiment inputs; published reference values are already stored.</p>
            <FormTabs id='measurement' items={measurementTabs} selected={measurementTab} onSelect={setMeasurementTab}/>
            {measurementTabs.map(([key,label])=><section key={key} id={`measurement-panel-${key}`} role='tabpanel' aria-labelledby={`measurement-tab-${key}`} hidden={measurementTab!==key}>
              {key==='electrical'&&<>{field('voltage_V','Cell voltage',{number:true,unit:'V',disabled:Boolean(form.current_trace_text?.trim()),help:'Optional; cell electrical energy only, excluding furnace and auxiliaries.'})}<ParameterGroup group='electrical' contract={contract} form={form} setForm={setForm} advanced={customTargets}/></>}
              {key==='gas'&&<><ParameterGroup group='production' contract={contract} form={form} setForm={setForm}/><ParameterGroup group='energy' contract={contract} form={form} setForm={setForm} advanced={customTargets}/></>}
              {['materials','endurance','environment','system','targets'].includes(key)&&<ParameterGroup group={key} contract={contract} form={form} setForm={setForm} advanced={customTargets}/>}
              {key==='evidence'&&<><h3>Measurement quality and records</h3><p className='small'>These identify your measurements, not the backend research library. Calibration is needed before interpreting collection efficiency; it is not required to calculate an ideal charge budget.</p><div className='fields'>
                {field('calibration_status','Gas calibration',{choices:[['unknown','Unknown / not supplied'],['reported_available','Documentation identified'],['not_available','Not available']]})}
                {field('calibration_reference','Calibration record — if identified')}{field('gas_measurement_method','Oxygen measurement / conversion method',{wide:true})}
                {field('records_reference','Your run / notebook reference — optional',{wide:true})}{field('observations','Observed changes — optional',{wide:true,textarea:true})}{field('source_label','Input origin / source label — optional',{wide:true})}
              </div><details><summary>Measurement uncertainty — optional</summary><div className='fields'>
                {field('current_uncertainty_A','Current absolute ± bound',{number:true,unit:'A',disabled:Boolean(form.current_trace_text?.trim())})}{field('duration_uncertainty_s','Duration absolute ± bound',{number:true,unit:'s',disabled:Boolean(form.current_trace_text?.trim())})}{field('oxygen_uncertainty_g','Oxygen absolute ± bound',{number:true,unit:'g'})}
              </div><p className='small'>Unknown is not zero. Scalar current/time bounds are not supported for histories in this version.</p></details>
              <details><summary>Composition / feedstock inventory — optional</summary><p className='small'>Only needed for stoichiometric inventory. A measured batch is different from regolith processed in a system-output window.</p><div className='fields'>
                {field('sample_mass_g','Batch mass',{number:true,unit:'g'})}{field('analysis_id','Composition analysis ID')}{field('composition_source','Composition source',{wide:true})}{field('composition_text','Reported oxides',{wide:true,textarea:true,unit:'wt%',help:'One oxide,wt_percent per line; one analysis. No silent normalization.'})}
              </div></details></>}
            </section>)}
          </section>
          <section id='setup-panel-comparison' role='tabpanel' aria-labelledby='setup-tab-comparison' hidden={setupStep!=='comparison'}>
            <p className='input-origin'>Read-only reference data · stored in the backend · not your experiment measurements</p><EvidenceLibrary library={library}/>
          </section>
          </fieldset>
          <div id="setup-panel-review" role="tabpanel" aria-labelledby="setup-tab-review" hidden={setupStep!=='review'} className="submit-area">
            <h3>Assess your experiment</h3><details><summary>Optional numerical scenario — separate from measured inputs</summary><ReactorLab token={workspace?.csrf} scenario={form.reactor_scenario} onScenario={scenario=>setForm(p=>({...p,reactor_scenario:scenario}))} busy={busy}/></details><p className="small">One assessment calculates metrics, checks applicable research references, and runs Meta review → critic → final explanation. No separate preview is required.</p>
            {inputError&&<p className="message">{inputError}</p>}
            {currentInput&&<details><summary>Measurements to be assessed</summary><p>{currentInput.experiment_name} · {currentInput.duration_s/3600} h · {currentInput.collected_o2_g ?? 'Unknown'} g oxygen</p><ReadableEvidence value={currentInput}/></details>}
            <p className="small">{!workspace ? 'Connecting to the local backend…' : !backendCompatible ? 'Restart the updated backend once before a new assessment. Saved reviews remain available.' : !workspace.api_key_present ? 'Set MODEL_API_KEY in the backend terminal and restart the backend.' : job?.state==='running' ? 'Assessment running · waiting for Meta. Each request allows up to 180 seconds; no automatic retry.' : activeReservations.length ? 'A request reservation is still pending. Do not start a duplicate run.' : blocked ? 'Previous request billing needs review. Inspect the local ledger.' : budgetLow ? 'Insufficient remaining local budget for another assessment.' : `Server key available · $${fmt(budget?.accounted_or_reserved_usd)} locally accounted/reserved.`}</p>
            {!busy&&recoverableBilling.length>0&&<div className="message"><strong>Previous request timed out or has unknown billing.</strong><p>No new assessment can start until you review it. Accepting below retains the full local reservation; it does not claim the request was free or settled.</p>{recoverableBilling.map(id=><p key={id}><span>Request {id.slice(0,8)}… </span><button type="button" className="button secondary" disabled={busy} onClick={()=>submitAction({action:'acknowledge_unknown_cost',request_id:id,consent:true})}>Accept unknown charge & unblock</button></p>)}</div>}
            <label className="consent"><input type="checkbox" checked={consent} disabled={busy || !contract || Boolean(inputError)} onChange={e => setConsent(e.target.checked)}/>Use Meta credits for this assessment: at most 5 requests / $1.25 local reservation, not a provider billing cap.</label>
            <div className="actions"><button className="button primary" disabled={busy || !consent || !workspace?.api_key_present || !contract || !backendCompatible || Boolean(inputError) || workspace?.persistence_error || blocked || budgetLow}>Assess with Meta ↗</button><button className="button secondary" type="button" disabled={job?.state !== 'running'} onClick={() => submitAction({action:'stop'})}>Stop before next request</button></div>
          </div>
          <div className='wizard-footer'><button className='text-button' type='button' disabled={stepIndex===0} onClick={()=>setSetupStep(setupSteps[stepIndex-1][0])}>← Back</button><span>{stepIndex+1} / {setupSteps.length}</span>{stepIndex<setupSteps.length-1&&<button className='button secondary' type='button' onClick={()=>setSetupStep(setupSteps[stepIndex+1][0])}>Continue →</button>}</div>
        </form>
        <p role="status" aria-live="polite" className={error ? 'message' : 'small'}>{notice}</p>
      </section>
      {setupStep==='review' && ((job?.action === 'assess' && job.state==='running') || saved) && <section className="panel"><div className="section-head"><h2>2. Follow the investigation</h2>{job?.state === 'running' && job.action==='assess' && <span className="tag live-badge">Live</span>}</div><ol className="steps">{stages.map(([key,label]) => <li key={key} className={done.has(key) ? 'done' : ''}>{label}</li>)}</ol><p role="status" className="small">{job?.state === 'running' && job.action==='assess' ? `${job.progress?.kind?.replaceAll('_',' ') || 'Preparing'} · ${job.progress?.api_attempts ?? 0} / 5 API requests. No automatic retries.` : job?.action==='assess' && job?.state === 'failed' ? job.error : job?.action==='assess' && job?.result?.status === 'failed' ? `Investigation stopped: ${job?.result?.error}. Partial calculations are retained; the review did not complete.` : 'Saved investigation replay — no new API calls. Inspect the findings below.'}</p></section>}
      {setupStep==='review' && saved && <Results token={workspace?.csrf} job={job} canBuild={backendCompatible && Boolean(workspace?.api_key_present) && !blocked && Boolean(budget && budget.accounted_or_reserved_usd+.25<=budget.local_limit_usd)} onRefresh={refresh} key={saved.report.id} value={saved} busy={busy} onReview={(id,state,reviewer,comment) => submitAction({action:'review_assessment',assessment_id:id,review_state:state,reviewer,comment})}/>}</>}
      <p className="footer-note">Evidence-review prototype. New experiment decisions are not ground-truth certified. <a href="/validation" target="_blank" rel="noopener noreferrer">Validation results and methods ↗</a></p>
    </main></>;
}
