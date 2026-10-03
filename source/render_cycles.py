"""Cycles edition of the V15 procedural RV. Keeps the existing Eevee edition intact."""
import bpy,sys,argparse,json,time,math,bmesh
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
if (ROOT/'StarPark_Cycles_Master.blend').exists():OUT=ROOT;ROOT=ROOT.parent
else:OUT=ROOT/'cycles_v01'
p=argparse.ArgumentParser()
p.add_argument('--prepare',action='store_true')
p.add_argument('--view',choices=['Exterior','reference','entrance','cutaway','chassis','garage','roof','lounge','kitchen'],default='Exterior')
p.add_argument('--preview',action='store_true');p.add_argument('--round',type=int,default=1)
p.add_argument('--device',choices=['CUDA','CPU'],default='CUDA');p.add_argument('--samples',type=int,default=0);p.add_argument('--width',type=int,default=0)
p.add_argument('--project-root',type=Path)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
if a.project_root:ROOT=a.project_root.resolve();OUT=ROOT/'cycles_v01'
OUT.mkdir(exist_ok=True)
(OUT/'renders').mkdir(exist_ok=True);(OUT/'previews').mkdir(exist_ok=True);(OUT/'logs').mkdir(exist_ok=True)
t=time.perf_counter()
MASTER=OUT/'StarPark_Cycles_Master.blend'

def settings(s,preview=False):
    s.render.engine='CYCLES'
    s.cycles.samples=a.samples or (64 if preview else (384 if a.view in ['lounge','kitchen'] else 256))
    s.cycles.use_adaptive_sampling=True;s.cycles.adaptive_threshold=.04 if preview else .012
    s.cycles.adaptive_min_samples=16 if preview else 32
    s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
    s.cycles.denoising_input_passes='RGB_ALBEDO_NORMAL'
    if hasattr(s.cycles,'use_denoising_gpu'):s.cycles.use_denoising_gpu=False
    s.cycles.max_bounces=12;s.cycles.diffuse_bounces=4;s.cycles.glossy_bounces=6
    s.cycles.transmission_bounces=10;s.cycles.transparent_max_bounces=12;s.cycles.volume_bounces=0
    s.cycles.caustics_reflective=False;s.cycles.caustics_refractive=False
    s.cycles.blur_glossy=.5;s.cycles.sample_clamp_indirect=5
    s.cycles.preview_samples=16;s.cycles.use_preview_denoising=True
    s.render.threads_mode='FIXED';s.render.threads=24
    width=a.width or (1120 if preview else 2560)
    s.render.resolution_x=width;s.render.resolution_y=round(width*.625);s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.color_depth='8' if preview else '16'
    s.render.image_settings.compression=35
    s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast'
    s.view_settings.exposure=.15
    for screen in bpy.data.screens:
        for ar in screen.areas:
            if ar.type=='VIEW_3D':
                sh=ar.spaces.active.shading;sh.type='SOLID';sh.color_type='MATERIAL'
                sh.show_shadows=False;sh.show_cavity=False;ar.spaces.active.overlay.show_overlays=False

