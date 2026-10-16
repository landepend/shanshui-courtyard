import bpy, bmesh, math
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

from mathutils import Vector,Quaternion
C=bpy.data.collections['ATANG_CHARACTER_V2'];MASTER=bpy.data.objects['ATANG_Master']
body=bpy.data.objects['Atang_SkinnedCharacter'];rig=bpy.data.objects['Atang_Rig']
bm=bmesh.new();bm.from_mesh(body.data)
bad=[]
for f in bm.faces:
    mat=body.data.materials[f.material_index].name
    if mat in ['Atang_JadeFabric','Atang_AnimeGold','Atang_SilkThread'] and all(v.co.z>.821 and abs(v.co.x)<.155 for v in f.verts):bad.append(f)
bmesh.ops.delete(bm,geom=bad,context='FACES')
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(body.data);bm.free()
rings=[(.77,.149,.108),(.82,.151,.111),(.90,.157,.101),(.99,.174,.088),(1.023,.178,.076),(1.046,.134,.063),(1.066,.054,.047)]
def front(x,z):
    for i in range(len(rings)-1):
        lo,hi=rings[i],rings[i+1]
        if lo[0]<=z<=hi[0]:
            t=(z-lo[0])/(hi[0]-lo[0]);rx=lo[1]*(1-t)+hi[1]*t;ry=lo[2]*(1-t)+hi[2]*t
            return -ry*math.sqrt(max(.04,1-(x/rx)**2))-.004
    return -.05
