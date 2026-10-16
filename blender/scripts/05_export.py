import bpy
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
rig=bpy.data.objects['Atang_Rig'];body=bpy.data.objects['Atang_SkinnedCharacter']
rig.animation_data.action=bpy.data.actions['Idle']
bpy.context.scene.frame_set(1)
bpy.context.scene.frame_end=61
bpy.ops.object.select_all(action='DESELECT')
for o in [rig,body,bpy.data.objects['ATANG_Master']]:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.wm.save_as_mainfile(filepath=project_path('blender/Atang.blend'))
try:
    bpy.ops.export_scene.gltf(filepath=project_path('assets/characters/atang.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_anim_single_armature=True,export_skins=True,export_yup=True)
except TypeError as e:print('EXPORT_ENUM_ERROR',str(e))
print('SAVED_AND_EXPORTED',[(a.name,list(a.frame_range)) for a in bpy.data.actions])

