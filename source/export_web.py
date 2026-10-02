"""Derive a layered, compressed glTF from the final bpy model; never save over it."""
import bpy,json,time
from pathlib import Path
from collections import defaultdict
root=Path(__file__).resolve().parents[1]
dest=root/'web_publish'/'assets';dest.mkdir(parents=True,exist_ok=True)
t=time.perf_counter()
bpy.ops.wm.open_mainfile(filepath=str(root/'StarPark_52_Optimized.blend'))
scene=bpy.context.scene
# Match the verified native cutaway view while retaining these objects for full views.
cutaway_prefix=('Ceiling','Continuous walnut ceiling','Continuous warm cove','Recessed ceiling','Recessed amber','Downlight','BATCH | Recessed ceiling','BATCH | Downlight','Bath front partition','Bath rear partition','Garage padded lining','Garage side rib','Garage warm perimeter','Pleated lounge drape','Wet room tiled wall','Vanity mirror','Mirror edge light','Walnut window','Walnut valance','Window valance','Cockpit walnut','Cockpit warm','Cockpit thin','Panoramic cockpit')
layers={
 'BODY • coachwork':('body','车身'),
 'BODY • trim, lamps & service panels':('trim','灯具与饰件'),
 'CHASSIS • engine & utility systems':('engine','发动机与水电系统'),
 'CHASSIS • structural frame':('frame','底盘车架'),
 'CHASSIS • wheels & brakes':('wheels','车轮与制动'),
 'GARAGE • cherry roadster / nose forward':('roadster','车库内跑车'),
 'GARAGE • low deck':('garage','下层车库'),
 'INTERIOR • bathroom':('bathroom','卫浴'),
 'INTERIOR • cockpit':('cockpit','驾驶舱'),
 'INTERIOR • floor & partitions':('floor','地板与隔断'),
 'INTERIOR • lounge':('lounge','客厅'),
 'INTERIOR • raised low-headroom bedroom':('bedroom','后部卧室'),
 'INTERIOR • walnut galley':('kitchen','厨房'),
 'ROOF • equipment & access':('roof','车顶设备'),
 'ROOF • forward drone lift':('drone','前部无人机平台'),
 'ROOF • rear cinematic prop':('roofprop','车顶造型道具')}
# glTF carries browser PBR values; original procedural materials remain in .blend.
for m in bpy.data.materials:
    if not m.use_nodes:continue
    nodes=m.node_tree.nodes
    p=next((n for n in nodes if n.type=='BSDF_PRINCIPLED'),None)
    if not p:continue
    values={k:p.inputs[k].default_value[:] if k in ('Base Color','Emission Color') else p.inputs[k].default_value for k in ('Base Color','Metallic','Roughness','Alpha','Emission Color','Emission Strength')}
    color=list(m.diffuse_color)
    # A brighter representative colour keeps wood/stone readable without texture baking.
    if m.name.startswith(('09 |','12 |')):color=list(values['Base Color'])
    values['Base Color']=color
    if m.name.startswith(('23 |','GLAZING |')):
        values.update({'Base Color':(.055,.10,.115,1),'Alpha':.35,'Metallic':.14,'Roughness':.12})
    if 'clear shower' in m.name:
        values.update({'Base Color':(.52,.65,.69,1),'Alpha':.14,'Metallic':0,'Roughness':.08})
    nodes.clear()
    p=nodes.new('ShaderNodeBsdfPrincipled');out=nodes.new('ShaderNodeOutputMaterial')
    m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface'])
    for k,v in values.items():p.inputs[k].default_value=v
    p.inputs['Emission Strength'].default_value=min(values['Emission Strength'],2)
    if hasattr(m,'use_backface_culling'):m.use_backface_culling=False
    if hasattr(m,'surface_render_method'):m.surface_render_method='DITHERED'

keep=[];hatch=bpy.data.objects.get('GARAGE HATCH • rotate Y to open')
for o in list(scene.objects):
    col=next((c.name for c in o.users_collection if c.name in layers),None)
    if not col or o.type not in {'MESH','CURVE','FONT','EMPTY'}:
        bpy.data.objects.remove(o,do_unlink=True);continue
    o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
    keep.append((o,col,o.name.startswith(cutaway_prefix),o.parent==hatch))
for c in bpy.data.collections:c.hide_viewport=False;c.hide_render=False
bpy.ops.object.select_all(action='DESELECT')
for o,col,cut,move in keep:
    if o.type in {'MESH','CURVE','FONT'}:o.select_set(True)
bpy.context.view_layer.objects.active=next(o for o,col,cut,move in keep if o.type=='MESH')
bpy.ops.object.convert(target='MESH')
batches=defaultdict(list)
for o,col,cut,move in keep:
    if o.type=='MESH':batches[(col,cut,move)].append(o)
groups={};counts={};original_meshes=sum(len(v) for v in batches.values())
for (col,cut,move),obs in batches.items():
    if col not in groups:
        key,label=layers[col];g=bpy.data.objects.new('WEB_'+key,None);scene.collection.objects.link(g)
        g['layer']=key;g['label']=label;groups[col]=g
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:
        # Clear original parenting while preserving geometry positions before joining.
        mat=o.matrix_world.copy();o.parent=None;o.matrix_world=mat;o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
    if len(obs)>1:bpy.ops.object.join()
    obj=bpy.context.object
    obj.name='WEBMESH_'+layers[col][0]+('_cutaway_cover' if cut else '')+('_hatch' if move else '')
    obj['cutawayHide']=cut
    mat=obj.matrix_world.copy();obj.parent=hatch if move else groups[col];obj.matrix_world=mat
    counts.setdefault(layers[col][0],0);counts[layers[col][0]]+=len(obj.data.polygons)
if hatch:
    mat=hatch.matrix_world.copy();hatch.parent=groups['BODY • trim, lamps & service panels'];hatch.matrix_world=mat
    hatch.name='WEB_garage_hatch';hatch['isHatch']=True
# Delete unused helper empties, retain semantic groups and the working hatch pivot.
for o in list(scene.objects):
    if o.type=='EMPTY' and o not in groups.values() and o!=hatch:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.preferences.addon_enable(module='io_scene_gltf2')
filepath=dest/'starpark.glb'
kwargs=dict(filepath=str(filepath),export_format='GLB',use_selection=True,export_yup=True,export_apply=False,export_materials='EXPORT',export_extras=True,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=16,export_draco_normal_quantization=12,export_draco_texcoord_quantization=14)
bpy.ops.export_scene.gltf(**kwargs)
report={'source':'StarPark_52_Optimized.blend','blender':bpy.app.version_string,'source_iteration':15,'mesh_objects_before':original_meshes,'mesh_objects_after':sum(o.type=='MESH' for o in scene.objects),'faces_by_layer':counts,'layers':[{'id':v[0],'label':v[1]} for v in layers.values()],'bytes':filepath.stat().st_size,'seconds':round(time.perf_counter()-t,2),'browser_materials':'PBR approximation of the native procedural materials','source_modified':False}
(dest/'model-info.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
(root/'logs'/'web_export_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('WEB_EXPORT',json.dumps(report,ensure_ascii=False),flush=True)
