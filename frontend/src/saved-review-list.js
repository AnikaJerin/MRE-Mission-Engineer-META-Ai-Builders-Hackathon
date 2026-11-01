export function selectReviews(rows,{query='',status='all',newestFirst=true}={}) {
  const term=query.trim().toLocaleLowerCase();
  const timestamp=row=>Number.isFinite(Date.parse(row.created_at))?Date.parse(row.created_at):0;
  return rows.filter(row=>(status==='all'||row.status===status) && (!term||String(row.name||'').toLocaleLowerCase().includes(term)))
    .slice().sort((a,b)=>(newestFirst?-1:1)*(timestamp(a)-timestamp(b)) || String(a.id).localeCompare(String(b.id)));
}
