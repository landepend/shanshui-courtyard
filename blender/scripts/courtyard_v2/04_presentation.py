import bpy,math
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
scene=bpy.data.scenes['COURTYARD_V2'];bpy.context.window.scene=scene
studio=bpy.data.collections.get('COURTYARD_PRESENTATION') or bpy.data.collections.new('COURTYARD_PRESENTATION')
if studio.name not in scene.collection.children:scene.collection.children.link(studio)
def move_to_studio(o):
    for c in list(o.users_collection):c.objects.unlink(o)
    studio.objects.link(o)
bpy.ops.object.camera_add(location=(29,-40,29))
cam=bpy.context.object;cam.name='Courtyard_PresentationCamera';move_to_studio(cam)
cam.rotation_euler=(Vector((0,1,4))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=44;scene.camera=cam
bpy.ops.object.light_add(type='SUN',location=(-15,-20,30))
sun=bpy.context.object;sun.name='Courtyard_StudioSun';move_to_studio(sun)
sun.rotation_euler=(.42,-.45,-.55);sun.data.energy=2;sun.data.angle=.15
bpy.ops.object.light_add(type='AREA',location=(15,-10,30))
fill=bpy.context.object;fill.name='Courtyard_StudioFill';move_to_studio(fill)
fill.data.energy=3500;fill.data.shape='DISK';fill.data.size=20
fill.rotation_euler=(Vector((0,0,4))-fill.location).to_track_quat('-Z','Y').to_euler()
world=bpy.data.worlds.new('Courtyard_StudioWorld');world.use_nodes=True
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
bg.inputs['Color'].default_value=(.55,.62,.57,1);bg.inputs['Strength'].default_value=.65;scene.world=world
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.11))
plane=bpy.context.object;plane.name='Courtyard_StudioGround';move_to_studio(plane)
m=bpy.data.materials.new('Courtyard_PreviewGround');m.use_nodes=True
p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(.28,.33,.26,1);p.inputs['Roughness'].default_value=.95
plane.data.materials.append(m)
try:scene.render.engine='BLENDER_EEVEE'
except TypeError as e:print(e)
scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.filepath=project_path('docs/screenshots/courtyard-blender-v2.png')
im=bpy.data.images.load(project_path('assets/concepts/courtyard-atang-anime-v2.png'),check_existing=True);im.pack();im.use_fake_user=True
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=project_path('blender/Courtyard.blend'))
print('COURTYARD_PREVIEW_SAVED')

