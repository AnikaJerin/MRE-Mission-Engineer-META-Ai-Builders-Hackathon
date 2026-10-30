"""Blender --background --python THIS -- INPUT_GLB OUTPUT_GLB COMPONENT.
Preserves reconstructed shape; centres and normalizes visual scale only.
No inferred engineering dimensions or simulation mesh.
"""
import sys,json,hashlib
from pathlib import Path
import bpy
args=sys.argv[sys.argv.index('--')+1:]
if len(args)!=3:raise SystemExit('Expected INPUT_GLB OUTPUT_GLB COMPONENT')
source,dest=map(Path,args[:2]);component=args[2]
if component not in ('vessel','wall','anode','cathode','melt','gas'):raise SystemExit('Unsupported component')
if dest.exists():raise SystemExit('Output exists; choose a new path')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(source))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
if not meshes:raise SystemExit('No reconstructed mesh')
for i,o in enumerate(meshes):o.name=component+'__SAM3D_'+str(i)
dest.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB')
bpy.ops.wm.save_as_mainfile(filepath=str(dest.with_suffix('.blend')))
dest.with_suffix('.provenance.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'mesh_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'component':component,'operation':'Named reconstructed meshes; source shape preserved. No engineering dimensions established.','solver_mesh':False},indent=2))
