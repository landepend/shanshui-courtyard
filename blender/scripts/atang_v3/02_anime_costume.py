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
C = bpy.data.collections.get('ATANG_CHARACTER_V2')
MASTER = bpy.data.objects.get('ATANG_Master')
def material(name, color, rough=.6, metal=0):
    name='Atang_'+name
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True
    m.node_tree.nodes.clear()
    p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    o=m.node_tree.nodes.new('ShaderNodeOutputMaterial')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough
    p.inputs['Metallic'].default_value=metal
    m.node_tree.links.new(p.outputs['BSDF'],o.inputs['Surface'])
    m.diffuse_color=(*color,1)
    return m
def register(obj, name, mat, bone='head'):
    obj.name='Atang_'+name
    for collection in list(obj.users_collection): collection.objects.unlink(obj)
    C.objects.link(obj)
    obj.parent=MASTER
    if mat: obj.data.materials.append(mat)
    if obj.type=='MESH':
        for p in obj.data.polygons: p.use_smooth=True
        if bone:
            g=obj.vertex_groups.new(name=bone)
            g.add(list(range(len(obj.data.vertices))),1,'REPLACE')
    return obj
def uv(name, pos, scale, mat, bone='head', segments=24, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=pos)
    obj=bpy.context.object
    obj.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return register(obj,name,mat,bone)
def mesh(name, vertices, faces, mat, bone='head', uvs=None):
    data=bpy.data.meshes.new('Atang_'+name+'_Mesh')
    data.from_pydata(vertices,[],faces)
    data.update()
    obj=bpy.data.objects.new('Atang_'+name,data)
    C.objects.link(obj);obj.parent=MASTER
    if mat:data.materials.append(mat)
    for p in data.polygons:p.use_smooth=True
    if bone:
        g=obj.vertex_groups.new(name=bone);g.add(list(range(len(data.vertices))),1,'REPLACE')
    if uvs:
        layer=data.uv_layers.new(name='UVMap')
        for poly,coords in zip(data.polygons,uvs):
            for idx,coord in zip(poly.loop_indices,coords):layer.data[idx].uv=coord
    return obj
def curve(name, points, radius, mat, bone='head', cyclic=False):
    data=bpy.data.curves.new('Atang_'+name,'CURVE')
    data.dimensions='3D';data.resolution_u=3;data.bevel_depth=radius;data.bevel_resolution=2
    spline=data.splines.new('POLY');spline.points.add(len(points)-1)
    for p,xyz in zip(spline.points,points):p.co=(*xyz,1)
    spline.use_cyclic_u=cyclic
    obj=bpy.data.objects.new('Atang_'+name,data);C.objects.link(obj)
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    types={i.identifier for i in bpy.ops.object.convert.get_rna_type().properties['target'].enum_items}
    assert 'MESH' in types
    bpy.ops.object.convert(target='MESH')
    return register(bpy.context.object,name,mat,bone)
