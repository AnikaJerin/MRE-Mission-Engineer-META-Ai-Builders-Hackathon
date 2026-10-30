// Owner-run export of an actual SAM mask. No API calls or reconstruction here.
import fs from 'node:fs';import path from 'node:path';import {createRequire} from 'node:module';import {fileURLToPath,pathToFileURL} from 'node:url';import crypto from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),id=process.argv[2];
if(!/^[a-zA-Z0-9_-]{1,100}$/.test(id||''))throw Error('Usage: node scripts/export_sam3d_input.mjs SAVED_SAM_ID');
const base=path.join(root,'outputs/sam-segmentations',id),r=JSON.parse(fs.readFileSync(path.join(base,'report.json'),'utf8'));
if(r.status!=='completed'||r.model!=='sam-3.1')throw Error('A completed actual SAM 3.1 segmentation is required');
const require=createRequire(path.join(root,'frontend/package.json')),parser=await import(pathToFileURL(require.resolve('@meta-sam/parser')).href);
async function* events(){yield* r.events;}
const parsed=await parser.parseImageStream(events()).finalResult;
if(parsed.outcome.status!=='completed'||parsed.diagnostics.some(d=>d.severity==='error'))throw Error('Incomplete SAM output');
const masks=parser.recordsOfKind(parsed.records,'mask');if(!masks.length)throw Error('No mask returned; no reconstruction input created');
const decoded=masks.map(m=>{const pixels=parser.decodeMaskToRaster(m.mask),rle=parser.decodeMaskToRLE(m.mask);return {pixels:Array.from(pixels),width:rle.size[1],height:rle.size[0]};}).sort((a,b)=>b.pixels.reduce((x,y)=>x+y,0)-a.pixels.reduce((x,y)=>x+y,0));
const mask=decoded[0];if(mask.width!==r.width||mask.height!==r.height)throw Error('Cropped mask coordinates require manual alignment. Export stopped rather than inventing alignment.');
const out=path.join(root,'outputs/sam3d-inputs',id);fs.mkdirSync(out,{recursive:true});if(fs.existsSync(path.join(out,'mask.json')))throw Error('Export exists; reuse it');
fs.copyFileSync(path.join(base,'input.png'),path.join(out,'reference.png'));
fs.writeFileSync(path.join(out,'mask.json'),JSON.stringify({...mask,component:r.component_id,source:r.source,sam_id:id,report_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(base,'report.json'))).digest('hex')}));console.log(out);
