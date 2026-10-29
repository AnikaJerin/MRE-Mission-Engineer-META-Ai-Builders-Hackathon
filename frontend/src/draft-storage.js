// Local draft backup only: never credentials, credit consent or automatic API work.
const prefix='mre.workspace-draft.v1.';
export function readBackup(storage,id) {
  try {const value=JSON.parse(storage.getItem(prefix+id));return value?.draft?.form && typeof value.draft.form==='object' ? value : null;} catch {return null;}
}
export function writeBackup(storage,id,draft,serverRevision,dirty=true) {
  try {storage.setItem(prefix+id,JSON.stringify({draft,serverRevision,dirty,savedAt:new Date().toISOString()}));return true;} catch {return false;}
}
export function chooseDraft(server,backup) {
  if (backup?.dirty && backup.serverRevision === server.revision) return {draft:backup.draft,conflict:false,from:'browser backup'};
  return {draft:server.draft,conflict:Boolean(backup?.dirty && backup.serverRevision !== server.revision),from:'SQLite workspace'};
}

export function browserStorage(){try{return globalThis.localStorage;}catch{return null;}}