def physical_glass(m,color,roughness):
    m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
    out=n.new('ShaderNodeOutputMaterial');out.location=(640,0)
    shader=n.new('ShaderNodeBsdfPrincipled');shader.location=(30,90)
    shader.inputs['Base Color'].default_value=(*color,1)
    shader.inputs['Metallic'].default_value=0;shader.inputs['Roughness'].default_value=roughness
    shader.inputs['Transmission Weight'].default_value=1;shader.inputs['IOR'].default_value=1.48
    # A thin-film tint for direct shadow rays prevents noise from tiny caustics.
    # Camera, reflected and transmitted rays still use the dielectric BSDF.
    path=n.new('ShaderNodeLightPath');path.location=(-240,-180)
    tr=n.new('ShaderNodeBsdfTransparent');tr.location=(20,-200);tr.inputs[0].default_value=(*color,1)
    mix=n.new('ShaderNodeMixShader');mix.location=(420,0)
    l.new(path.outputs['Is Shadow Ray'],mix.inputs[0]);l.new(shader.outputs['BSDF'],mix.inputs[1]);l.new(tr.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
    m['Cycles material']='Physical dielectric camera/reflection/refraction; tinted transparent shadow approximation; procedural nodes only'

def prepare():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'StarPark_52_Optimized.blend'));s=bpy.context.scene
    for m in bpy.data.materials:
        if m.name.startswith(('23 |','GLAZING |')):physical_glass(m,(.90,.95,.965),.038)
        if 'clear shower' in m.name:physical_glass(m,(.985,.995,1),.025)
        if m.name.startswith('16 |'):
            shader=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
            if shader:
                shader.inputs['Emission Color'].default_value=(1,.65,.35,1)
                shader.inputs['Emission Strength'].default_value=1.7
    for o in s.objects:
        if o.type=='LIGHT' and o.name.startswith('Interior warm'):
            o.data.color=(1,.84,.67);o.data.energy=26
    # A continuous procedural studio sky avoids inverted tree-line patterns
    # inherited from the direction shader originally tuned for Eevee reflections.
    n=s.world.node_tree.nodes;l=s.world.node_tree.links;n.clear()
    tc=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(tc.outputs['Normal'],sep.inputs[0])
    height=n.new('ShaderNodeMath');height.operation='MULTIPLY_ADD';height.inputs[1].default_value=.5;height.inputs[2].default_value=.5;l.new(sep.outputs['Z'],height.inputs[0])
    sky=n.new('ShaderNodeValToRGB');sky.name='Cycles procedural studio sky'
    sky.color_ramp.elements[0].color=(.28,.29,.29,1);sky.color_ramp.elements[1].color=(.48,.60,.76,1)
    middle=sky.color_ramp.elements.new(.5);middle.color=(.72,.74,.71,1)
    sky.color_ramp.interpolation='EASE';l.new(height.outputs[0],sky.inputs[0])
    background=n.new('ShaderNodeBackground');background.inputs['Strength'].default_value=.45;l.new(sky.outputs[0],background.inputs['Color'])
    world_out=n.new('ShaderNodeOutputWorld');l.new(background.outputs[0],world_out.inputs['Surface'])
    s.world['Cycles environment']='Continuous node-generated studio sky; no HDR or bitmap; physical lighting/reflections'
    thickened=[]
    for name in ['Panoramic laminated wraparound windscreen','Roadster windscreen']:
        o=bpy.data.objects.get(name)
        if not o or o.type!='MESH':continue
        bm=bmesh.new();bm.from_mesh(o.data);has_boundary=any(e.is_boundary for e in bm.edges);bm.free()
        if not has_boundary:continue
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
        mod=o.modifiers.new('Cycles physical glazing thickness','SOLIDIFY');mod.thickness=.006;mod.offset=0
        bpy.ops.object.modifier_apply(modifier=mod.name);thickened.append(name)
    settings(s)
    s.camera=bpy.data.objects['CAM 01 | front right three-quarter'];s.cycles.device='CPU'
    s.render.filepath=str(OUT/'renders'/'StarPark_Cycles_Exterior.png')
    s['Render edition']='Cycles / V15 geometry / physical dielectric glazing / solid viewport'
    s['Cycles version']='01';s['Cycles source']='StarPark_52_Optimized.blend';s['Cycles script']='scripts/render_cycles.py'
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.wm.save_as_mainfile(filepath=str(MASTER))
    report={'engine':s.render.engine,'blender':bpy.app.version_string,'objects':len(s.objects),'modifiers':sum(len(o.modifiers) for o in s.objects),'thickened_glazing':thickened,'external_texture_nodes':[m.name for m in bpy.data.materials if m.use_nodes and any(n.type in {'TEX_IMAGE','TEX_ENVIRONMENT'} for n in m.node_tree.nodes)],'source_preserved':True,'native_default_device':'CPU; render script selects CUDA when requested','viewport':'SOLID material colors'}
    assert not report['external_texture_nodes'];assert report['modifiers']==0
    (OUT/'logs'/'preparation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print('CYCLES_PREPARED',json.dumps(report,ensure_ascii=False),flush=True)

def aim(o,pt):o.rotation_euler=(Vector(pt)-o.location).to_track_quat('-Z','Y').to_euler()

def setup_view(s,view):
    if view=='Exterior':return
    if view=='cutaway':
        for c in bpy.data.collections:
            if c.name.startswith(('BODY','ROOF','SCENERY')):c.hide_render=True
        for o in bpy.data.objects:
            if o.name.startswith(('Ceiling','Continuous walnut ceiling','Continuous warm cove','Recessed ceiling','Recessed amber','Downlight','BATCH | Recessed ceiling','BATCH | Downlight','Bath front partition','Bath rear partition','Garage padded lining','Garage side rib','Garage warm perimeter','Pleated lounge drape','Wet room tiled wall','Vanity mirror','Mirror edge light','Walnut window','Walnut valance','Window valance','Cockpit walnut','Cockpit warm','Cockpit thin','Panoramic cockpit')):o.hide_render=True
        cam=bpy.data.objects['CAM 02 | cabin cutaway'];cam.location=(-8,-26,18.7);aim(cam,(0,0,2));cam.data.ortho_scale=17.5
        for o in bpy.data.objects:
            if o.type=='LIGHT' and o.name.startswith('Interior warm'):o.data.energy=30
    elif view=='chassis':
        for c in bpy.data.collections:
            if not c.name.startswith(('CHASSIS','STUDIO')):c.hide_render=True
        cam=bpy.data.objects['CAM 03 | chassis engineering'];cam.location=(-11,-21,15.5);aim(cam,(0,0,.72));cam.data.ortho_scale=16.7
    elif view=='garage':
        bpy.data.objects['GARAGE HATCH • rotate Y to open'].rotation_euler[1]=math.radians(118)
        cam=bpy.data.objects['CAM 04 | low rear garage'];cam.location=(13,-7.2,4);aim(cam,(4.1,0,1.9));cam.data.ortho_scale=8.4
    elif view=='roof':
        cam=bpy.data.objects['CAM 05 | forward drone detail'];cam.location=(-9.4,-7.4,10.3);aim(cam,(-3.8,0,4.1));cam.data.ortho_scale=5.9
    elif view=='reference':cam=bpy.data.objects['CAM 07 | reference comparison']
    elif view=='entrance':cam=bpy.data.objects['CAM 08 | entrance side comparison']
    else:
        # Let the existing node-generated distant environment show through the glass.
        # The old cone-tree silhouettes were distracting in a refractive Cycles view.
        c=bpy.data.collections['SCENERY • procedural mountains and trees'];c.hide_render=True;c.hide_viewport=True
        bpy.data.objects['Infinite studio floor'].hide_render=True
        for n in s.world.node_tree.nodes:
            if n.type=='BACKGROUND':n.inputs['Strength'].default_value=.65
        for o in bpy.data.objects:
            if o.type=='LIGHT' and o.name in ['Key / enormous silk','Long rim / rear shoulder','Front beauty card','Side fill']:o.data.energy*=.24
        cam=bpy.data.objects['CAM 06 | interior']
        if view=='lounge':cam.location=(-1.65,.04,2.85);aim(cam,(-4.35,.1,2.32));cam.data.lens=17
        else:cam.location=(1.1,-.10,2.94);aim(cam,(-3.6,.03,2.20));cam.data.lens=21
        cam.data.dof.use_dof=True;cam.data.dof.focus_distance=3;cam.data.dof.aperture_fstop=3.2
    s.camera=cam

def device(s):
    if a.device=='CPU':s.cycles.device='CPU';return 'CPU'
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='CUDA';prefs.get_devices()
    gpus=[d for d in prefs.devices if d.type=='CUDA']
    if not gpus:s.cycles.device='CPU';return 'CPU (no CUDA device)'
    for d in prefs.devices:d.use=d.type=='CUDA'
    s.cycles.device='GPU';return 'CUDA / '+gpus[0].name

if a.prepare:prepare()
else:
    bpy.ops.wm.open_mainfile(filepath=str(MASTER));s=bpy.context.scene
    setup_view(s,a.view);settings(s,a.preview);backend=device(s)
    output=OUT/('previews' if a.preview else 'renders')/((f'round_{a.round:02d}_' if a.preview else 'StarPark_Cycles_')+a.view+'.png')
    s.render.filepath=str(output)
    print('CYCLES_START',a.view,backend,s.cycles.samples,s.render.resolution_x,flush=True)
    try:bpy.ops.render.render(write_still=True)
    except RuntimeError as e:
        if s.cycles.device!='GPU':raise
        print('CUDA_FALLBACK',str(e),flush=True);s.cycles.device='CPU';backend='CPU fallback: '+str(e);bpy.ops.render.render(write_still=True)
    report={'view':a.view,'preview':a.preview,'round':a.round,'engine':s.render.engine,'device':backend,'samples':s.cycles.samples,'adaptive_threshold':s.cycles.adaptive_threshold,'denoiser':s.cycles.denoiser,'resolution':[s.render.resolution_x,s.render.resolution_y],'color_depth':s.render.image_settings.color_depth,'camera':s.camera.name,'seconds':round(time.perf_counter()-t,2),'output':str(output),'bytes':output.stat().st_size}
    (OUT/'logs'/output.with_suffix('.json').name).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print('CYCLES_COMPLETE',json.dumps(report,ensure_ascii=False),flush=True)
