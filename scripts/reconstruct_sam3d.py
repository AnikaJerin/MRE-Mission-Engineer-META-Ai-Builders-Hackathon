"""Owner-run on the official SAM 3D Objects Linux/NVIDIA environment.
Not a Meta Model API endpoint; never substitutes a procedural mesh on failure.
"""
import argparse,json,hashlib,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--sam3d-repo',required=True);p.add_argument('--pipeline',required=True);p.add_argument('--bundle',required=True);p.add_argument('--output',required=True);a=p.parse_args()
b=Path(a.bundle);dest=Path(a.output)
if dest.exists():raise SystemExit('Output already exists; choose a new directory')
# Dependencies belong to the official external SAM 3D environment.
import numpy as np
from PIL import Image
mask=json.loads((b/'mask.json').read_text());image=np.asarray(Image.open(b/'reference.png').convert('RGB'))
m=np.asarray(mask['pixels'],dtype=np.uint8).reshape(mask['height'],mask['width']).astype(bool)
if image.shape[:2]!=m.shape or not m.any():raise SystemExit('Mask/image alignment or empty-mask error')
sys.path.insert(0,str(Path(a.sam3d_repo)/'notebook'))
from inference import Inference
model=Inference(a.pipeline,compile=False);result=model(image,m,seed=42)
mesh=result.get('glb')
if mesh is None:raise SystemExit('SAM 3D returned no GLB; no replacement generated')
dest.mkdir(parents=True);mesh.export(str(dest/'component.glb'))
meta={'component':mask['component'],'sam_id':mask['sam_id'],'source':mask.get('source'),'sam_report_sha256':mask['report_sha256'],'model':'facebookresearch/sam-3d-objects','geometry_class':'approximate_visual_reconstruction','physical_scale_verified':False,'solver_mesh':False,'seed':42,'mesh_sha256':hashlib.sha256((dest/'component.glb').read_bytes()).hexdigest()}
(dest/'provenance.json').write_text(json.dumps(meta,indent=2));print(dest)
