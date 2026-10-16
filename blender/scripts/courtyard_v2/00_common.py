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

# All design coordinates are x/elevation/z, matching the game. A rigid rotation
# (x, -z, elevation) gives Blender Z-up; glTF export restores game Y-up.
SCENE_NAME = 'COURTYARD_V2'
COLLECTION_NAME = 'COURTYARD_ARCHITECTURE'
OUT = project_path('') + '/'
B = {}
PALETTE = {
    'wood': ('4B2C23', .78, 0), 'woodLight': ('76503B', .76, 0),
    'red': ('963C2D', .51, 0), 'redLight': ('B8593D', .58, 0),
    'gold': ('C4A268', .34, .55), 'goldDark': ('927145', .49, .40),
    'stone': ('AEADA0', .91, 0), 'stoneDark': ('777F77', .95, 0),
    'wall': ('D5CCB4', .94, 0), 'paper': ('C8B991', .85, 0),
    'jade': ('87AAA0', .30, .05), 'ink': ('2A423C', .82, 0),
    'tile0': ('47615D', .65, .05), 'tile1': ('536C65', .62, .05),
    'tile2': ('3C5553', .71, .03), 'tile3': ('5E756B', .67, .04),
    'tileDark': ('304744', .85, 0), 'linen': ('A0A084', .96, 0)
}

def material(key):
    name = 'CV2_' + key
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        m.use_nodes = True
    hx, rough, metal = PALETTE[key]
    rgb = [int(hx[i:i+2], 16) / 255 for i in (0,2,4)]
    linear = [v / 12.92 if v < .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
    bs = next((node for node in m.node_tree.nodes if node.type == 'BSDF_PRINCIPLED'), None)
    if bs is None:
        bs = m.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    bs.inputs['Base Color'].default_value = (*linear, 1)
    bs.inputs['Roughness'].default_value = rough
    bs.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*linear, 1)
    return m

def setup():
    s = bpy.data.scenes.get(SCENE_NAME)
    if s is None:
        s = bpy.data.scenes.new(SCENE_NAME)
    bpy.context.window.scene = s
    c = bpy.data.collections.get(COLLECTION_NAME)
    if c is None:
        c = bpy.data.collections.new(COLLECTION_NAME)
    if c.name not in s.collection.children:
        s.collection.children.link(c)
    r = bpy.data.objects.get('CourtyardRoot')
    if r is None:
        r = bpy.data.objects.new('CourtyardRoot', None)
        c.objects.link(r)
    r['assetVersion'] = 'courtyard-anime-v2'
    r['coordinateSystem'] = 'glTF Y-up; source Blender (x,-z,y)'
    return s, c, r

S, C, ROOT = setup()

def mesh_add(part, mat, verts, faces):
    key = (part, mat)
    if key not in B:
        B[key] = [[], []]
    vv, ff = B[key]
    n = len(vv)
    vv.extend(verts)
    ff.extend([tuple(n+i for i in face) for face in faces])

def box(part, mat, center, size):
    x,y,z=center; a,b,c=[v*.5 for v in size]
    v=[(x-a,y-b,z-c),(x+a,y-b,z-c),(x+a,y+b,z-c),(x-a,y+b,z-c),
       (x-a,y-b,z+c),(x+a,y-b,z+c),(x+a,y+b,z+c),(x-a,y+b,z+c)]
    mesh_add(part,mat,v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)])

def beam(part, mat, a, b, width, depth=None):
    depth = width if depth is None else depth
    aa,bb=Vector(a),Vector(b)
    d=bb-aa
    if d.length < .00001:
        return
    d.normalize()
    ref=Vector((0,1,0)) if abs(d.y)<.95 else Vector((0,0,1))
    u=d.cross(ref).normalized()*width*.5
    v=d.cross(u).normalized()*depth*.5
    verts=[tuple(p+su*u+sv*v) for p in (aa,bb) for su,sv in [(-1,-1),(1,-1),(1,1),(-1,1)]]
    mesh_add(part,mat,verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])

