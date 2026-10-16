"""Ensure the project gate rejects damaged assets and unsynchronized copies."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('project_checks', ROOT / 'tools/check-project.py')
CHECKS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKS)


def model_document():
    return {
        'asset': {'version': '2.0'},
        'buffers': [{'byteLength': 4}],
        'meshes': [{'primitives': []}],
        'animations': [{'name': name} for name in sorted(CHECKS.ANIMATIONS)],
        'skins': [{'joints': list(range(25))}],
        'nodes': [{'extras': {'part': part}} for part in sorted(CHECKS.PARTS)],
    }


def encode_glb(doc):
    encoded = json.dumps(doc).encode('utf-8')
    encoded += b' ' * (-len(encoded) % 4)
    chunks = struct.pack('<II', len(encoded), 0x4E4F534A) + encoded
    chunks += struct.pack('<II', 4, 0x004E4942) + b'\x00' * 4
    return struct.pack('<III', 0x46546C67, 2, 12 + len(chunks)) + chunks


class ProjectGateTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix='courtyard gate ')
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.source = self.root / 'source.glb'
        self.doc = model_document()
        self.source.write_bytes(encode_glb(self.doc))

    def test_valid_embedded_container_and_contracts(self):
        doc = CHECKS.read_glb(self.source)
        CHECKS.validate_contract(doc, 'character')
        CHECKS.validate_contract(doc, 'architecture')

    def test_corrupt_or_truncated_container_fails(self):
        original = self.source.read_bytes()
        for raw in [b'bad', original[:-1], b'XXXX' + original[4:]]:
            with self.subTest(length=len(raw)):
                self.source.write_bytes(raw)
                with self.assertRaises(ValueError):
                    CHECKS.read_glb(self.source)

    def test_chunk_claiming_more_than_available_fails(self):
        raw = bytearray(self.source.read_bytes())
        struct.pack_into('<I', raw, 12, len(raw) * 4)
        self.source.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, 'chunk size'):
            CHECKS.read_glb(self.source)

    def test_external_resource_fails(self):
        for field, value in [('buffers', [{'uri': 'remote.bin', 'byteLength': 4}]),
                             ('images', [{'uri': 'texture.png'}])]:
            with self.subTest(field=field):
                doc = copy.deepcopy(self.doc)
                doc[field] = value
                self.source.write_bytes(encode_glb(doc))
                with self.assertRaises(ValueError):
                    CHECKS.read_glb(self.source)

    def test_animation_and_skeleton_regressions_fail(self):
        for field, value in [('animations', self.doc['animations'][:-1]),
                             ('animations', self.doc['animations'] + [self.doc['animations'][0]]),
                             ('skins', [{'joints': [0] * 25}]),
                             ('skins', [{'joints': list(range(25)) + [0]}])]:
            with self.subTest(field=field):
                doc = copy.deepcopy(self.doc)
                doc[field] = value
                with self.assertRaises(ValueError):
                    CHECKS.validate_contract(doc, 'character')

    def test_missing_building_part_fails(self):
        self.doc['nodes'].pop()
        with self.assertRaisesRegex(ValueError, 'Missing architecture parts'):
            CHECKS.validate_contract(self.doc, 'architecture')

    def test_stale_unity_copy_fails(self):
        target = self.root / 'unity.glb'
        target.write_bytes(self.source.read_bytes())
        CHECKS.check_model_pair(self.root, 'source.glb', 'unity.glb', 'character')
        target.write_bytes(b'stale model')
        with self.assertRaisesRegex(ValueError, 'Unity copy differs'):
            CHECKS.check_model_pair(self.root, 'source.glb', 'unity.glb', 'character')


if __name__ == '__main__':
    unittest.main()
