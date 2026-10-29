'use strict';
let workspace = null;
let activeFilter = 'all';
const $ = id => document.getElementById(id);
const labels = {current:'Applied current',duration:'Electrolysis duration',temperature:'Operating temperature',carrier_flow:'Argon carrier flow',oxygen_mass:'Reported oxygen mass',faradaic_efficiency:'Reported Faradaic efficiency'};
const units = {A:'A',s:'s',degC:'°C',sccm:'sccm',g:'g',fraction:'fraction'};
const node = (tag,text,cls) => {
  const el = document.createElement(tag);
  if (text !== undefined) el.textContent = text;
  if (cls) el.className = cls;
  return el;
};
function safeLink(url,text) {
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== 'https:') return node('span',text);
    const a = node('a',text);
    a.href = parsed.href; a.target = '_blank'; a.rel = 'noopener noreferrer';
    return a;
  } catch { return node('span',text); }
}
function field(label,value) {
  const dl = node('dl',undefined,'detail-field');
  const dd = node('dd');
  if (value instanceof Node) dd.append(value); else dd.textContent = String(value);
  dl.append(node('dt',label),dd);
  return dl;
}
function openDetails(kind,title,fields,limit) {
  $('detail-kind').textContent = kind;
  $('detail-body').replaceChildren(node('h2',title,'detail-title'));
  fields.forEach(([label,value]) => $('detail-body').append(field(label,value)));
  if (limit) $('detail-body').append(node('p',limit,'detail-limit'));
  $('detail').showModal();
}
function evidenceDetail(item) {
  const source = workspace.sources.find(s => s.id === item.source_id);
  const fields = [['Evidence ID',item.id],['Record type',item.epistemic_status]];
  if (item.kind === 'quantity') fields.push(['Reported value',`${item.value} ${units[item.unit] || item.unit}`],['Measurement uncertainty','Unknown in this fixture; not assumed zero.']);
  else fields.push(['Author interpretation',item.text]);
  fields.push(['Source location',item.locator],['Transformation',item.transformation]);
  if (source) fields.push(['Original source',safeLink(source.url,source.title)]);
  openDetails('EVIDENCE / PROVENANCE',labels[item.field] || 'Collection interpretation',fields,'Source-linked development evidence. No new physical calculation or independent validation has been performed.');
}
function sourceDetail(source) {
  const acquisition = source.local_acquisition;
  const fields = [['Role',source.role.replaceAll('_',' ')],['Pinned record',source.version],['Format',source.format],['License / rights',source.license],['Reuse guidance',source.redistribution],['Rights evidence',safeLink(source.rights_evidence,'Review rights record ↗')],['Local acquisition',acquisition.status.replaceAll('-',' ')],['Source',safeLink(source.url,'Open original source ↗')]];
  if (acquisition.sha256) fields.push(['Local SHA-256',acquisition.sha256]);
  source.download_urls.forEach((url,i) => fields.push([`Source download ${i+1}`,safeLink(url,'Open download ↗')]));
  fields.push(['Limitations',source.limitations.join(' • ')]);
  openDetails('RESOURCE / DETAILS',source.title,fields,'Opening an external link is your action. Local registration verifies integrity, not scientific validity or redistribution permission.');
}
function renderEvidence() {
  $('evidence-list').replaceChildren();
  const items = workspace.case.evidence.filter(e => activeFilter === 'all' || e.kind === activeFilter);
  items.forEach(item => {
    const button = node('button',undefined,'evidence-row');
    button.type = 'button';
    const label = node('span',labels[item.field] || 'Oxygen collection limitation','label');
    label.append(node('small',item.kind === 'quantity' ? 'Reported · uncertainty unknown' : 'Author interpretation · source-specific'));
    const value = item.kind === 'quantity' ? `${item.value} ${units[item.unit] || item.unit}` : 'Review';
    button.append(label,node('span',value,'value'),node('span','↗','arrow'));
    button.addEventListener('click',() => evidenceDetail(item));
    $('evidence-list').append(button);
  });
}
function render() {
  $('metric-evidence').textContent = workspace.case.evidence.length;
  $('metric-gaps').textContent = workspace.case.missing_inputs.length;
  $('metric-files').textContent = `${workspace.sources.filter(s => s.local_acquisition.status === 'local-hash-matches').length} / ${workspace.sources.length}`;
  $('case-question').textContent = workspace.case.question;
  $('case-config').textContent = workspace.case.configuration;
  $('hashes').textContent = `Case SHA-256: ${workspace.case_sha256} | Manifest SHA-256: ${workspace.manifest_sha256}`;
  renderEvidence();
  $('gap-list').replaceChildren();
  workspace.case.missing_inputs.forEach(gap => {
    const card = node('article',undefined,'gap');
    card.append(node('h4',gap.description),node('p',gap.consequence));
    $('gap-list').append(card);
  });
  $('source-list').replaceChildren();
  workspace.sources.forEach(source => {
    const card = node('article',undefined,'panel source-card');
    card.append(node('span',source.role.replaceAll('_',' ').toUpperCase(),'eyebrow'),node('h3',source.title),node('p',source.format,'muted'),node('span',source.local_acquisition.status.replaceAll('-',' '),'source-state'));
    const button = node('button','Review source & rights ↗','secondary');
    button.addEventListener('click',() => sourceDetail(source));
    card.append(button); $('source-list').append(card);
  });
  renderAccounting();
  renderInvestigation();
  renderValidation();
  renderEngineering();
  renderWorkbench();
  $('export').disabled = false;
}
async function load() {
  $('refresh').disabled = true;
  $('load-status').textContent = 'Reading local evidence…';
  $('load-status').classList.remove('error');
  try {
    const response = await fetch('/api/workspace',{cache:'no-store'});
    if (!response.ok) throw new Error('Local evidence could not be loaded. Run validate-case and data-status in your terminal.');
    workspace = await response.json(); render();
    $('load-status').textContent = 'Local evidence loaded · refresh made no Meta calls';
  } catch (error) {
    workspace = null; $('export').disabled = true;
    $('wb-results').replaceChildren();$('wb-job').textContent='Workspace unavailable; no result shown.';
    ['metric-evidence','metric-gaps','metric-files'].forEach(id => $(id).textContent = '—');
    ['evidence-list','gap-list','source-list'].forEach(id => $(id).replaceChildren());
    ['case-question','case-config','hashes'].forEach(id => $(id).textContent = '');
    $('accounting-content').hidden = true;
    $('accounting-state').textContent = 'Local evidence unavailable; no accounting results shown.';
    clearInvestigation('Local evidence unavailable; no investigation shown.');
    $('validation-content').replaceChildren(node('p','Local evidence unavailable; saved results hidden.','notice'));
    $('engineering-content').replaceChildren(node('p','Local evidence unavailable; engineering reviews hidden.','notice'));
    $('load-status').classList.add('error');
    $('load-status').textContent = error.message || 'Could not read the local workspace.';
  } finally { $('refresh').disabled = false; }
}
function switchView(view) {
  document.querySelectorAll('[data-view]').forEach(button => {
    const active = button.dataset.view === view;
    button.classList.toggle('active',active); button.setAttribute('aria-pressed',String(active));
  });
  document.querySelectorAll('.view').forEach(section => {
    const active = section.id === `view-${view}`;
    section.hidden = !active; section.classList.toggle('active',active);
  });
}
document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click',() => switchView(button.dataset.view)));
document.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click',() => {
  activeFilter = button.dataset.filter;
  document.querySelectorAll('[data-filter]').forEach(b => {
    b.classList.toggle('active',b === button); b.setAttribute('aria-pressed',String(b === button));
  });
  if (workspace) renderEvidence();
}));
$('inspect').addEventListener('click',() => {
  const view = $('inspect').dataset.targetView || 'evidence';
  switchView(view);
  const heading = $(view === 'investigation' ? 'investigation-heading' : 'evidence-heading');
  heading.setAttribute('tabindex','-1'); heading.focus({preventScroll:true});
  $(`view-${view}`).scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
});
$('close-detail').addEventListener('click',() => $('detail').close());
$('refresh').addEventListener('click',load);
$('export').addEventListener('click',() => {
  if (!workspace) return;
  const exported = {exported_at:new Date().toISOString(),...workspace,workbench:workspace.workbench?{...workspace.workbench,csrf:undefined}:undefined,export_scope:'Saved evidence, accounting, recorded drafts and validation results. No certification or raw telemetry implied.'};
  const url = URL.createObjectURL(new Blob([JSON.stringify(exported,null,2)],{type:'application/json'}));
  const a = node('a'); a.href = url; a.download = 'mre-development-evidence.json';
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url),1000);
});
function formatNumber(value, digits=6) {
  return typeof value === 'number' && Number.isFinite(value) ? value.toLocaleString(undefined,{maximumSignificantDigits:digits}) : 'Unavailable';
}
function renderAccounting() {
  const data = workspace.day2 || {status:'not-run'};
  const content = $('accounting-content');
  content.hidden = true;
  if (data.status !== 'saved-accounting-available') {
    const instructions = data.status === 'not-run' ? 'Run accounting in your terminal to create the first saved report.' : (data.reason || 'Saved report requires review.');
    $('accounting-state').textContent = `${data.status.replaceAll('-',' ')} · ${instructions}`;
    return;
  }
  const report = data.report;
  const inventory = report.inventory;
  const charge = report.charge;
  const comparison = report.historical_comparison;
  $('accounting-state').textContent = `Recorded local run: ${data.run_name} · no new calculation on page load`;
  $('inventory-result').textContent = `${formatNumber(inventory.represented_oxygen_g)} g`;
  $('inventory-basis').textContent = `For a user-selected ${formatNumber(inventory.reference_batch_mass_g)} g reference mass. This is not the measured experiment batch mass.`;
  $('inventory-summary').replaceChildren(
    field('Original oxide total',`${formatNumber(inventory.oxide_total_wt_percent)} wt%`),
    field('Unrepresented composition',`${formatNumber(inventory.unrepresented_wt_percent)} wt%`),
    field('Uncertainty','Unknown; no statistical interval supplied')
  );
  $('charge-result').textContent = `${formatNumber(charge.ideal_oxygen_g)} g`;
  $('charge-summary').replaceChildren(
    field('Inputs',`${formatNumber(charge.current_a)} A × ${formatNumber(charge.duration_s)} s`),
    field('Charge',`${formatNumber(charge.charge_c)} C`),
    field('Reported collected oxygen',`${formatNumber(charge.reported_oxygen_g)} g`),
    field('Apparent oxygen-to-charge ratio',formatNumber(charge.apparent_oxygen_to_charge_ratio))
  );
  $('comparison-status').textContent = comparison.status.replaceAll('-',' ');
  $('comparison-details').textContent = comparison.status === 'not-applicable' ? comparison.scope : `Computed ratio: ${formatNumber(comparison.computed_apparent_ratio)}; paper-reported fraction: ${formatNumber(comparison.reported_efficiency_fraction)}. ${comparison.scope}`;
  $('oxide-rows').replaceChildren();
  inventory.components.forEach(component => {
    const row = node('tr');
    row.append(node('td',component.oxide),node('td',formatNumber(component.wt_percent)),node('td',formatNumber(component.represented_oxygen_g)));
    const source = workspace.sources.find(s => s.id === component.source_id);
    const cell = node('td');
    if (source) {
      const button = node('button',component.locator + ' ↗','text-button');
      button.addEventListener('click',() => sourceDetail(source)); cell.append(button);
    } else cell.textContent = component.source_id;
    row.append(cell); $('oxide-rows').append(row);
  });
  $('accounting-hash').textContent = `Created ${report.created_at} · SHA-256: ${report.report_sha256}`;
  content.hidden = false;
}
function clearInvestigation(message) {
  $('investigation-state').textContent = message;
  $('investigation-summary').hidden = true;
  $('challenge-card').hidden = true;
  $('metric-agent-requests').textContent = '0';
  $('agent-request-caption').textContent = 'No current run loaded';
  $('hero-run-status').textContent = 'Historical development case · no current run loaded';
  $('inspect').dataset.targetView = 'evidence';
  $('inspect').replaceChildren(document.createTextNode('Inspect experiment '),node('span','↗'));
  $('investigation-events').replaceChildren();
  $('investigation-evidence').textContent = 'No current tool results shown.';
  [['initial-plan-card','ORIGINAL PLAN'],['revised-plan-card','REVISED PLAN']].forEach(([id,title]) => {
    $(id).replaceChildren(node('span',title,'eyebrow'),node('h3','No current plan to display'),node('p','Start an investigation explicitly from your terminal.','muted'));
  });
}
function referenceButtons(refs, run) {
  const container = node('div');
  refs.forEach(ref => {
    const button = node('button',ref,'reference-button');
    button.addEventListener('click',() => {
      const evidence = workspace.case.evidence.find(e => e.id === ref);
      const source = workspace.sources.find(s => s.id === ref);
      const gap = workspace.case.missing_inputs.find(g => g.id === ref);
      const tool = (run.events || []).find(e => e.kind === 'tool_result' && e.data.evidence_id === ref);
      if (evidence) evidenceDetail(evidence);
      else if (source) sourceDetail(source);
      else if (gap) openDetails('RECORDED INPUT GAP',gap.description,[['Consequence',gap.consequence]],'This is a recorded absence, not a new measurement.');
      else if (tool) openDetails('RECORDED TOOL RESULT',tool.data.tool,[['Evidence ID',ref],['Arguments',JSON.stringify(tool.data.arguments)],['Result',JSON.stringify(tool.data.result,null,2)]],'Local numerical/readiness evidence, not independent science certification.');
    });
    container.append(button);
  });
  return container;
}
function renderPlan(id, title, plan, run) {
  const card = $(id);
  const test = plan.next_test;
  card.replaceChildren(node('span',title,'eyebrow'),node('h3',test.question,'plan-question'),node('p',plan.decision_status.replaceAll('_',' '),'draft-status'),field('Proposed measurement / evidence request',test.measurement),field('Why it may discriminate',test.why_discriminates));
  card.append(referenceButtons(test.evidence_refs,run));
  const prerequisites = node('ul',undefined,'plan-list');
  test.prerequisites.forEach(text => prerequisites.append(node('li',text)));
  card.append(node('h4','Prerequisites'),prerequisites);
  const details = node('details');
  details.append(node('summary','Review unconfirmed explanations and limits'));
  plan.hypotheses.forEach(h => {
    const section = node('article',undefined,'hypothesis');
    section.append(node('h4',h.label),node('p',h.explanation),field('Discriminating observation',h.discriminating_observation),referenceButtons(h.evidence_refs,run));
    details.append(section);
  });
  const limits = node('ul',undefined,'plan-list');
  plan.limitations.forEach(text => limits.append(node('li',text)));
  details.append(limits); card.append(details);
}
function renderInvestigation() {
  const run = workspace.investigation || {status:'not-run'};
  clearInvestigation(`Recorded run ${run.run_name || 'v1'} · ${run.status.replaceAll('-',' ')}`);
  const events = run.events || [];
  if(run.status === 'archived-draft-investigation') $('investigation-state').textContent += ' · Historical code version: evidence shown for review; current implementation is not verified by this old run.';
  const attempts = events.filter(e => e.kind === 'api_reserved').length;
  $('metric-agent-requests').textContent = attempts;
  $('agent-request-caption').textContent = run.status === 'completed-draft-investigation' ? 'Completed · no calls on refresh' : run.status === 'not-run' ? 'No investigation started' : 'Recorded attempts · not a live activity counter';
  $('hero-run-status').textContent = run.status === 'completed-draft-investigation' ? 'Historical development case · completed draft available' : `Historical development case · ${run.status.replaceAll('-',' ')}`;
  if (run.status !== 'not-run') {
    $('inspect').dataset.targetView = 'investigation';
    $('inspect').replaceChildren(document.createTextNode('View investigation '),node('span','↗'));
  }
  if (['not-run','needs-review','stale'].includes(run.status)) {
    if (run.status === 'not-run') $('investigation-state').textContent += ' · Use investigation-preview before explicitly starting a paid run.';
    else $('investigation-state').textContent += ' · Results suppressed; inspect inputs and saved trace before continuing.';
    return;
  }
  const initial = events.find(e => e.kind === 'initial_plan');
  const challenge = events.find(e => e.kind === 'challenge');
  $('investigation-summary').hidden = false;
  const mode = events[0]?.data?.execution_mode || 'unknown';
  $('investigation-summary').textContent = `${mode === 'live-api' ? 'Recorded Meta API run' : 'Test-double trace; not real API performance'} · ${attempts} API attempts · ${events.filter(e => e.kind === 'tool_result').length} local tools · ${run.trace_integrity}. Same-model critique and all prose require scientific review.`;
  if (initial) renderPlan('initial-plan-card','ORIGINAL DRAFT',initial.data,run);
  if (run.result) {
    renderPlan('revised-plan-card',run.result.test_card_changed ? 'REVISED DRAFT' : 'RETAINED TEST CARD',run.result.revised_plan,run);
    $('investigation-summary').textContent += ` Changed fields: ${run.result.changed_fields.join(', ') || 'none'}.`;
  }
  if (challenge) {
    const data = challenge.data;
    $('challenge-card').hidden = false;
    $('challenge-card').replaceChildren(node('span','MODEL CRITIC / NOT INDEPENDENT EXPERT REVIEW','eyebrow'),node('h3',data.weakness),field('Why this matters',data.why_it_matters),field('Rival explanation',data.alternate_explanation),field('Requested revision',data.requested_revision),referenceButtons(data.evidence_refs,run));
  }
  const failure = events.findLast(e => e.kind === 'failed' || e.kind === 'stopped');
  if (failure) $('investigation-state').textContent += ` · ${failure.data.message}`;
  events.forEach((event,index) => {
    const row = node('li');
    const content = node('div');
    content.append(node('h3',event.kind.replaceAll('_',' ').replaceAll('-',' ')));
    if (event.kind === 'tool_result') content.append(node('p',`${event.data.tool} · ${event.data.evidence_id}`));
    if (event.kind === 'api_reserved') content.append(node('p',`Request ${event.data.request_number} · $${event.data.reserved_usd.toFixed(2)} local reservation`));
    row.append(node('span',String(index).padStart(2,'0')),content,node('em',event.time.slice(11,19) + ' UTC'));
    $('investigation-events').append(row);
  });
  $('investigation-evidence').textContent = JSON.stringify(events.filter(e => e.kind === 'tool_result').map(e => e.data),null,2);
}
$('refresh-investigation').addEventListener('click',load);
function comparisonTable(summary, source=false) {
  const wrap=node('div',undefined,'table-scroll');const table=node('table',undefined,'science-table');
  const head=node('tr'); ['Method','Valid','Exact decision / all fields','Numeric / missing set'].forEach(s=>head.append(node('th',s)));
  const thead=node('thead');thead.append(head);table.append(thead);const tbody=node('tbody');
  Object.entries(summary.counts || {}).forEach(([name,c])=>{
    const n=source?c.selected:c.selected_cases;const row=node('tr');
    [name.replaceAll('_',' '),`${source?c.valid:c.valid_outputs} / ${n}`,`${source?c.all_exact:c.decision_exact} / ${n}`,`${source?c.number_exact:c.missing_set_exact} / ${n}`].forEach(v=>row.append(node('td',v)));
    tbody.append(row);
  });table.append(tbody);wrap.append(table);return wrap;
}
function renderValidation() {
  const data=workspace.validation || {};const area=$('validation-content');if(!area)return;area.replaceChildren();
  const pilot=data.pilot || {status:'not-run'};const panel=node('article',undefined,'panel');
  panel.append(node('span','PRESERVED BASELINE PILOT','eyebrow'),node('h3',pilot.status));
  if(pilot.summary){panel.append(comparisonTable(pilot.summary),field('Paired corrections / regressions',JSON.stringify(pilot.summary.paired)),node('p','Six dependent development cases. Readiness labels only; no automatic next-test utility score.','tiny'));}
  area.append(panel);
  const release=data.release_audit || {status:'not-run'};const gate=node('article',undefined,'panel accounting-check');
  gate.append(node('span','DETERMINISTIC RELEASE POLICY','eyebrow'),node('h3',release.status));
  if(release.report){gate.append(field('Decisions corrected by code',release.report.code_corrected_decisions),node('p',release.report.scope,'tiny'));
    const details=node('details');details.append(node('summary','Inspect raw versus effective decisions'));const pre=node('pre',JSON.stringify(release.report.rows,null,2),'json-view');details.append(pre);gate.append(details);}
  else gate.append(node('p','Run release-audit in the terminal. It preserves raw model scores.','muted'));area.append(gate);
  const run=data.source_benchmark || {status:'not-run'};const source=node('article',undefined,'panel accounting-check');
  source.append(node('span','PUBLISHED EVIDENCE / NEW COMPARISON','eyebrow'),node('h3',run.status));
  (run.annotations||[]).forEach(note=>source.append(node('p',note.message,'callout')));
  if(run.status==='archived-source-pilot') source.append(node('p','Historical dataset/code version. Raw recorded scores are retained; they do not validate the current benchmark.','tiny'));
  if(run.report){
    source.append(comparisonTable(run.report.summary,true),field('Recorded API attempts',run.report.api_attempts),field('Settled estimated cost',`$${formatNumber(run.report.settled_estimated_cost_usd)}`),node('p',run.report.summary.scope,'tiny'));
    source.append(node('p','Constructed claims checked against public sources. Not four reactor failures; not an optimal-experiment benchmark.','tiny'));
    run.report.rows.forEach(row=>{
      const card=node('article',undefined,'source-result');card.append(node('h3',row.task_id.replaceAll('-',' ')),node('p',row.evidence.constructed_claim,'muted'),safeLink(row.evidence.source_receipt.url,row.evidence.source_receipt.locator+' ↗'));
      const steps=node('div',undefined,'validation-steps');
      [['one_pass','Original answer'],['challenge_revision','After challenge + check'],['resample_control','Equal-call control']].forEach(([method,label])=>{
        const answer=row.answers[method];const block=node('section',undefined,'validation-step');block.append(node('h4',label));
        if(answer){block.append(field('Evidence status',answer.evidence_status),field('Reference value',answer.reference_value===null?'Not requested':`${formatNumber(answer.reference_value)} ${answer.reference_unit}`),node('p',answer.explanation),field('Next evidence request (unscored)',answer.next_evidence_request));}
        else block.append(node('p','No valid answer recorded.'));steps.append(block);
      });card.append(steps);
      const events=(run.events||[]).filter(e=>e.data.task_id===row.task_id && ['critic','tool_result','failed'].includes(e.kind));
      const details=node('details');details.append(node('summary','Actual critique, local check and errors'),node('pre',JSON.stringify(events,null,2),'json-view'));card.append(details);source.append(card);
    });
  }else source.append(node('p','No saved source-grounded run available. Page refresh never starts a paid evaluation.','muted'));
  area.append(source);
}
$('export-validation').addEventListener('click',()=>{
  if(!workspace?.validation)return;const url=URL.createObjectURL(new Blob([JSON.stringify(workspace.validation,null,2)],{type:'application/json'}));
  const a=node('a');a.href=url;a.download='mre-validation-evidence.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
function renderEngineering() {
  const target=$('engineering-content');if(!target)return;target.replaceChildren();
  const saved=workspace.validation?.engineering_reviews || {status:'not-run'};
  target.append(node('p',saved.status.replaceAll('-',' '),'notice'));
  if(!saved.report){target.append(node('p','No saved two-case engineering run yet. Use engineering-preview, freeze, then the explicit paid run in your terminal.','muted'));return;}
  const report=saved.report;const summary=report.summary || {};
  if(report.components){
    target.append(node('p',report.same_frozen_implementation?'Component runs share a frozen implementation.':'Separately versioned case evidence: these results are not one fixed-implementation experiment.','callout'));
    report.components.forEach(c=>target.append(field(`Component ${c.run_name} / freeze`,c.freeze_sha256 || 'See original report')));
  }
  const overview=node('article',undefined,'panel');overview.append(node('span','RECORDED COMPARISON','eyebrow'),node('h3',`${(summary.complete_case_ids||[]).length} completed engineering evidence workflows`));
  const wrap=node('div',undefined,'table-scroll');const table=node('table',undefined,'science-table');const head=node('tr');
  ['Method','Available cases','Claim labels','Required sources','Numeric checks','Unsupported endorsements','Missed contradictions'].forEach(t=>head.append(node('th',t)));const thead=node('thead');thead.append(head);table.append(thead);const body=node('tbody');
  Object.entries(summary.methods||{}).forEach(([method,s])=>{const row=node('tr');[method.replaceAll('_',' '),`${s.available}/${s.cases}`,`${s.claims_correct}/${s.claims_total}`,`${s.reference_coverage_correct}/${s.reference_coverage_total}`,`${s.numeric_correct}/${s.numeric_total}`,s.unsupported_endorsements,`${s.missed_contradictions}/${s.reference_contradictions}`].forEach(t=>row.append(node('td',String(t))));body.append(row);});
  table.append(body);wrap.append(table);overview.append(wrap,field('Paired corrections / regressions',JSON.stringify(summary.paired)),field('Recorded API attempts',report.api_attempts),field('Settled estimated cost',`$${formatNumber(report.settled_estimated_cost_usd)}`));
  overview.append(node('p','Metrics cover the explicit claim ledger and numeric fields. Hypotheses, free-text semantics and optimal next-test utility are not automatically validated.','tiny'));target.append(overview);
  if(saved.status==='archived-engineering-reviews')target.append(node('p','Archived implementation version; raw historical results shown for review.','callout'));
  report.rows.forEach(row=>{
    const card=node('article',undefined,'panel accounting-check');card.append(node('span',row.source_group,'eyebrow'),node('h3',row.title),node('p',row.evidence.configuration,'muted'),field('Workflow',row.status));
    const check=row.independent_numeric_checks;card.append(field('Independent Decimal/Fraction checks',check?.passed?'Production arithmetic agrees with independent implementation':'Needs review'));
    const grid=node('div',undefined,'validation-steps');
    [['one_pass','Original review'],['challenge_revision','After critic + second check'],['resample_control','Equal-call control']].forEach(([method,label])=>{
      const plan=row.plans[method],score=row.scores?.[method];const block=node('section',undefined,'validation-step');block.append(node('h4',label));
      if(!plan){block.append(node('p','No valid review recorded.'));grid.append(block);return;}
      const next=plan.next_evidence_request;block.append(field('Release status',score?.release_status||'Unscored'),node('h4',next.question),field('Measurement / record',next.measurement_or_record),field('Why relevant (unscored)',next.why_relevant));
      const list=node('ul');next.prerequisites.forEach(t=>list.append(node('li',t)));block.append(list);
      const details=node('details');details.append(node('summary','Unconfirmed hypotheses and limits'));
      plan.hypotheses.forEach(h=>details.append(node('p',`${h.explanation} — ${h.status}. Distinguishing evidence: ${h.distinguishing_evidence}`)));
      plan.limitations.forEach(t=>details.append(node('p',t,'tiny')));block.append(details);grid.append(block);
    });card.append(grid);
    const revised=row.scores?.challenge_revision;
    if(revised?.available){
      const tableWrap=node('div',undefined,'table-scroll');const claims=node('table',undefined,'science-table');const tr=node('tr');['Claim','Reference status','Revised status','Source coverage'].forEach(t=>tr.append(node('th',t)));const th=node('thead');th.append(tr);claims.append(th);const tbody=node('tbody');
      revised.claim_details.forEach(c=>{const r=node('tr');const claim=row.evidence.review_claims.find(x=>x.id===c.claim_id);[`${c.claim_id}: ${claim?.text||''}`,c.expected,c.predicted,c.required_reference_blocks_present?'Required blocks cited':'Reference missing'].forEach(t=>r.append(node('td',t)));tbody.append(r);});claims.append(tbody);tableWrap.append(claims);card.append(node('h4','Structured claim audit'),tableWrap);
      const nums=node('details');nums.append(node('summary','Independent numerical references and tolerances'),node('pre',JSON.stringify({model_checks:revised.calculations,independent_tool_checks:check},null,2),'json-view'));card.append(nums);
    }
    const sources=node('details');sources.append(node('summary','Validation sources and ground truth'));
    row.evidence.sources.forEach(s=>sources.append(safeLink(s.url,`${s.id} · ${s.locator} ↗`),node('p',s.facts)));card.append(sources);
    const trace=node('details');trace.append(node('summary','Actual tool cycle and challenge'));
    trace.append(node('pre',JSON.stringify({tools:row.tools,critique:row.critique,changed_claim_labels:row.changed_claim_labels,next_request_changed:row.next_request_changed},null,2),'json-view'));card.append(trace);
    target.append(card);
  });
}
load();


let wbInitialized=false,wbPoll=null,wbLastJob='';
function selectedCases(){return (workspace?.workbench?.suite.cases||[]).filter(c=>c.split===$('wb-split').value);}
function updateCaseOptions(){
  const options=$('wb-case');options.replaceChildren();
  const all=node('option','All 6 cases — required for split completion');all.value='';options.append(all);
  selectedCases().forEach(c=>{const o=node('option',`${c.id} · ${c.title}`);o.value=c.id;options.append(o);});
  $('wb-run').value=$('wb-split').value==='development'?'dev-t12-v1':'eval-t12-v1';renderCasePreview();
}
function renderCasePreview(){
  const target=$('wb-case-preview');target.replaceChildren();const cases=selectedCases().filter(c=>!$('wb-case').value||c.id===$('wb-case').value);
  const count=cases.length;$('wb-scope').textContent=`${count} case(s) · at most ${count*7} API requests · $${(count*1.75).toFixed(2)} local reservation. No hardware action.`;
  cases.forEach(c=>{
    const d=node('details');d.append(node('summary',`${c.id} · ${c.title}`),node('p',c.question));
    c.sources.forEach(source=>{d.append(source.url?safeLink(source.url,source.locator+' ↗'):node('p',source.locator),node('p',source.facts,'tiny'));});
    d.append(field('Source family',c.source_group));if(c.lineage)d.append(field('Development lineage',c.lineage));
    d.append(field('Supplied record',JSON.stringify(c.record,null,2)),field('Numeric task',c.numeric_task?JSON.stringify(c.numeric_task):'None; output must be null / not_applicable'));target.append(d);
  });
}
function renderWorkbench(){
  const wb=workspace?.workbench;if(!wb)return;
  if(!wbInitialized){updateCaseOptions();wbInitialized=true;switchView('workbench');}
  const busy=wb.job.state==='running';
  ['wb-start','wb-check','wb-freeze-button','wb-export'].forEach(id=>$(id).disabled=busy);
  $('wb-start').disabled=busy||!wb.api_key_present||!$('wb-consent').checked;
  $('wb-stop').disabled=!busy;
  $('wb-key').textContent=wb.api_key_present?'Meta key available in server environment.':'Meta key absent: set MODEL_API_KEY in the server terminal, then restart this server. Offline checks and saved results still work.';
  $('wb-budget').textContent=`Local ledger: $${formatNumber(wb.budget.accounted_or_reserved_usd)} accounted/reserved of $${wb.budget.local_limit_usd}. ${wb.budget.blocking_unresolved_requests.length} blocking unresolved request(s).`;
  if(wb.budget.blocking_unresolved_requests.length)$('wb-start').disabled=true;
  const freezes=$('wb-freezes');freezes.replaceChildren();
  wb.suite.freezes.forEach(f=>freezes.append(field('Current freeze',`${f.name} · ${f.sha256}`)));
  const gates=$('wb-gate');gates.replaceChildren();
  if(!wb.suite.freezes.length)gates.append(node('p','T12 pending: create a freeze, then complete development and evaluation.','callout'));
  wb.suite.freezes.forEach(f=>gates.append(node('p',`${f.name}: development ${f.gate.development_complete?'complete':'pending'} · T12 execution ${f.gate.execution_complete?'complete':'pending'}. Execution completion does not guarantee correctness.`,f.gate.execution_complete?'notice':'callout')));
  gates.append(node('p',`${wb.suite.evaluation_attempts.filter(a=>a.mode==='live-api').length} recorded live evaluation starts. Preserve failed attempts in reliability reporting.`,'tiny'));
  const selector=$('wb-report-select'),selected=selector.value;selector.replaceChildren();
  wb.suite.reports.forEach(saved=>{const o=node('option',`${saved.run_name} · ${saved.report?.split||saved.status}`);o.value=saved.run_name;selector.append(o);});
  if([...selector.options].some(o=>o.value===selected))selector.value=selected;else if(selector.options.length)selector.selectedIndex=selector.options.length-1;
  renderSuiteReport();
  const sources=$('wb-validation-sources');sources.replaceChildren(node('pre',wb.suite.sources_document,'source-text'),node('pre',wb.suite.protocol,'source-text'));
  const job=wb.job;const signature=JSON.stringify(job);
  $('wb-job').textContent=busy?`Working: ${job.action} · ${job.progress?.case_id||''} · ${job.progress?.kind||'queued'} · event ${job.progress?.sequence??0}. Keep this server running.`:job.state==='failed'?`Stopped: ${job.error}`:job.state==='completed'?`Completed: ${job.result?.status}. See checks or saved report below.`:'Ready. Choose a case, then run offline checks first.';
  if(signature!==wbLastJob&&job.state==='completed'){
    if(job.action==='check'){
      const out=$('wb-check-result');out.replaceChildren(node('p',job.result.passed?'Local source-contract and independent numeric checks passed.':'Local check failed; do not start paid work.'));
      Object.entries(job.result.checks).filter(([,v])=>v.applicable).forEach(([id,v])=>out.append(field(`${id} / ${v.unit}`,`production ${v.production}; independent ${v.reference}; difference ${v.absolute_difference}`)));
    }
    if(job.action==='export'){
      const target=$('wb-export-links');target.replaceChildren();const name=job.run_name;
      [['HTML','html'],['JSON','json']].forEach(([label,ext])=>{const a=node('a',`Download ${label} report ↗`);a.href=`/api/export?name=${encodeURIComponent(name)}&format=${ext}`;a.target='_blank';a.rel='noopener';target.append(a);});
    }
  }
  wbLastJob=signature;
  if(busy&&!wbPoll)wbPoll=setTimeout(async()=>{wbPoll=null;await load();},1500);
}
function renderSuiteReport(){
  const target=$('wb-results');target.replaceChildren();const selected=$('wb-report-select').value;
  const saved=workspace?.workbench?.suite.reports.find(r=>r.run_name===selected);
  if(!saved?.report){target.append(node('p','No T12 run yet. Completed earlier investigations remain under Engineering reviews.','muted'));return;}
  const r=saved.report;target.append(field('Report status',saved.status),field('Execution mode',r.execution_mode),field('Frozen protocol',r.freeze_sha256),field('Actual requests / estimated settled cost',`${r.api_attempts} / $${formatNumber(r.settled_estimated_cost_usd)}`));
  const table=node('table',undefined,'science-table'),head=node('tr');['Method','Valid / selected','Failed / not attempted','Correct verdict','All checks passed','Numeric tasks','Unsupported endorsements','Missed contradictions'].forEach(t=>head.append(node('th',t)));table.append(head);
  Object.entries(r.summary.methods||{}).forEach(([m,s])=>{const row=node('tr');[m.replaceAll('_',' '),`${s.available}/${s.selected}`,`${s.failed_outputs} / ${s.not_attempted}`,`${s.correct}/${s.available} (${s.accuracy_percent===null?'unavailable':formatNumber(s.accuracy_percent)+'%'})`,`${s.passed}/${s.available}`,`${s.numeric_exact}/${s.numeric_total}`,s.unsupported_endorsements,`${s.missed_contradictions}/${s.reference_contradictions}`].forEach(v=>row.append(node('td',String(v))));table.append(row);});
  const scroll=node('div',undefined,'table-scroll');scroll.append(table);target.append(scroll,node('p',r.summary.scope||'Scores withheld','tiny'));
  const summary=node('details');summary.append(node('summary','Paired changes and source groups'),node('pre',JSON.stringify(r.summary,null,2),'source-text'));target.append(summary);
  r.rows.forEach(row=>{
    const card=node('article',undefined,'panel accounting-check');card.append(node('h4',`${row.case_id} · ${row.title}`),field('Workflow',row.status),node('p',row.evidence.question));if(row.error)card.append(node('p',row.error,'callout'));
    ['one_pass','challenge_revision','resample_control','checklist'].forEach(method=>{
      const answer=row.answers[method],s=row.scores?.[method];const detail=node('details');detail.append(node('summary',`${method.replaceAll('_',' ')} · ${answer?answer.verdict:'not available'}`));
      if(answer){detail.append(node('p',answer.rationale),field('Next evidence request — usefulness unscored',answer.next_evidence_request),field('Source references',answer.evidence_refs.join(', ')),field('Missing records',answer.missing_inputs.join(', ')||'None'),field('Value / unit',`${answer.value??'not applicable'} / ${answer.unit}`));}
      if(s?.available)detail.append(field('Reference verdict',s.expected),node('p',s.reference_basis,'tiny'),field('Reference audit',JSON.stringify(s,null,2)));card.append(detail);
    });
    const tool=node('details');tool.append(node('summary','Actual selected tool, critic and independent calculation'),node('pre',JSON.stringify({tool:row.tool,critic:row.critic,independent_check:row.independent_numeric},null,2),'source-text'));card.append(tool);target.append(card);
  });
}
async function workbenchAction(action){
  if(!workspace?.workbench)return;
  const data={action};if(action==='freeze')data.freeze_name=$('wb-freeze').value;
  if(action==='run')Object.assign(data,{run_name:$('wb-run').value,freeze_name:$('wb-freeze').value,split:$('wb-split').value,case_id:$('wb-case').value,consent:$('wb-consent').checked});
  if(action==='export')data.run_name=$('wb-export-name').value;
  ['wb-start','wb-check','wb-freeze-button','wb-export'].forEach(id=>$(id).disabled=true);
  try{
    const response=await fetch('/api/actions',{method:'POST',headers:{'Content-Type':'application/json','X-MRE-Token':workspace.workbench.csrf},body:JSON.stringify(data)});
    const result=await response.json();if(!response.ok)throw new Error(result.error||'Action rejected');
    if(action==='run')$('wb-consent').checked=false;
    await load();
  }catch(error){$('wb-job').textContent=error.message;['wb-start','wb-check','wb-freeze-button','wb-export'].forEach(id=>$(id).disabled=false);$('wb-start').disabled=!$('wb-consent').checked||!workspace.workbench.api_key_present;}
}
$('wb-split').addEventListener('change',updateCaseOptions);$('wb-case').addEventListener('change',renderCasePreview);$('wb-report-select').addEventListener('change',renderSuiteReport);
$('wb-consent').addEventListener('change',()=>{$('wb-start').disabled=!$('wb-consent').checked||!workspace?.workbench?.api_key_present||workspace?.workbench?.job.state==='running';});
[['wb-check','check'],['wb-freeze-button','freeze'],['wb-start','run'],['wb-stop','stop'],['wb-export','export']].forEach(([id,action])=>$(id).addEventListener('click',()=>workbenchAction(action)));
