"""Owner-run Blender exporter. No API call and no physics on import.
Blender --background --python scripts/build_reactor_asset.py -- --output outputs/reactor-assets/yu2025
"""
import argparse,json,math,hashlib,sys
from pathlib import Path

def main():
 import bpy
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args(args)
 out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
 target=out/'reactor.glb';manifest=out/'manifest.json'
 if target.exists() or manifest.exists():raise RuntimeError('Use a new output directory; assets are never overwritten')
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 mats={}
 for key,color in {'ceramic':(.76,.78,.70,1),'pt':(.65,.69,.74,1),'mo':(.30,.37,.43,1),'melt':(.72,.24,.06,1),'steel':(.24,.29,.34,1),'gas':(.40,.75,.82,1)}.items():
  m=bpy.data.materials.new(key);m.diffuse_color=color;m.use_nodes=True
  bsdf=m.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=color;bsdf.inputs['Roughness'].default_value=.38
  mats[key]=m
 parts=[]
 def mesh(name,vertices,faces,mat):
  data=bpy.data.meshes.new(name);data.from_pydata(vertices,[],faces);data.update()
  obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj);obj.data.materials.append(mats[mat]);parts.append(name);return obj
 def tube(name,ri,ro,z0,z1,mat,cut=False):
  n=72;theta=1.5*math.pi if cut else 2*math.pi;start=math.pi*.25 if cut else 0
  vertices=[]
  for z,r in [(z0,ri),(z0,ro),(z1,ri),(z1,ro)]:
   vertices.extend((r*math.cos(start+theta*i/n),r*math.sin(start+theta*i/n),z) for i in range(n+1))
  m=n+1;faces=[]
  for i in range(n):
   faces.extend([(i,i+1,2*m+i+1,2*m+i),(m+i,3*m+i,3*m+i+1,m+i+1),(i,m+i,m+i+1,i+1),(2*m+i,2*m+i+1,3*m+i+1,3*m+i)])
  if cut:faces.extend([(0,2*m,3*m,m),(n,m+n,3*m+n,2*m+n)])
  return mesh(name,vertices,faces,mat)
 def rod(name,r,z0,z1,mat,x=0,y=0):
  bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=r,depth=z1-z0,location=(x,y,(z1+z0)/2))
  obj=bpy.context.object;obj.name=name;obj.data.materials.append(mats[mat]);parts.append(name);return obj
 # All dimensions below are normalized visual assumptions, NOT paper CAD dimensions.
 tube('vessel__outer_alumina',1.22,1.30,-1.35,1.30,'ceramic',True)
 tube('wall__YSZ',.92,1.00,-1.22,1.0,'ceramic',True)
 tube('anode__exterior_Pt_collector',1.005,1.025,-1.15,-.45,'pt',True)
 rod('cathode__Mo',.16,-1.12,1.70,'mo')
 tube('cathode__alumina_sheath',.17,.23,-.20,1.40,'ceramic')
 tube('melt__regolith',.165,.91,-1.17,-.55,'melt',True)
 tube('vessel__endplate',.24,1.34,1.30,1.39,'steel',True)
 rod('gas__outlet',.07,1.38,1.92,'gas',.80,0)
 rod('gas__inlet',.07,1.38,1.75,'gas',-.80,0)
 tube('vessel__furnace_context',1.45,1.63,-1.35,-.35,'steel',True)
 # Export Y-up glTF; separate named meshes retain selection/mapping.
 bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',export_yup=True)
 receipt={'design':'Yu2025 inverted YSZ/Pt hollow-anode arrangement','source_url':'https://ntrs.nasa.gov/citations/20250004626','locator':'Figure 1(b); methods 2.2.1–2.2.2; supplementary Figure S1',
  'geometry_class':'normalized_source_based_approximation','dimensions':'All visual dimensions are authoring assumptions, not published CAD or solver dimensions.',
  'parts':parts,'sam_role':'Optional visible-component reference masks only. This exporter does not claim SAM 3D reconstruction.',
  'physics_boundary':'GLB is visual only. Radial solver geometry remains separately entered and validated.',
  'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
 manifest.write_text(json.dumps(receipt,indent=2));print(str(target));print(str(manifest))
if __name__=='__main__':main()
