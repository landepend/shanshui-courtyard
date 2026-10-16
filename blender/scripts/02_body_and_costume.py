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

ivory=material('IvoryFabric',(.73,.69,.58),.92)
rose=material('RoseFabric',(.40,.17,.19),.9)
jade=material('JadeFabric',(.055,.18,.15),.88)
thread=material('SilkThread',(.79,.64,.45),.7)
petal=material('EmbroideredPetal',(.79,.48,.40),.88)
leaf=material('EmbroideredLeaf',(.12,.25,.17),.9)
skin=bpy.data.materials['Atang_Skin'];hair=bpy.data.materials['Atang_Hair'];gold=bpy.data.materials['Atang_Gold']
shoe=material('ClothShoes',(.035,.028,.025),.9)
sole=material('ShoeSoles',(.24,.19,.13),.97)
# Small packed weave textures; images are authored here, not downloaded.
for mat,col in [(ivory,(.73,.69,.58)),(rose,(.40,.17,.19)),(jade,(.055,.18,.15))]:
    image=bpy.data.images.new(mat.name+'_Weave',width=128,height=128,alpha=True)
    pixels=[]
    for y in range(128):
        for x in range(128):
            weave=1 + .025*math.sin(x*math.pi/2)*math.cos(y*math.pi/2)+.012*math.sin(x*.47+y*.37)
            pixels.extend([min(1,c*weave) for c in col]+[1])
    image.pixels.foreach_set(pixels);image.pack()
    shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
    mat.node_tree.links.new(tex.outputs['Color'],shader.inputs['Base Color'])
def loft(name,rings,mat,bone,n=48,pleats=0):
    vertices=[];faces=[];uvs=[]
    for j,(z,rx,ry,cx,cy) in enumerate(rings):
        t=j/(len(rings)-1)
        for i in range(n):
            a=2*math.pi*i/n;fold=1+pleats*math.cos(a*18)*(1-t)**1.2
            vertices.append((cx+rx*math.cos(a)*fold,cy+ry*math.sin(a)*fold,z))
        if j<len(rings)-1:
            for i in range(n):
                k=j*n+i;kn=j*n+(i+1)%n
                faces.append((k,kn,kn+n,k+n));uvs.append(((i/n,t),((i+1)/n,t),((i+1)/n,(j+1)/(len(rings)-1)),(i/n,(j+1)/(len(rings)-1))))
    return mesh(name,vertices,faces,mat,bone,uvs)
def weights(obj,kind,side=''):
    for g in list(obj.vertex_groups):obj.vertex_groups.remove(g)
    groups={}
    for v in obj.data.vertices:
        p=obj.matrix_world @ v.co
        if kind=='torso':
            values=blend('pelvis','spine',max(0,min(1,(p.z-.78)/.10))) if p.z<.89 else blend('spine','chest',max(0,min(1,(p.z-.89)/.10)))
        elif kind=='leg':values=blend('shin.'+side,'thigh.'+side,max(0,min(1,(p.z-.31)/.09)))
        elif kind=='sleeve':values=blend('forearm.'+side,'upper_arm.'+side,max(0,min(1,(p.z-.82)/.11)))
        else:values=skirt_weights(p)
        for name,w in values.items():
            if w>.0001:
                if name not in groups:groups[name]=obj.vertex_groups.new(name=name)
                groups[name].add([v.index],w,'REPLACE')
def blend(a,b,t):return {a:1-t,b:t}
torso=loft('TailoredBlouse',[(.77,.145,.106,0,0),(.82,.15,.11,0,0),(.9,.155,.104,0,0),(.98,.17,.091,0,0),(1.025,.174,.075,0,0),(1.065,.065,.052,0,0)],ivory,'chest')
weights(torso,'torso')
loft('Neck',[(1.045,.047,.043,0,.008),(1.10,.048,.043,0,.008),(1.145,.054,.044,0,.008)],skin,'neck',32)
rings=[]
for j in range(22):
    t=1-j/21;z=.79-.55*t;rx=.148+.143*t**.68;ry=.106+.103*t**.70
    rings.append((z,rx,ry,0,.012*t))
skirt=loft('PleatedHanfuSkirt',rings,rose,'pelvis',96,.035)
def skirt_weights(p):
    t=max(0,min(1,(.74-p.z)/.5));phi=math.atan2(p.y,p.x)
    if abs(p.x)>.11:bone='skirt.L' if p.x>0 else 'skirt.R'
    else:bone='skirt.front' if p.y<0 else 'skirt.back'
    return blend('pelvis',bone,.70*t)
