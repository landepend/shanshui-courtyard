"""Rebuild the self-contained offline HTML from the editable project sources."""
from pathlib import Path
import base64, json, re
root=Path(__file__).resolve().parents[1]
def read(path):return (root/path).read_text(encoding='utf-8-sig')
def uri(code):return 'data:text/javascript;base64,'+base64.b64encode(code.encode('utf-8')).decode('ascii')
imports={'three':uri(read('vendor/three.module.js'))}
for name in ['OrbitControls','Reflector','RoomEnvironment']:
    imports['three/addons/'+name+'.js']=uri(read('vendor/'+name+'.js'))
imports['geometry-utils']=uri(read('vendor/BufferGeometryUtils.js'))
imports['gltf-loader']=uri(read('vendor/GLTFLoader.js').replace('./BufferGeometryUtils.js','geometry-utils'))
imports['character']=uri(read('src/character.js').replace('../vendor/GLTFLoader.js','gltf-loader'))
imports['explore']=uri(read('src/explore.js').replace('./character.js','character'))
imports['architecture']=uri(read('src/architecture.js').replace('../vendor/GLTFLoader.js','gltf-loader'))
scene=read('src/scene.js').replace('./explore.js','explore').replace('./architecture.js','architecture')
html=read('index.html')
html=re.sub(r'<script type="importmap">[\s\S]*?</script>','<script type="importmap">'+json.dumps({'imports':imports})+'</script>',html)
model=base64.b64encode((root/'assets/characters/atang.glb').read_bytes()).decode('ascii')
architecture=base64.b64encode((root/'assets/architecture/courtyard.glb').read_bytes()).decode('ascii')
html=html.replace('<script type="module" src="./src/scene.js"></script>','<script>globalThis.__COURTYARD_GLB__="'+architecture+'";globalThis.__ATANG_GLB__="'+model+'";</script><script type="module" src="'+uri(scene)+'"></script>')
out=root/'dist/shanshui-courtyard-single.html'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html,encoding='utf-8')
assert './src/scene.js' not in html
print('Built offline single HTML:',out, out.stat().st_size,'bytes')

