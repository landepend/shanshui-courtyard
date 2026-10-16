from pathlib import Path
import zipfile,json,struct,hashlib,subprocess,sys,tempfile,os,re
root=Path(__file__).resolve().parents[1]
raw=(root/'assets/characters/atang.glb').read_bytes()
magic,version,length=struct.unpack_from('<III',raw)
assert magic==0x46546c67 and version==2 and length==len(raw)
chunk_length,chunk_type=struct.unpack_from('<II',raw,12)
doc=json.loads(raw[20:20+chunk_length])
clips=[a['name'] for a in doc['animations']]
assert set(clips)=={'Idle','Walk','Run','Sprint','Jump','Fall','Land','Climb','Glide'},clips
assert len(doc['skins'])==1 and len(doc['skins'][0]['joints'])==25
assert all('bufferView' in image for image in doc.get('images',[]))
assert all('uri' not in b for b in doc['buffers'])
report={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'bones':len(doc['skins'][0]['joints']),'animations':clips,'materials':len(doc['materials']),'embeddedImages':len(doc.get('images',[]))}
(root/'tests/results').mkdir(parents=True,exist_ok=True)
(root/'tests/results/model-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
# Rebuild from current sources instead of shipping an older preview.
subprocess.run([sys.executable,str(root/'tools/build-single.py')],check=True)
out=root/'dist/山水楼阁-Unity准备版.zip'
excluded={'__pycache__','library','temp','obj','logs','usersettings','node_modules','.venv','.vs','build','builds'}
# A failed package must leave any previous delivery intact.
with tempfile.NamedTemporaryFile(dir=out.parent,suffix='.zip',delete=False) as temp:
    temporary=Path(temp.name)
try:
    with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name in ['src','assets','blender','docs','tests','tools','vendor','unity','.github']:
            for p in sorted((root/name).rglob('*')):
                relative=p.relative_to(root)
                if (p.is_file() and not any(part.lower() in excluded for part in relative.parts)
                    and relative.parts[:3] not in {('tests','results','browser'),('tests','results','checks')}
                    and not re.search(r'\.blend\d+$',p.name)
                    and p.suffix.lower() not in {'.pyc','.log','.csproj','.sln','.key','.pem'}
                    and p.name not in {'.DS_Store','Thumbs.db'} and not p.name.startswith('.env')):
                    z.write(p,relative)
        for name in ['index.html','README.md','README.txt','CONTRIBUTING.md','AGENTS.md',
                     '.editorconfig','.gitattributes','.gitignore','start.py','dist/shanshui-courtyard-single.html']:
            z.write(root/name,name)
    with zipfile.ZipFile(temporary) as z:
        assert z.testzip() is None
        assert 'assets/characters/atang.glb' in z.namelist()
    os.replace(temporary,out)
finally:
    temporary.unlink(missing_ok=True)
print(json.dumps(report))
print('Package:',out,out.stat().st_size,'bytes')

