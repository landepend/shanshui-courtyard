"""Dependency-free project checks; needs Node.js for JavaScript syntax only."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ANIMATIONS = {'Idle', 'Walk', 'Run', 'Sprint', 'Jump', 'Fall', 'Land', 'Climb', 'Glide'}
PARTS = {'roof', 'dougong', 'column', 'window', 'corridor'}
MODEL_PAIRS = (
    ('assets/characters/atang.glb', 'unity/Assets/Art/Characters/atang.glb', 'character'),
    ('assets/architecture/courtyard.glb', 'unity/Assets/Art/Architecture/courtyard.glb', 'architecture'),
)


def read_glb(path):
    """Check the GLB container before reading its embedded glTF JSON."""
    raw = path.read_bytes()
    if len(raw) < 20:
        raise ValueError('GLB header is truncated')
    magic, version, length = struct.unpack_from('<III', raw)
    if magic != 0x46546C67 or version != 2 or length != len(raw):
        raise ValueError('Invalid GLB magic, version or file length')
    offset, chunks = 12, []
    while offset < len(raw):
        if offset + 8 > len(raw):
            raise ValueError('Truncated GLB chunk header')
        size, kind = struct.unpack_from('<II', raw, offset)
        offset += 8
        if size % 4 or offset + size > len(raw):
            raise ValueError('Invalid GLB chunk size')
        chunks.append((kind, raw[offset:offset + size]))
        offset += size
    if not chunks or chunks[0][0] != 0x4E4F534A:
        raise ValueError('First GLB chunk must contain JSON')
    if len(chunks) > 2 or (len(chunks) == 2 and chunks[1][0] != 0x004E4942):
        raise ValueError('Expected JSON followed by an optional BIN chunk')
    doc = json.loads(chunks[0][1].decode('utf-8'))
    if doc.get('asset', {}).get('version') != '2.0':
        raise ValueError('Expected glTF asset version 2.0')
    buffers = doc.get('buffers', [])
    if len(buffers) != 1 or 'uri' in buffers[0]:
        raise ValueError('Expected one embedded GLB buffer')
    declared = buffers[0].get('byteLength')
    if (len(chunks) != 2 or not isinstance(declared, int) or declared <= 0
            or not 0 <= len(chunks[1][1]) - declared <= 3):
        raise ValueError('Embedded buffer length does not match BIN chunk')
    if any('uri' in image or 'bufferView' not in image for image in doc.get('images', [])):
        raise ValueError('Textures must be embedded in GLB buffer views')
    return doc


def validate_contract(doc, kind):
    if not doc.get('meshes'):
        raise ValueError('Model has no meshes')
    if kind == 'character':
        clips = [clip.get('name') for clip in doc.get('animations', [])]
        if len(clips) != len(ANIMATIONS) or set(clips) != ANIMATIONS:
            raise ValueError('Character must contain all nine named animations exactly once')
        skins = doc.get('skins', [])
        if (len(skins) != 1 or len(skins[0].get('joints', [])) != 25
                or len(set(skins[0]['joints'])) != 25):
            raise ValueError('Character must contain one skin with 25 unique joints')
    elif kind == 'architecture':
        parts = {node.get('extras', {}).get('part') for node in doc.get('nodes', [])}
        missing = PARTS - parts
        if missing:
            raise ValueError('Missing architecture parts: ' + ', '.join(sorted(missing)))
    else:
        raise ValueError('Unknown model kind: ' + kind)


def check_model_pair(root, source, target, kind):
    validate_contract(read_glb(root / source), kind)
    source_hash = hashlib.sha256((root / source).read_bytes()).digest()
    target_hash = hashlib.sha256((root / target).read_bytes()).digest()
    if source_hash != target_hash:
        raise ValueError('Unity copy differs; run tools/sync-unity-assets.ps1 -RequireArchitecture')


def source_files(root, folders, pattern):
    return sorted(path for folder in folders for path in (root / folder).rglob(pattern)
                  if '__pycache__' not in path.parts)


def main():
    failures = []
    counts = {'python': 0, 'javascript': 0, 'json': 0, 'models': 0}

    def run(label, operation):
        try:
            operation()
        except (OSError, ValueError, SyntaxError, TypeError, KeyError, subprocess.SubprocessError) as error:
            failures.append(f'{label}: {error}')

    for path in [ROOT / 'start.py', *source_files(ROOT, ['tools', 'blender/scripts', 'tests'], '*.py')]:
        run(str(path.relative_to(ROOT)), lambda p=path: ast.parse(p.read_text(encoding='utf-8-sig'), filename=str(p)))
        counts['python'] += 1

    node = shutil.which('node')
    if node is None:
        failures.append('Node.js is required for JavaScript syntax checks; install Node.js 24')
    else:
        for path in source_files(ROOT, ['src', 'tests/browser', 'vendor'], '*.js'):
            def check_javascript(p=path):
                result = subprocess.run(
                    [node, '--input-type=module', '--check'], input=p.read_text(encoding='utf-8-sig'),
                    encoding='utf-8', capture_output=True, timeout=30, check=False)
                if result.returncode:
                    raise ValueError(result.stderr.strip())
            run(str(path.relative_to(ROOT)), check_javascript)
            counts['javascript'] += 1

    for path in source_files(ROOT, ['docs', 'tests', 'unity/Packages'], '*.json'):
        if path.is_relative_to(ROOT / 'tests/results/browser') or path.is_relative_to(ROOT / 'tests/results/checks'):
            continue
        run(str(path.relative_to(ROOT)), lambda p=path: json.loads(p.read_text(encoding='utf-8-sig')))
        counts['json'] += 1

    for source, target, kind in MODEL_PAIRS:
        run(source, lambda s=source, t=target, k=kind: check_model_pair(ROOT, s, t, k))
        counts['models'] += 1

    print('Checked: ' + ', '.join(f'{count} {kind}' for kind, count in counts.items()))
    if failures:
        for failure in failures:
            print('FAIL ' + failure, file=sys.stderr)
        return 1
    print('PASS project checks (static checks only; Unity and browser runtime not tested)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