def tube(part, mat, pts, radius, sides=8, radii=None, cap=True):
    p=[Vector(v) for v in pts]; verts=[]; faces=[]
    for i,q in enumerate(p):
        d=p[min(i+1,len(p)-1)]-p[max(0,i-1)]
        d.normalize()
        ref=Vector((0,1,0)) if abs(d.y)<.93 else Vector((0,0,1))
        u=d.cross(ref).normalized(); v=d.cross(u).normalized()
        r=radius if radii is None else radii[i]
        for j in range(sides):
            a=j*math.tau/sides
            verts.append(tuple(q+r*(math.cos(a)*u+math.sin(a)*v)))
        if i:
            for j in range(sides):
                k=(i-1)*sides+j; nn=(j+1)%sides
                faces.append((k,(i-1)*sides+nn,i*sides+nn,i*sides+j))
    if cap:
        faces.extend([tuple(reversed(range(sides))),tuple((len(p)-1)*sides+j for j in range(sides))])
    mesh_add(part,mat,verts,faces)

def cyl(part, mat, x,y,z,r,h,sides=16,rtop=None):
    tube(part,mat,[(x,y-h*.5,z),(x,y+h*.5,z)],r,sides,[r,r if rtop is None else rtop])

def lathe(part,mat,x,y,z,profile,sides=16):
    verts=[]; faces=[]
    for h,r in profile:
        for j in range(sides):
            t=j*math.tau/sides
            verts.append((x+math.cos(t)*r,y+h,z+math.sin(t)*r))
    for i in range(len(profile)-1):
        for j in range(sides):
            a=i*sides+j; b=i*sides+(j+1)%sides
            faces.append((a,b,b+sides,a+sides))
    faces.extend([tuple(reversed(range(sides))),tuple((len(profile)-1)*sides+j for j in range(sides))])
    mesh_add(part,mat,verts,faces)