def bez(points,t):
    a,b,c,d=[Vector(p) for p in points]
    return (1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d
strips=[]
for index,control in enumerate([[(-.044,0,1.063),(-.061,0,1.032),(-.038,0,.993),(.005,0,.963)],[(.044,0,1.063),(.060,0,1.034),(.015,0,.965),(-.11,0,.823)]]):
    vs=[];fs=[]
    for j in range(41):
        t=j/40;p=bez(control,t);tan=(bez(control,min(1,t+.001))-bez(control,max(0,t-.001))).normalized()
        across=Vector((tan.z,0,-tan.x))
        for k in range(4):
            offset=[-.017,-.014,.014,.017][k];q=p+across*offset
            vs.append((q.x,front(q.x,q.z)-.001*index,q.z))
        if j<40:
            for k in range(3):a=j*4+k;fs.append((a,a+1,a+5,a+4))
    data=bpy.data.meshes.new('AnimeFittedCollarMesh');data.from_pydata(vs,[],fs);data.update()
    ob=bpy.data.objects.new('Atang_AnimeFittedCollar'+str(index),data);C.objects.link(ob);ob.parent=MASTER
    data.materials.append(bpy.data.materials['Atang_JadeFabric']);data.materials.append(bpy.data.materials['Atang_AnimeGold'])
    for f in data.polygons:f.use_smooth=True;f.material_index=0 if f.index%3==1 else 1
    g=ob.vertex_groups.new(name='chest');g.add(list(range(len(vs))),1,'REPLACE')
    strips.append(ob)
bpy.ops.object.select_all(action='DESELECT')
for ob in [body]+strips:ob.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
def rot(name,x=0,y=0,z=0):
    p=rig.pose.bones[name];p.rotation_mode='QUATERNION';q=p.bone.matrix_local.to_quaternion()
    p.rotation_quaternion=q.inverted() @ Quaternion((1,0,0),x) @ Quaternion((0,1,0),y) @ Quaternion((0,0,1),z) @ q
for clip,frames in [('Sprint',20),('Jump',18),('Fall',30),('Land',12),('Climb',36),('Glide',48)]:
    if bpy.data.actions.get(clip):bpy.data.actions.remove(bpy.data.actions[clip])
    action=bpy.data.actions.new(clip);action.use_fake_user=True;rig.animation_data.action=action
    for frame in range(1,frames+2):
        t=(frame-1)/frames;phase=t*math.tau
        for p in rig.pose.bones:p.rotation_mode='QUATERNION';p.rotation_quaternion=Quaternion();p.location=(0,0,0)
        if clip=='Sprint':
            rot('spine',.13);rot('head',-.08)
            for s,side in [(1,'L'),(-1,'R')]:
                f=phase+(0 if s==1 else math.pi)
                rot('thigh.'+side,.70*math.cos(f)-.2);rot('shin.'+side,.25+.7*max(0,math.sin(f)))
                rot('upper_arm.'+side,-.55*math.cos(f));rot('forearm.'+side,-.55)
                rot('skirt.'+side,.13*math.cos(f));rot('braid.'+side,.06*math.sin(f))
            rig.pose.bones['root'].location.y=.018*(1-math.cos(phase*2))
        elif clip=='Jump':
            for s,side in [(1,'L'),(-1,'R')]:
                rot('thigh.'+side,-.27-.18*math.sin(t*math.pi));rot('shin.'+side,.32+.48*math.sin(t*math.pi))
                rot('upper_arm.'+side,-.45-.50*math.sin(t*math.pi));rot('forearm.'+side,-.25)
            rot('spine',.08)
        elif clip=='Fall':
            for s,side in [(1,'L'),(-1,'R')]:
                rot('thigh.'+side,-.15);rot('shin.'+side,.35)
                rot('upper_arm.'+side,-.25,y=-s*.55);rot('forearm.'+side,-.1)
                rot('skirt.'+side,-.04)
        elif clip=='Land':
            crouch=math.sin(math.pi*t)*(1-t)
            rig.pose.bones['root'].location.y=-.07*crouch
            for s,side in [(1,'L'),(-1,'R')]:
                rot('thigh.'+side,-.40*crouch);rot('shin.'+side,.75*crouch)
                rot('foot.'+side,-.35*crouch);rot('upper_arm.'+side,-.3*crouch)
            rot('spine',.20*crouch)
        elif clip=='Climb':
            for s,side in [(1,'L'),(-1,'R')]:
                f=phase+(0 if s==1 else math.pi)
                rot('upper_arm.'+side,-2.55+.35*math.sin(f),y=-s*.10)
                rot('forearm.'+side,.35+.32*(1+math.sin(f)))
                rot('thigh.'+side,-.7-.28*math.sin(f));rot('shin.'+side,1.1+.3*math.sin(f))
                rot('foot.'+side,-.35);rot('skirt.'+side,-.13-.04*math.sin(f))
            rot('head',-.1)
        elif clip=='Glide':
            rot('spine',.12);rot('head',-.1)
            for s,side in [(1,'L'),(-1,'R')]:
                rot('upper_arm.'+side,-.45,y=-s*1.12);rot('forearm.'+side,-.20)
                rot('thigh.'+side,.08+.03*math.sin(phase));rot('shin.'+side,.16)
                rot('skirt.'+side,-.07);rot('braid.'+side,.13+.03*math.sin(phase))
            rot('sash',.15)
        for p in rig.pose.bones:
            p.keyframe_insert(data_path='rotation_quaternion',frame=frame,group=p.name)
            p.keyframe_insert(data_path='location',frame=frame,group=p.name)
rig.animation_data.action=bpy.data.actions['Idle'];bpy.context.scene.frame_set(1)
# Recalculate normals and verify all vertices have valid deform weights.
bm=bmesh.new();bm.from_mesh(body.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
assert all(sum(g.weight for g in v.groups if body.vertex_groups[g.group].name in rig.data.bones)>.99 for v in body.data.vertices)
bpy.ops.object.select_all(action='DESELECT')
for ob in [body,rig,MASTER]:ob.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=project_path('assets/characters/atang.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=True,export_animation_mode='ACTIONS',export_anim_single_armature=True,export_skins=True,export_yup=True)
bpy.ops.wm.save_as_mainfile(filepath=project_path('blender/Atang_Anime_v3.blend'))
bpy.context.scene.render.filepath=project_path('docs/screenshots/atang-anime-v3.png')
bpy.ops.render.render(write_still=True)
print('ANIME_GLTF_READY',len(body.data.vertices),[a.name for a in bpy.data.actions])

