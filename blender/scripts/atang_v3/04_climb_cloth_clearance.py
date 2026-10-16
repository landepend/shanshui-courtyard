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

from mathutils import Quaternion
previous=bpy.context.scene
bpy.context.window.scene=bpy.data.scenes['ATANG_ANIME_V3']
rig=bpy.data.objects['Atang_Rig'];body=bpy.data.objects['Atang_SkinnedCharacter']
rig.animation_data.action=bpy.data.actions['Climb']
for frame in range(1,38):
    bpy.context.scene.frame_set(frame)
    phase=(frame-1)/36*math.tau
    for name,angle in [('skirt.front',-.55),('skirt.L',-.33-.04*math.sin(phase)),('skirt.R',-.33+.04*math.sin(phase)),('sash',-.30)]:
        p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion()
        p.rotation_quaternion=q.inverted() @ Quaternion((1,0,0),angle) @ q
        p.keyframe_insert(data_path='rotation_quaternion',frame=frame,group=p.name)
rig.animation_data.action=bpy.data.actions['Idle'];bpy.context.scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT')
for ob in [rig,body,bpy.data.objects['ATANG_Master']]:ob.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=project_path('assets/characters/atang.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=True,export_animation_mode='ACTIONS',export_anim_single_armature=True,export_skins=True,export_yup=True)
bpy.ops.wm.save_as_mainfile(filepath=project_path('blender/Atang_Anime_v3.blend'))
bpy.context.window.scene=previous
print('CLIMB_CLOTH_CLEARANCE_UPDATED')

