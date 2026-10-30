// Decode saved provider events using Meta's parser; never trust browser-submitted pixels.
import fs from 'node:fs';
import {parseImageStream,recordsOfKind,decodeMaskToRaster,decodeMaskToRLE} from '@meta-sam/parser';
const report=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
async function* events(){yield* report.events;}
const parsed=await parseImageStream(events()).finalResult;
if(parsed.outcome.status!=='completed'||parsed.diagnostics.some(d=>d.severity==='error'))throw Error('Incomplete SAM masks');
const masks=recordsOfKind(parsed.records,'mask').map((record,index)=>{
 const raw=decodeMaskToRaster(record.mask),rle=decodeMaskToRLE(record.mask),mh=rle.size[0],mw=rle.size[1],h=report.height,w=report.width,b=record.bounds,p=new Uint8Array(w*h);
 if(!b||b.left<0||b.top<0||b.right>w||b.bottom>h)throw Error('Mask/image coordinates do not match');
 for(let y=b.top;y<b.bottom;y++)for(let x=b.left;x<b.right;x++){const sx=Math.min(mw-1,Math.floor((x-b.left)*mw/(b.right-b.left))),sy=Math.min(mh-1,Math.floor((y-b.top)*mh/(b.bottom-b.top)));p[y*w+x]=raw[sy*mw+sx];}
 let area=0,eroded=0,dilated=0;const widths=[];let minX=w,minY=h,maxX=-1,maxY=-1;
 const at=(x,y)=>x>=0&&y>=0&&x<w&&y<h&&p[y*w+x]>0;
 for(let y=0;y<h;y++){let left=w,right=-1;for(let x=0;x<w;x++){
  const a=at(x,y),n=[a,at(x-1,y),at(x+1,y),at(x,y-1),at(x,y+1)];
  if(n.every(Boolean))eroded++;if(n.some(Boolean))dilated++;
  if(a){area++;left=Math.min(left,x);right=Math.max(right,x);minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y);}
 }if(right>=left)widths.push(right-left+1);}
 widths.sort((a,b)=>a-b);
 return {index,area_px:area,area_one_pixel_low:eroded,area_one_pixel_high:dilated,max_width_px:widths.at(-1)||0,median_row_width_px:widths.length?(widths[Math.floor((widths.length-1)/2)]+widths[Math.ceil((widths.length-1)/2)])/2:0,bbox:area?[minX,minY,maxX,maxY]:null,touches_edge:minX===0||minY===0||maxX===w-1||maxY===h-1};
});
process.stdout.write(JSON.stringify({masks}));