weights(skirt,'skirt')
loft('WovenWaistSash',[(.768,.158,.115,0,0),(.785,.162,.118,0,0),(.817,.155,.113,0,0)],jade,'pelvis',64)
for z in [.771,.812]:
    curve('SashPiping'+str(z),[(.159*math.cos(i*2*math.pi/64),.117*math.sin(i*2*math.pi/64),z) for i in range(64)],.0024,thread,'pelvis',True)
# Fitted crossed collar with a narrow stitched border.
for side in [-1,1]:
    control=[(side*.057,-.042,1.067),(side*.115,-.072,1.027),(-side*.015,-.111,.923),(-side*.123,-.112,.805)]
    lock('CrossCollar'+str(side),control,.028,.004,jade,'chest')
    curve('CollarSeam'+str(side),[tuple(bezier(control,i/35)+Vector((side*.018,-.004,0))) for i in range(36)],.0016,thread,'chest')
for j in range(2):
    control=[(.10+j*.025,-.12,.79),(.11+j*.02,-.16,.66),(.09+j*.02,-.20,.45),(.12+j*.02,-.205,.34+j*.05)]
    lock('HangingSash'+str(j),control,.022,.003,jade,'sash')
    curve('SashStitch'+str(j),[tuple(bezier(control,i/24)+Vector((.015,-.004,0))) for i in range(25)],.001,thread,'sash')
for s in [-1,1]:
    side='L' if s>0 else 'R'
    leg=loft('Leggings.'+side,[(.095,.046,.041,s*.086,0),(.17,.047,.041,s*.086,0),(.32,.050,.047,s*.086,0),(.38,.053,.050,s*.086,0),(.52,.060,.056,s*.086,0),(.64,.064,.059,s*.086,0)],ivory,'thigh.'+side,32)
    weights(leg,'leg',side)
    loft('SockFold.'+side,[(.18,.050,.045,s*.086,0),(.193,.053,.048,s*.086,0),(.21,.050,.045,s*.086,0)],ivory,'shin.'+side,32)
    loft('Sole.'+side,[(.012,.054,.117,s*.086,-.043),(.025,.059,.121,s*.086,-.043),(.039,.058,.119,s*.086,-.043)],sole,'foot.'+side,40)
    loft('EmbroideredShoe.'+side,[(.038,.057,.115,s*.086,-.043),(.065,.060,.114,s*.086,-.044),(.095,.052,.097,s*.086,-.035),(.12,.036,.051,s*.086,-.005)],shoe,'foot.'+side,40)
    # Wide hanging sleeves, built around the shoulder-elbow-wrist path.
    vertices=[];faces=[];uvs=[];rows=20;n=40
    control=[(s*.165,0,1.025),(s*.222,0,.99),(s*.248,-.008,.82),(s*.244,-.014,.739)]
    for j in range(rows+1):
        t=j/rows;point=bezier(control,t);tangent=(bezier(control,min(1,t+.01))-bezier(control,max(0,t-.01))).normalized()
        depth=Vector((0,1,0));width=tangent.cross(depth).normalized()
        r=.070+.037*t*t
        for i in range(n):
            a=i*2*math.pi/n;fold=1+.025*math.sin(a*7)*t
            q=point+width*(r*math.cos(a)*fold)+depth*(r*.77*math.sin(a))
            vertices.append(tuple(q))
        if j<rows:
            for i in range(n):a=j*n+i;b=j*n+(i+1)%n;faces.append((a,b,b+n,a+n));uvs.append(((i/n,t),((i+1)/n,t),((i+1)/n,(j+1)/rows),(i/n,(j+1)/rows)))
    sleeve=mesh('WideSleeve.'+side,vertices,faces,ivory,'upper_arm.'+side,uvs)
    weights(sleeve,'sleeve',side)
    end=Vector(control[-1]);direction=(Vector(control[-1])-Vector(control[-2])).normalized();wide=direction.cross(Vector((0,1,0))).normalized()
    for offset in [0,.017]:
        center=end-direction*offset
        curve('CuffTrim.'+side+str(offset),[tuple(center+wide*(.107*math.cos(i*2*math.pi/48))+Vector((0,.083*math.sin(i*2*math.pi/48),0))) for i in range(48)],.006,jade,'forearm.'+side,True)
    uv('Palm.'+side,(s*.244,-.018,.69),(.033,.023,.048),skin,'hand.'+side,24,16)
    for j in range(4):
        x=s*.244+(j-1.5)*.014;z=.655-(.006 if j in [0,3] else .016)
        uv('Finger.'+side+str(j),(x,-.02,z),(.0078,.011,.025),skin,'hand.'+side,16,10)
        curve('FingerCrease.'+side+str(j),[(x-.004,-.030,z+.006),(x+.004,-.030,z+.006)],.0005,bpy.data.materials['Atang_EarInner'],'hand.'+side)
    thumb=uv('Thumb.'+side,(s*.279,-.027,.69),(.012,.016,.027),skin,'hand.'+side,16,12)
    thumb.rotation_euler.y=s*.4
