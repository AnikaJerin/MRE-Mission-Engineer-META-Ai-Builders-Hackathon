export function formatCurrentTrace(rows=[]) {
  return rows.map(r=>`${r.time_s},${r.current_A},${r.voltage_V ?? ''},${r.source || ''}`).join('\n');
}
export function parseCurrentTrace(text='') {
  if(!text.trim())return [];
  const lines=text.trim().split(/\r?\n/).filter(line=>line.trim());
  if(lines.length<2 || lines.length>1000)throw new Error('Current history needs 2–1000 rows.');
  const rows=[];
  for(const line of lines){
    const [time,current,voltage,...source]=line.split(',').map(s=>s.trim());
    if(time==='' || current==null || current==='')throw new Error('Current rows: time_s,current_A,voltage_V,optional source.');
    const t=Number(time),i=Number(current),v=voltage==null || voltage===''?null:Number(voltage);
    if(!Number.isFinite(t) || !Number.isFinite(i) || t<0 || i<0 || v!==null && (!Number.isFinite(v) || v<0))throw new Error('Trace values must be finite nonnegative numbers; put no units in the row.');
    if(rows.length && t<=rows[rows.length-1].time_s)throw new Error('Current-history times must strictly increase; rows are not sorted automatically.');
    rows.push({time_s:t,current_A:i,voltage_V:v,source:source.join(',') || null});
  }
  return rows;
}
