export async function get(path) {
  const response = await fetch(path, {cache: 'no-store'});
  let value;
  try {value = await response.json();} catch {throw new Error(response.status===404?'This feature needs the updated backend. Restart the backend once; keep all saved files.':'Cannot read the Python backend response. Check the backend on 127.0.0.1:8769.');}
  if (!response.ok) throw new Error((value.error || 'The local request failed.')+(value.incident_id ? ` [Incident ${value.incident_id}]` : ''));
  return value;
}
export async function action(token, value) {
  const response = await fetch('/api/actions', {method: 'POST', headers: {'Content-Type': 'application/json', 'X-MRE-Token': token}, body: JSON.stringify(value)});
  let result;
  try {result = await response.json();} catch {throw new Error('Cannot reach the Python backend on port 8769.');}
  if (!response.ok) throw new Error(result.error || 'The local action was rejected.');
  return result;
}

export async function saveDraft(token,draft,revision) {
  const response=await fetch('/api/workspace-draft',{method:'POST',headers:{'Content-Type':'application/json','X-MRE-Token':token},body:JSON.stringify({draft,revision})});
  const value=await response.json();
  if(!response.ok){const error=new Error(value.error || 'Draft save failed. Browser backup retained.');error.status=response.status;throw error;}
  return value;
}