def bezier(points,t):
    a,b,c,d=[Vector(p) for p in points]
    return (1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d
def lock(name, control, width, thickness, mat, bone='head'):
    vertices=[];faces=[];n=24;sides=8
    for j in range(n+1):
        t=j/n;p=bezier(control,t)
        tangent=(bezier(control,min(1,t+.005))-bezier(control,max(0,t-.005))).normalized()
        normal=Vector((0,-1,0));wide=tangent.cross(normal).normalized()
        depth=wide.cross(tangent).normalized()
        taper=max(.06,math.sin(math.pi*(t*.92+.035))**.45)*(1-.5*t)
        for k in range(sides):
            a=2*math.pi*k/sides;q=p+wide*(math.cos(a)*width*taper)+depth*(math.sin(a)*thickness*taper)
            vertices.append(tuple(q))
        if j<n:
            for k in range(sides):a=j*sides+k;b=j*sides+(k+1)%sides;faces.append((a,b,b+sides,a+sides))
    faces.extend([tuple(reversed(range(sides))),tuple(n*sides+k for k in range(sides))])
    return mesh(name,vertices,faces,mat,bone)
def face_y(x,z):
    rz=(z-1.275)/.195
    jaw=.77+.23*min(1,max(0,(z-1.08)/.18))
    rx=.16*jaw
    y=-.141*math.sqrt(max(.01,1-(x/rx)**2-rz*rz))
    y-=.023*math.exp(-(x/.025)**2-((z-1.255)/.042)**2)
    y-=.006*math.exp(-(x/.05)**2-((z-1.187)/.03)**2)
    y-=.005*(math.exp(-((x-.085)/.045)**2-((z-1.235)/.045)**2)+math.exp(-((x+.085)/.045)**2-((z-1.235)/.045)**2))
    return y

import bmesh
rig=bpy.data.objects['Atang_Rig'];body=bpy.data.objects['Atang_SkinnedCharacter']
ivory=bpy.data.materials['Atang_IvoryFabric'];jade=bpy.data.materials['Atang_JadeFabric']
gold=bpy.data.materials['Atang_AnimeGold'];petal=bpy.data.materials['Atang_AnimeFlower'];green=bpy.data.materials['Atang_AnimeJade']
# Retire the old segmented blouse. Keep the fitted skirt, hands, legs and shoes.
bm=bmesh.new();bm.from_mesh(body.data)
delete=[]
for f in bm.faces:
    name=body.data.materials[f.material_index].name
    if name=='Atang_IvoryFabric' and all(v.co.z>.72 for v in f.verts):delete.append(f)
    elif name=='Atang_JadeFabric' and all(v.co.z>.82 for v in f.verts):delete.append(f)
bmesh.ops.delete(bm,geom=delete,context='FACES')
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
bm.to_mesh(body.data);bm.free()
for name,col in [('Atang_AnimeHair',(.042,.025,.019)),('Atang_AnimeHairLight',(.065,.039,.026)),('Atang_Skin',(.87,.65,.54))]:
    mat=bpy.data.materials[name];p=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=.72
# Much subtler woven material, without noisy dark stripes.
for name,col in [('Atang_IvoryFabric',(.84,.79,.68)),('Atang_RoseFabric',(.63,.36,.37)),('Atang_JadeFabric',(.16,.29,.23))]:
    mat=bpy.data.materials[name];p=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    for link in list(mat.node_tree.links):
        if link.to_socket==p.inputs['Base Color']:mat.node_tree.links.remove(link)
    p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=.88
def loft(name,rings,mat,bone,n=64):
    vs=[];fs=[];uvs=[]
    for j,(z,rx,ry,cx,cy) in enumerate(rings):
        for i in range(n):
            a=i*math.tau/n;vs.append((cx+rx*math.cos(a),cy+ry*math.sin(a),z))
        if j<len(rings)-1:
            for i in range(n):
                k=j*n+i;kn=j*n+(i+1)%n;fs.append((k,kn,kn+n,k+n))
                uvs.append(((i/n,j/(len(rings)-1)),((i+1)/n,j/(len(rings)-1)),((i+1)/n,(j+1)/(len(rings)-1)),(i/n,(j+1)/(len(rings)-1))))
    return mesh(name,vs,fs,mat,bone,uvs)
torso=loft('AnimeTailoredJacket',[(.77,.149,.108,0,0),(.82,.151,.111,0,0),(.90,.157,.101,0,0),(.99,.174,.088,0,0),(1.023,.178,.076,0,0),(1.046,.134,.063,0,0),(1.066,.054,.047,0,0)],ivory,'chest')
for v in torso.data.vertices:
    t=max(0,min(1,(v.co.z-.82)/.17))
    torso.vertex_groups['chest'].add([v.index],t,'REPLACE')
    group=torso.vertex_groups.get('spine') or torso.vertex_groups.new(name='spine');group.add([v.index],1-t,'REPLACE')
for s,side in [(1,'L'),(-1,'R')]:
    vs=[];fs=[];n=48;rows=24
    control=[(s*.13,0,1.025),(s*.20,0,1.02),(s*.23,-.007,.84),(s*.244,-.014,.739)]
    for j in range(rows+1):
        t=j/rows;p=bezier(control,t);tan=(bezier(control,min(1,t+.005))-bezier(control,max(0,t-.005))).normalized()
        width=tan.cross(Vector((0,1,0))).normalized();r=.045+.057*math.sin(t*math.pi/2)**.65
        for i in range(n):
            a=i*math.tau/n;q=p+width*(r*math.cos(a))+Vector((0,r*.8*math.sin(a),0))
            vs.append(tuple(q))
        if j<rows:
            for i in range(n):a=j*n+i;b=j*n+(i+1)%n;fs.append((a,b,b+n,a+n))
    fs.append(tuple(reversed(range(n))))
    sleeve=mesh('AnimeContinuousSleeve.'+side,vs,fs,ivory,'upper_arm.'+side)
    chest=sleeve.vertex_groups.new(name='chest');fore=sleeve.vertex_groups.new(name='forearm.'+side);upper=sleeve.vertex_groups['upper_arm.'+side]
    for v in sleeve.data.vertices:
        t=v.index//n/rows;cw=max(0,1-t/.28);fw=max(0,min(1,(t-.5)/.34));uw=(1-cw)*(1-fw)
        chest.add([v.index],cw,'REPLACE');upper.add([v.index],uw,'REPLACE');fore.add([v.index],(1-cw)*fw,'REPLACE')
# Open overcoat: a continuous ivory shell around sides/back, exposing the rose skirt.
vs=[];fs=[];rows=18;cols=72
for j in range(rows+1):
    t=j/rows;rx=.159+.117*t;ry=.119+.077*t
    for i in range(cols+1):
        a=-math.pi/2+.5+(math.tau-1)*i/cols
        z=.795-.34*t-.012*math.cos(a*4)*t
        vs.append((rx*math.cos(a),ry*math.sin(a)+.006*t,z))
    if j<rows:
        for i in range(cols):
            a=j*(cols+1)+i;fs.append((a,a+1,a+cols+2,a+cols+1))
coat=mesh('AnimeLayeredOvercoat',vs,fs,ivory,'pelvis')
for v in coat.data.vertices:
    t=max(0,min(1,(.77-v.co.z)/.32));name='skirt.L' if v.co.x>0 else 'skirt.R'
    coat.vertex_groups['pelvis'].add([v.index],1-.55*t,'REPLACE')
    g=coat.vertex_groups.get(name) or coat.vertex_groups.new(name=name);g.add([v.index],.55*t,'REPLACE')
for a in [-math.pi/2+.5,math.pi*1.5-.5]:
    pts=[]
    for j in range(25):
        t=j/24;pts.append(((.161+.117*t)*math.cos(a),(.121+.077*t)*math.sin(a),.795-.34*t-.012*math.cos(a*4)*t))
    curve('AnimeCoatBorder'+str(a),pts,.003,gold,'sash')
# Fitted crossover collar and narrow contrasting inner edge.
for s in [-1,1]:
    control=[(s*.048,-.039,1.064),(s*.080,-.080,1.031),(-s*.012,-.108,.951),(-s*.11,-.112,.824)]
    lock('AnimeCrossCollar'+str(s),control,.021,.002,jade,'chest')
    curve('AnimeCollarGold'+str(s),[tuple(bezier(control,i/32)+Vector((s*.014,-.003,0))) for i in range(33)],.0013,gold,'chest')
# A silk waist bow, jade medallion and tassel, with deliberate layered construction.
for s in [-1,1]:
    ob=uv('AnimeWaistBow'+str(s),(s*.047,-.133,.795),(.046,.012,.024),jade,'pelvis',24,12)
    ob.rotation_euler.y=s*.35
uv('AnimeWaistKnot',(0,-.144,.792),(.021,.012,.023),jade,'pelvis')
curve('AnimePendantCord',[(0,-.147,.79),(.015,-.16,.72),(.01,-.17,.665)],.0021,gold,'sash')
uv('AnimeJadeMedallion',(.01,-.173,.646),(.025,.006,.029),green,'sash',32,16)
curve('AnimeJadeRim',[(.01+.026*math.cos(i*math.tau/48),-.178,.646+.030*math.sin(i*math.tau/48)) for i in range(49)],.0018,gold,'sash',True)
for i in range(9):
    curve('AnimePendantTassel'+str(i),[(.01+(i-4)*.002,-.174,.617),(.015+(i-4)*.002,-.18,.58),(.017+(i-4)*.002,-.18,.55)],.0008,jade,'sash')
def flower(name,center,bone,size=.011):
    center=Vector(center)
    for k in range(5):
        a=k*math.tau/5
        uv(name+'Petal'+str(k),tuple(center+Vector((math.cos(a)*size*.70,-.002,math.sin(a)*size*.70))),(size*.65,.0015,size*.75),petal,bone,10,6)
    uv(name+'Gold',tuple(center+Vector((0,-.004,0))),(size*.24,.002,size*.24),gold,bone,10,6)
# Fine restrained floral embroidery on the fitted upper jacket and long coat fronts.
for s in [-1,1]:
    pts=[(s*(.10+.015*math.sin(j*.3)),-.096,.86+j*.007) for j in range(18)]
    curve('AnimeJacketStem'+str(s),pts,.0012,green,'chest')
    for k in range(3):flower('AnimeJacketBlossom'+str(s)+str(k),(s*(.10+.012*math.sin(k*2)),-.103,.88+k*.04),'chest',.009)
    for k in range(4):
        z=.49+k*.055;t=(.795-z)/.34;a=-math.pi/2+s*.67
        center=((.16+.117*t)*math.cos(a),(.12+.077*t)*math.sin(a)-.004,z)
        flower('AnimeCoatBlossom'+str(s)+str(k),center,'skirt.L' if s==1 else 'skirt.R',.011)
# Give each newly made component coherent outward normals before consolidation.
for ob in C.objects:
    if ob.type!='MESH' or ob==body:continue
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
bpy.ops.object.select_all(action='DESELECT')
for ob in C.objects:
    if ob.type=='MESH':ob.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
body.name='Atang_SkinnedCharacter';body.parent=rig
# Normalize all deform weights after the garment replacement.
for v in body.data.vertices:
    valid=[g for g in v.groups if body.vertex_groups[g.group].name in rig.data.bones]
    total=sum(g.weight for g in valid)
    if total>0:
        for g in valid:body.vertex_groups[g.group].add([v.index],g.weight/total,'REPLACE')
print('ANIME_COSTUME_READY',len(body.data.vertices),len(body.data.materials))
bpy.context.scene.render.filepath=project_path('docs/screenshots/atang-anime-v3.png')
bpy.ops.render.render(write_still=True)