def prism(part,mat,poly,depth,axis='z',offset=0):
    # Planar outlined solid; poly is an ordered (horizontal,elevation) loop.
    v=[]
    for side in [-1,1]:
        for a,y in poly:
            v.append((a,y,offset+side*depth*.5) if axis=='z' else (offset+side*depth*.5,y,a))
    n=len(poly); faces=[tuple(reversed(range(n))),tuple(range(n,n*2))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    mesh_add(part,mat,v,faces)

def flush(stage):
    for ob in list(C.objects):
        if ob.get('stage')==stage:
            old=ob.data
            bpy.data.objects.remove(ob,do_unlink=True)
            if old and old.users==0:
                bpy.data.meshes.remove(old)
    count=0; tris=0
    for (part,mat),(vv,ff) in B.items():
        name='CV2_'+stage+'_'+part+'_'+mat
        me=bpy.data.meshes.new(name)
        me.from_pydata([(x,-z,y) for x,y,z in vv],[],ff)
        me.materials.append(material(mat))
        me.update()
        ob=bpy.data.objects.new(name,me); C.objects.link(ob); ob.parent=ROOT
        ob['part']=part; ob['stage']=stage
        ob['source']='Blender modeled solid geometry'
        count+=1; tris+=sum(max(0,len(f)-2) for f in ff)
    B.clear()
    print('COURTYARD_STAGE',stage,'meshes',count,'triangles',tris)

def column(x,z,floor,height,part='column',radius=.185):
    base_bottom=.82 if part=='column' and abs(floor-1.04)<.001 else floor
    base_top=floor+.11
    box(part,'stoneDark',(x,(base_top+base_bottom)*.5,z),(.66,base_top-base_bottom,.66))
    lathe(part,'stone',x,floor+.10,z,[(0,.31),(.07,.31),(.10,.245),(.17,.23),(.24,.255),(.28,.235)],20)
    lathe(part,'red',x,floor+.36,z,[(0,radius*1.06),(height*.35,radius),(height*.8,radius*.94),(height,radius*.89)],20)
    for yy in [floor+.37,floor+.44,floor+height+.27]:
        cyl(part,'goldDark',x,yy,z,radius*1.08,.035,20)
    lathe(part,'wood',x,floor+height+.30,z,[(0,radius*1.12),(.06,radius*1.12),(.10,radius*1.40)],16)

def curved_bracket(x,y,z,L,axis='x',mat='red',part='dougong',thickness=.13):
    poly=[]
    for i in range(13):
        t=-1+2*i/12
        poly.append((L*.5*t,y+.07+.16*abs(t)**2))
    for i in range(12,-1,-1):
        t=-1+2*i/12
        poly.append((L*.5*t,y-.075+.22*abs(t)**2))
    if axis=='x':
        prism(part,mat,[(a+x,b) for a,b in poly],thickness,'z',z)
    else:
        prism(part,mat,[(a+z,b) for a,b in poly],thickness,'x',x)

def dougong(x,y,z,scale=1,part='dougong'):
    box(part,'wood',(x,y,z),(.44*scale,.21*scale,.44*scale))
    box(part,'goldDark',(x,y+.105*scale,z),(.40*scale,.035*scale,.40*scale))
    for lev in range(3):
        yy=y+(.20+lev*.225)*scale; ll=(.68+lev*.34)*scale
        for axis in ['x','z']:
            curved_bracket(x,yy,z,ll,axis,'red' if lev%2==0 else 'woodLight',part,.145*scale)
            for sg in [-1,1]:
                xx=x+sg*ll*.43 if axis=='x' else x
                zz=z+sg*ll*.43 if axis=='z' else z
                box(part,'wood',(xx,yy+.17*scale,zz),(.23*scale,.13*scale,.23*scale))
                box(part,'gold',(xx,yy+.23*scale,zz),(.205*scale,.025*scale,.205*scale))
        # Slanted ang between stacked bracket tiers.
        for sg in [-1,1]:
            beam(part,'red',(x,y+.22*scale,z),(x,y+(.43+lev*.19)*scale,z+sg*(.31+lev*.20)*scale),.095*scale,.15*scale)

def rail(a,b,y,part='column',opening=None):
    a,b=Vector(a),Vector(b); length=(b-a).length
    n=max(1,round(length/.68))
    for yy,w in [(y+.18,.075),(y+.62,.07),(y+.89,.11)]:
        aa=a.copy();bb=b.copy();aa.y=bb.y=yy;beam(part,'red',aa,bb,w,.10)
    for i in range(n+1):
        p=a.lerp(b,i/n)
        box(part,'wood',(p.x,y+.53,p.z),(.075,.80,.075))
        if i<n:
            q=a.lerp(b,(i+.5)/n)
            # Rotated lozenge motif is actual openwork.
            tangent=(b-a).normalized(); center=Vector((q.x,y+.43,q.z))
            points=[center+tangent*.17,center+Vector((0,.15,0)),center-tangent*.17,center-Vector((0,.15,0)),center+tangent*.17]
            tube(part,'goldDark',points,.018,5)

def frame_window(x,y,z,width,height,rot=0,paper=True,part='window'):
    # Coordinates local to a vertical window, rotated around elevation axis.
    co=math.cos(rot);si=math.sin(rot)
    def p(a,b,c): return (x+a*co+c*si,y+b,z-a*si+c*co)
    def wb(mat,a,b,c,w,h,d):
        aa=p(a-w*.5,b,c);bb=p(a+w*.5,b,c)
        beam(part,mat,aa,bb,d,h)
    if paper: wb('paper',0,0,-.06,width,height,.035)
    for sx in [-1,1]:
        wb('red',sx*width*.5,0,0,.105,height+.16,.12)
        wb('goldDark',sx*(width*.5-.075),0,.069,.018,height,.014)
    for sy in [-1,1]:
        wb('wood',0,sy*height*.5,0,width+.12,.11,.14)
        wb('gold',0,sy*(height*.5-.075),.078,width-.05,.018,.018)
    cols=max(3,round(width/.29)); rows=max(3,round(height/.33))
    for i in range(1,cols): wb('wood',-width*.5+width*i/cols,0,.045,.030,height-.08,.053)
    for j in range(1,rows): wb('wood',0,-height*.5+height*j/rows,.045,width-.08,.031,.053)
    for i in range(cols):
        for j in range(rows):
            if (i+j)%2: continue
            cx=-width*.5+width*(i+.5)/cols;cy=-height*.5+height*(j+.5)/rows
            pts=[p(cx-.085,cy,.079),p(cx,cy+.105,.079),p(cx+.085,cy,.079),p(cx,cy-.105,.079),p(cx-.085,cy,.079)]
            tube(part,'goldDark',pts,.011,4)

def carved_beam(a,b,y,part='column'):
    aa=Vector(a);bb=Vector(b);aa.y=bb.y=y
    beam(part,'wood',aa,bb,.24,.30)
    for dy in [-.11,.11]:
        p=aa.copy();q=bb.copy();p.y+=dy;q.y+=dy
        beam(part,'goldDark',p,q,.265,.024)
    direction=(bb-aa).normalized();length=(bb-aa).length
    normal=direction.cross(Vector((0,1,0))).normalized()
    for i in range(max(1,int(length/.60))):
        p=aa.lerp(bb,(i+.5)/max(1,int(length/.60)))+normal*.129
        pts=[]
        for k in range(17):
            t=k*math.tau/16
            pts.append(tuple(p+direction*(.19*math.cos(t))+Vector((0,.072*math.sin(2*t),0))))
        tube(part,'gold',pts,.013,5)

def roof_point(a,b,r,h,base,side,u,t):
    expand=max(0,(t-.38)/.62)
    span=r+(a-r)*expand
    lift=.29*t**8+.64*abs(u)**8*t**5
    yy=base+h*max(0,1-t)**1.62+lift
    if side<2: return Vector((u*span,yy,(1 if side==0 else -1)*b*t))
    return Vector(((1 if side==2 else -1)*span,yy,u*b*t))

def roof_geometry(a,b,h,base,part='roof',hole=0,origin=(0,0,0),rot=0,density=1):
    # Native solid half-cylinder tile shells lie on the curved hip/gable patches.
    # Neither displacement textures nor flat repeated roof boxes are used.
    co=math.cos(rot);si=math.sin(rot)
    def tr(p):
        x,y,z=p
        return (origin[0]+x*co+z*si,origin[1]+y,origin[2]-x*si+z*co)
    r=a*(.51 if hole else .64)
    count=0
    for side in range(4):
        t0=max(hole,.38) if side>=2 else hole
        nu=40 if part=='roof' else 22;nt=20 if part=='roof' else 10
        vv=[];ff=[]
        for j in range(nt+1):
            t=t0+(1-t0)*j/nt
            for i in range(nu+1):
                p=roof_point(a,b,r,h,base,side,-1+2*i/nu,t)
                vv.append(tr(p))
        for j in range(nt):
            for i in range(nu):
                k=j*(nu+1)+i;ff.append((k,k+1,k+nu+2,k+nu+1))
        mesh_add(part,'tileDark',vv,ff)
        # Thickness and underside edge follow the same roof outline.
        edge=[roof_point(a,b,r,h,base,side,-1+2*i/48,1) for i in range(49)]
        tube(part,'wood',[tr(p+Vector((0,-.095,0))) for p in edge],.093,8)
        tube(part,'red',[tr(p+Vector((0,-.190,0))) for p in edge],.055,8)
        tube(part,'goldDark',[tr(p+Vector((0,-.014,0))) for p in edge],.023,6)
        # Tile courses overlap down the pitch, with alternated glazed tones.
        slope_len=math.hypot(b,h) if side<2 else math.hypot(a-r,h*.6)
        rows=max(3,math.ceil(slope_len*(1-t0)/(.34/density)))
        dt=(1-t0)/rows
        for j in range(rows):
            t=t0+(j+.5)*dt
            span=r+(a-r)*max(0,(t-.38)/.62) if side<2 else b*t
            cols=max(3,math.ceil(2*span/(.235/density)))
            width=2*span/cols
            for i in range(cols):
                u=-1+2*(i+.5)/cols
                p=roof_point(a,b,r,h,base,side,u,t)
                du=(roof_point(a,b,r,h,base,side,u+.001,t)-p).normalized()
                dv=(roof_point(a,b,r,h,base,side,u,t+.001)-p).normalized()
                normal=dv.cross(du).normalized()
                if normal.y<0:normal=-normal
                rr=width*.49;segs=5;v=[];faces=[]
                for shell in range(2):
                    for end in range(2):
                        tt=max(t0-.015,min(1.014,t+(-.61 if end==0 else .61)*dt))
                        pp=roof_point(a,b,r,h,base,side,u,tt)
                        radius=rr-shell*.014
                        for k in range(segs+1):
                            theta=k*math.pi/segs
                            q=pp+du*(math.cos(theta)*radius)+normal*(.020+math.sin(theta)*radius)
                            v.append(tr(q))
                ring=segs+1
                for shell in range(2):
                    for k in range(segs):
                        idx=shell*ring*2+k
                        faces.append((idx,idx+1,idx+ring+1,idx+ring))
                for end in range(2):
                    for k in range(segs):
                        idx=end*ring+k
                        faces.append((idx,idx+ring*2,idx+ring*2+1,idx+1))
                for k in [0,segs]:faces.append((k,k+ring,k+ring*3,k+ring*2))
                mesh_add(part,'tile'+str((i*7+j*3+side)%4),v,faces)
                count+=1
                if j==rows-1:
                    # Circular eave-end discs, center boss and petal incision.
                    ep=roof_point(a,b,r,h,base,side,u,1.015)
                    tangent=(roof_point(a,b,r,h,base,side,u,1.016)-ep).normalized()
                    center=ep+normal*.032
                    tube(part,'tile1',[tr(center-tangent*.025),tr(center+tangent*.025)],rr*.96,10)
                    tube(part,'goldDark',[tr(center+tangent*.028),tr(center+tangent*.044)],rr*.30,7)
        # Visible projecting rafters under the eave and gold carved terminal ends.
        span=a if side<2 else b
        nr=max(5,round(span*2/.34))
        for i in range(nr+1):
            u=-1+2*i/nr
            ps=[]
            for j in range(7):
                tt=.69+j*.31/6
                ps.append(tr(roof_point(a,b,r,h,base,side,u,tt)+Vector((0,-.19,0))))
            tube(part,'woodLight',ps,.044,7)
            tube(part,'goldDark',ps[-2:],.049,6)
        # Hip ridge tiles and curved edge fascia rising into the corner.
        for sg in [-1,1]:
            pts=[roof_point(a,b,r,h,base,side,sg,t0+(1-t0)*i/24) for i in range(25)]
            tube(part,'tileDark',[tr(p+Vector((0,.085,0))) for p in pts],.105,8)
            tube(part,'goldDark',[tr(p+Vector((0,.164,0))) for p in pts],.026,6)
    if not hole:
        # Ridge crest, sculpted fish/chiwen silhouettes, and open gable trusses.
        tube(part,'tileDark',[tr((-r,base+h+.10,0)),tr((0,base+h+.16,0)),tr((r,base+h+.10,0))],.16,10)
        tube(part,'goldDark',[tr((-r,base+h+.23,0)),tr((0,base+h+.28,0)),tr((r,base+h+.23,0))],.033,7)
        for sg in [-1,1]:
            pts=[]
            for i in range(21):
                t=i/20
                pts.append(tr((sg*(r+.14+.33*math.sin(t*math.pi*.8)),base+h+.10+.88*t,0)))
            tube(part,'goldDark',pts,.10,10,radii=[.135-.067*i/20 for i in range(21)])
            curl=[]
            for i in range(25):
                t=i*math.pi*1.5/24; rr=.21*(1-i/32)
                curl.append(tr((sg*(r+.34+rr*math.cos(t)),base+h+.91+rr*math.sin(t),0)))
            tube(part,'gold',curl,.039,7)
            # Paired ribbed fins along the sculptural spine.
            for j in range(7):
                t=.16+j*.085
                x=sg*(r+.14+.33*math.sin(t*math.pi*.8)); yy=base+h+.10+.88*t
                beam(part,'goldDark',tr((x,yy,0)),tr((x-sg*(.18+.07*math.sin(t*4)),yy+.18,0)),.055,.07)
            gy=base+h*(.62**1.62)
            gpoly=[(0,base+h-.12)]
            for i in range(1,13):
                tt=.38*i/12;gpoly.append((b*tt,base+h*(1-tt)**1.62-.10))
            gpoly.append((-b*.38,gy-.10))
            for i in range(11,0,-1):
                tt=.38*i/12;gpoly.append((-b*tt,base+h*(1-tt)**1.62-.10))
            # The gable is a closed extruded polygon, rotated with the roof.
            v=[]
            for dx in [-.05,.05]:
                v.extend(tr((sg*r+dx,yy,zz)) for zz,yy in gpoly)
            nn=len(gpoly);f=[tuple(reversed(range(nn))),tuple(range(nn,2*nn))]
            f.extend((i,(i+1)%nn,(i+1)%nn+nn,i+nn) for i in range(nn))
            mesh_add(part,'wood',v,f)
            for side_z in [-1,1]:
                pts=[tr((sg*(r+.071),base+h*(1-.38*i/16)**1.62-.02,side_z*b*.38*i/16)) for i in range(17)]
                tube(part,'goldDark',pts,.038,7)
            for j in range(-5,6):
                zz=j*b*.061; top=base+h*(1-abs(zz)/b)**1.62-.15
                beam(part,'red',tr((sg*(r+.075),gy,zz)),tr((sg*(r+.075),top,zz)),.050,.050)
    return count
