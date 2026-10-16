import bpy, math
from pathlib import Path

def project_path(relative):
    """Resolve from the script, an opened project .blend, or the working directory."""
    for source in (globals().get('__file__'), bpy.data.filepath, str(Path.cwd())):
        if not source:
            continue
        origin = Path(source).resolve()
        for parent in (origin, *origin.parents):
            if (parent / 'index.html').is_file() and (parent / 'assets').is_dir():
                return str(parent / relative)
    raise RuntimeError('Cannot locate the project. Open its .blend file or run the script by filename from this project.')

from mathutils import Vector
scene=bpy.context.scene
studio=bpy.data.collections.new('ATANG_PRESENTATION')
scene.collection.children.link(studio)
def link(o):
    for c in list(o.users_collection):c.objects.unlink(o)
    studio.objects.link(o)
bpy.ops.object.camera_add(location=(2,-4,2.0))
cam=bpy.context.object;cam.name='Atang_PresentationCamera';link(cam)
cam.rotation_euler=(Vector((0,0,.78))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=1.92
scene.camera=cam
for name,position,power,size in [('Key',(-3,-4,5),380,4),('Fill',(3,-1,3),210,3),('Rim',(1,3,4),350,3)]:
    bpy.ops.object.light_add(type='AREA',location=position)
    light=bpy.context.object;light.name='Atang_'+name;link(light);light.data.energy=power;light.data.shape='DISK';light.data.size=size
    light.rotation_euler=(Vector((0,0,.8))-light.location).to_track_quat('-Z','Y').to_euler()
world=bpy.data.worlds.new('Atang_StudioWorld');world.use_nodes=True
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
bg.inputs['Color'].default_value=(.45,.42,.36,1);bg.inputs['Strength'].default_value=.45
scene.world=world
try:scene.render.engine='BLENDER_EEVEE'
except TypeError as e:print('ENGINE',e)
print('CAMERA_ENUMS',[i.identifier for i in bpy.types.Camera.bl_rna.properties['type'].enum_items])
print('IMAGE_ENUMS',[i.identifier for i in scene.render.image_settings.bl_rna.properties['file_format'].enum_items])
scene.render.resolution_x=900;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.filepath=project_path('docs/screenshots/atang-blender.png')
rig=bpy.data.objects['Atang_Rig'];rig.animation_data.action=bpy.data.actions['Idle'];scene.frame_set(1)
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=project_path('blender/Atang.blend'))
print('PRESENTATION_SAVED')

