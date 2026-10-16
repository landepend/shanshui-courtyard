"""Verify publishing preserves model bytes and respects Pages file limits."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('pages_build', ROOT / 'tools/build-pages.py')
PAGES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PAGES)


def read_model(path):
    raw = path.read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + size]), raw[28 + size:]


class PagesBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='Pages 庭院 project ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'project'
        self.root.mkdir()

    def test_repack_preserves_every_view_and_model_metadata(self):
        source = ROOT / PAGES.MODEL
        before, binary = read_model(source)
        destination = self.root / 'courtyard.gltf'
        PAGES.split_model(source, destination)
        after = json.loads(destination.read_text(encoding='utf-8'))
        chunks = [(self.root / buffer['uri']).read_bytes() for buffer in after['buffers']]
        self.assertGreater(len(chunks), 1)
        for buffer, chunk in zip(after['buffers'], chunks):
            self.assertEqual(buffer['byteLength'], len(chunk))
            self.assertLessEqual(len(chunk), PAGES.BUFFER_BYTES)
        for original, packed in zip(before['bufferViews'], after['bufferViews']):
            start = original.get('byteOffset', 0)
            offset = packed['byteOffset']
            size = original['byteLength']
            self.assertEqual(offset % 4, 0)
            self.assertEqual(binary[start:start + size],
                             chunks[packed['buffer']][offset:offset + size])
        restored = copy.deepcopy(after)
        restored['buffers'] = before['buffers']
        for original, packed in zip(before['bufferViews'], restored['bufferViews']):
            for field in ['buffer', 'byteOffset']:
                if field in original:
                    packed[field] = original[field]
                else:
                    packed.pop(field, None)
        self.assertEqual(before, restored)  # Includes part tags, materials, accessors and axes.

    def test_cli_build_from_other_directory_and_cleans_stale_files(self):
        for folder in ['src', 'vendor', 'assets/architecture', 'assets/characters', 'tools']:
            (self.root / folder).mkdir(parents=True, exist_ok=True)
        for name in ['index.html', 'src/architecture.js', PAGES.MODEL,
                     'assets/characters/atang.glb', 'tools/build-pages.py']:
            shutil.copy2(ROOT / name, self.root / name)
        output = self.root / 'dist/pages'
        output.mkdir(parents=True)
        (output / 'stale.glb').write_bytes(b'stale')
        (self.root / 'dist/keep.html').write_text('other delivery', encoding='utf-8')
        result = subprocess.run([sys.executable, str(self.root / 'tools/build-pages.py')],
                                cwd=self.temp.name, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((output / 'stale.glb').exists())
        self.assertFalse((output / PAGES.MODEL).exists())
        self.assertFalse((output / 'unity').exists())
        self.assertFalse((output / 'tools').exists())
        self.assertTrue((output / 'index.html').exists())
        self.assertTrue((output / 'assets/characters/atang.glb').exists())
        self.assertEqual((self.root / 'dist/keep.html').read_text(), 'other delivery')
        self.assertIn('courtyard.gltf', (output / 'src/architecture.js').read_text())
        self.assertEqual((self.root / 'src/architecture.js').read_bytes(),
                         (ROOT / 'src/architecture.js').read_bytes())
        for path in output.rglob('*'):
            if path.is_file():
                self.assertLessEqual(path.stat().st_size, PAGES.MAX_FILE_BYTES)

    def test_oversized_buffer_view_fails_explicitly(self):
        with self.assertRaisesRegex(ValueError, 'buffer view exceeds'):
            PAGES.split_model(ROOT / PAGES.MODEL, self.root / 'courtyard.gltf', buffer_bytes=4)

    def test_unexpected_loader_url_fails_instead_of_shipping_missing_model(self):
        for folder in ['src', 'vendor', 'assets/architecture', 'assets/characters']:
            (self.root / folder).mkdir(parents=True, exist_ok=True)
        for name in ['index.html', PAGES.MODEL, 'assets/characters/atang.glb']:
            shutil.copy2(ROOT / name, self.root / name)
        (self.root / 'src/architecture.js').write_text('// no model URL', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Expected one architecture model URL'):
            PAGES.build(self.root)


if __name__ == '__main__':
    unittest.main()
