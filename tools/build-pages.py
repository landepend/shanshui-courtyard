"""Build the browser preview for Pages without changing the shared GLB assets."""
import json
from pathlib import Path
import shutil
import struct

ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_BYTES = 25 * 1024 * 1024
BUFFER_BYTES = 16 * 1024 * 1024
MODEL = 'assets/architecture/courtyard.glb'


def split_model(source, destination, buffer_bytes=BUFFER_BYTES):
    """Repack embedded buffer views losslessly into bounded, local glTF buffers."""
    raw = source.read_bytes()
    if len(raw) < 20 or struct.unpack_from('<III', raw) != (0x46546C67, 2, len(raw)):
        raise ValueError('Invalid GLB header')
    json_size, json_kind = struct.unpack_from('<II', raw, 12)
    binary_header = 20 + json_size
    if json_kind != 0x4E4F534A or binary_header + 8 > len(raw):
        raise ValueError('Expected GLB JSON and BIN chunks')
    binary_size, binary_kind = struct.unpack_from('<II', raw, binary_header)
    binary = raw[binary_header + 8:]
    doc = json.loads(raw[20:binary_header])
    buffers = doc.get('buffers', [])
    if (binary_kind != 0x004E4942 or binary_size != len(binary)
            or len(buffers) != 1 or 'uri' in buffers[0]
            or not 0 <= len(binary) - buffers[0]['byteLength'] <= 3):
        raise ValueError('Expected one embedded GLB buffer')
    if doc.get('extensionsUsed') or any('uri' in image for image in doc.get('images', [])):
        raise ValueError('Pages repacking requires an embedded model without glTF extensions')

    chunks = [bytearray()]
    for view in doc['bufferViews']:
        start, size = view.get('byteOffset', 0), view['byteLength']
        if (view.get('buffer', 0) != 0 or start < 0 or size <= 0
                or start + size > buffers[0]['byteLength']):
            raise ValueError('Invalid embedded buffer view')
        if size > buffer_bytes:
            raise ValueError('A model buffer view exceeds the Pages buffer budget')
        chunk = chunks[-1]
        padding = -len(chunk) % 4
        if len(chunk) + padding + size > buffer_bytes:
            chunks.append(bytearray())
            chunk, padding = chunks[-1], 0
        chunk.extend(b'\x00' * padding)
        view['buffer'] = len(chunks) - 1
        view['byteOffset'] = len(chunk)
        chunk.extend(binary[start:start + size])

    destination.parent.mkdir(parents=True, exist_ok=True)
    doc['buffers'] = []
    for index, chunk in enumerate(chunks):
        name = f'{destination.stem}-{index}.bin'
        (destination.parent / name).write_bytes(chunk)
        doc['buffers'].append({'uri': name, 'byteLength': len(chunk)})
    destination.write_text(json.dumps(doc, ensure_ascii=False, separators=(',', ':')) + '\n',
                           encoding='utf-8')


def build(root=ROOT):
    output = root / 'dist/pages'
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    shutil.copy2(root / 'index.html', output / 'index.html')
    for folder in ['src', 'vendor']:
        shutil.copytree(root / folder, output / folder,
                        ignore=shutil.ignore_patterns('__pycache__', '.DS_Store'))
    character = Path('assets/characters/atang.glb')
    (output / character).parent.mkdir(parents=True)
    shutil.copy2(root / character, output / character)
    split_model(root / MODEL, (output / MODEL).with_suffix('.gltf'))

    # Only the generated module uses the publishing format; source/offline keep GLB.
    module = output / 'src/architecture.js'
    source = module.read_text(encoding='utf-8')
    if source.count('../' + MODEL) != 1:
        raise ValueError('Expected one architecture model URL in src/architecture.js')
    model_url = '../' + Path(MODEL).with_suffix('.gltf').as_posix()
    module.write_text(source.replace('../' + MODEL, model_url),
                      encoding='utf-8')
    files = [path for path in output.rglob('*') if path.is_file()]
    for path in files:
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError(f'Pages asset exceeds 25 MiB: {path.relative_to(output)}')
    largest = max(files, key=lambda path: path.stat().st_size)
    print(f'Built Pages preview: {output} ({len(files)} files)')
    print(f'Largest asset: {largest.relative_to(output)} ({largest.stat().st_size} bytes)')
    return output


if __name__ == '__main__':
    build()