# Embroidery follows the skirt surface and shares its deformation groups.
def surface(phi,z,offset=.003):
    t=max(0,min(1,(.79-z)/.55));rx=.148+.143*t**.68;ry=.106+.103*t**.70
    fold=1+.035*math.cos(phi*18)*t**1.2
    return Vector(((rx*fold+offset)*math.cos(phi),(ry*fold+offset)*math.sin(phi)+.012*t,z))
for k in range(20):
    phi=k*2*math.pi/20
    stempoints=[tuple(surface(phi+.06*math.sin(j/18*math.pi),.255+j*.125/18,.004)) for j in range(19)]
    stem=curve('PlumStem'+str(k),stempoints,.0013,leaf,'pelvis');weights(stem,'skirt')
    for j,(angle,z) in enumerate([(phi,.315),(phi+.09,.365),(phi-.065,.29)]):
        center=surface(angle,z,.006);tangent=Vector((-math.sin(angle),math.cos(angle),0))
        vs=[];fs=[]
        for pet in range(5):
            a=pet*2*math.pi/5
            c=center+tangent*(math.cos(a)*.008)+Vector((0,0,math.sin(a)*.008))
            start=len(vs);vs.append(tuple(c))
            for q in range(8):
                b=q*2*math.pi/8;p=c+tangent*(math.cos(b)*.006)+Vector((0,0,math.sin(b)*.008))
                vs.append(tuple(p))
            for q in range(8):fs.append((start,start+q+1,start+(q+1)%8+1))
        flower=mesh('SilkBlossom'+str(k)+'_'+str(j),vs,fs,petal,'pelvis');weights(flower,'skirt')
        bud=uv('FlowerStamen'+str(k)+'_'+str(j),tuple(center+Vector((math.cos(angle)*.001,math.sin(angle)*.001,0))),(.0028,.0028,.0028),thread,'pelvis',8,6);weights(bud,'skirt')
for side in ['L','R']:
    x=.086 if side=='L' else -.086
    curve('ShoeEmbroidery.'+side,[(x-.025,-.122,.074),(x-.012,-.135,.082),(x+.012,-.135,.082),(x+.025,-.122,.074)],.002,thread,'foot.'+side)
# Refinement from the turnaround: rounder jaw and larger, gently shaped eyes.
face=bpy.data.objects['Atang_SculptedFace']
for v in face.data.vertices:
    z=v.co.z
    if z<1.24:
        t=max(0,min(1,(1.24-z)/.16))
        v.co.x*=1+.08*t
        v.co.z+=.018*t*t
for s in [-1,1]:
    cx=s*.066
    for prefix in ['AlmondEye','UpperLid','LowerLid']:
        o=bpy.data.objects.get('Atang_'+prefix+str(s))
        if o:
            for v in o.data.vertices:
                x,z=v.co.x,v.co.z
                v.co.x=cx+(x-cx)*1.06
                v.co.z=1.294+(z-1.294)*1.28
                v.co.y=face_y(v.co.x,v.co.z)-(.006 if prefix!='AlmondEye' else .005)
    for prefix in ['Iris','Pupil','EyeGlint','EyeGlintSmall']:
        o=bpy.data.objects.get('Atang_'+prefix+str(s))
        if o:o.scale.x*=1.22;o.scale.z*=1.22
concept=bpy.data.images.load(project_path('assets/concepts/atang-turnaround-v1.png'),check_existing=True)
concept.name='Atang_Concept_Turnaround';concept.use_fake_user=True;concept.pack()
print('BODY_AND_CLOTH_COMPLETE',len(C.objects),'objects',sum(len(o.data.vertices) for o in C.objects if o.type=='MESH'),'vertices before consolidation')

