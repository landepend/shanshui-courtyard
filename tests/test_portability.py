"""Regression checks for clean-copy packaging and movable project paths (stdlib only)."""
import ast
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='courtyard paths ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / '庭院 project'
        for name in ['src', 'vendor', 'tools', 'assets/characters', 'assets/architecture', 'unity/Library']:
            (self.root / name).mkdir(parents=True)
        for name in ['build-single.py', 'package.py']:
            shutil.copy2(ROOT / 'tools' / name, self.root / 'tools' / name)
        for name in ['README.md', 'README.txt', 'CONTRIBUTING.md', 'AGENTS.md',
                     '.editorconfig', '.gitattributes', '.gitignore', 'start.py']:
            (self.root / name).write_text('fixture', encoding='utf-8')
        (self.root / 'index.html').write_text(
            '<script type="importmap">{}</script><script type="module" src="./src/scene.js"></script>', encoding='utf-8')
        for name in ['three.module', 'OrbitControls', 'Reflector', 'RoomEnvironment', 'BufferGeometryUtils', 'GLTFLoader']:
            (self.root / 'vendor' / (name + '.js')).write_text('// fixture', encoding='utf-8')
        for name in ['character', 'explore', 'architecture', 'scene']:
            (self.root / 'src' / (name + '.js')).write_text('// fixture', encoding='utf-8')
        doc = {'animations': [{'name': name} for name in ['Idle', 'Walk', 'Run', 'Sprint', 'Jump', 'Fall', 'Land', 'Climb', 'Glide']],
               'skins': [{'joints': list(range(25))}], 'materials': [], 'buffers': [], 'images': []}
        encoded = json.dumps(doc).encode('utf-8')
        encoded += b' ' * (-len(encoded) % 4)
        raw = struct.pack('<III', 0x46546c67, 2, 20 + len(encoded)) + struct.pack('<II', len(encoded), 0x4e4f534a) + encoded
        for name in ['characters/atang.glb', 'architecture/courtyard.glb']:
            (self.root / 'assets' / name).write_bytes(raw)
        (self.root / 'unity/Library/cache').write_text('exclude me')
        for name in ['tests/results/browser/output.txt', 'tests/results/checks/output.json',
                     '.github/workflows/project-checks.yml']:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('fixture', encoding='utf-8')

    def run_tool(self, name):
        # Deliberately launch outside the project, whose path contains spaces and Unicode.
        return subprocess.run([sys.executable, str(self.root / 'tools' / name)],
                              cwd=self.temp.name, capture_output=True, text=True)

    def test_single_file_from_clean_copy(self):
        result = self.run_tool('build-single.py')
        self.assertEqual(result.returncode, 0, result.stderr)
        html = (self.root / 'dist/shanshui-courtyard-single.html').read_text()
        self.assertIn('globalThis.__COURTYARD_GLB__=', html)
        self.assertIn('globalThis.__ATANG_GLB__=', html)
        self.assertNotIn('src="./src/scene.js"', html)

    def test_package_builds_preview_and_refreshes_stale_output(self):
        result = self.run_tool('package.py')
        self.assertEqual(result.returncode, 0, result.stderr)
        single = self.root / 'dist/shanshui-courtyard-single.html'
        first = single.read_bytes()
        (self.root / 'src/scene.js').write_text('// changed source')
        result = self.run_tool('package.py')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotEqual(first, single.read_bytes())
        with zipfile.ZipFile(self.root / 'dist/山水楼阁-Unity准备版.zip') as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(archive.read('dist/shanshui-courtyard-single.html'), single.read_bytes())
            for name in ['README.md', 'CONTRIBUTING.md', 'AGENTS.md', '.editorconfig', '.gitattributes',
                         '.gitignore', '.github/workflows/project-checks.yml',
                         'assets/characters/atang.glb', 'assets/architecture/courtyard.glb']:
                self.assertIn(name, archive.namelist())
            self.assertNotIn('unity/Library/cache', archive.namelist())
            self.assertNotIn('tests/results/browser/output.txt', archive.namelist())
            self.assertNotIn('tests/results/checks/output.json', archive.namelist())

    def test_invalid_model_keeps_previous_delivery(self):
        result = self.run_tool('package.py')
        self.assertEqual(result.returncode, 0, result.stderr)
        output = self.root / 'dist/山水楼阁-Unity准备版.zip'
        before = output.read_bytes()
        (self.root / 'assets/characters/atang.glb').write_bytes(b'invalid')
        self.assertNotEqual(self.run_tool('package.py').returncode, 0)
        self.assertEqual(output.read_bytes(), before)

    def test_archive_error_keeps_delivery_and_cleans_temporary_zip(self):
        self.assertEqual(self.run_tool('package.py').returncode, 0)
        output = self.root / 'dist/山水楼阁-Unity准备版.zip'
        before = output.read_bytes()
        (self.root / 'README.md').unlink()
        self.assertNotEqual(self.run_tool('package.py').returncode, 0)
        self.assertEqual(output.read_bytes(), before)
        self.assertEqual(list(output.parent.glob('*.zip')), [output])


class BlenderPathTests(unittest.TestCase):
    def resolver(self, filename=None, blend='', cwd=None):
        source = ROOT / 'blender/scripts/courtyard_v2/00_common.py'
        tree = ast.parse(source.read_text())
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'project_path')
        class TestPath(type(Path())):
            @classmethod
            def cwd(cls):
                return Path(cwd or tempfile.gettempdir())
        namespace = {'Path': TestPath, 'bpy': SimpleNamespace(data=SimpleNamespace(filepath=blend))}
        if filename is not None:
            namespace['__file__'] = filename
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), namespace)
        return namespace['project_path']

    def test_script_location_from_unrelated_cwd(self):
        resolve = self.resolver(filename=str(ROOT / 'blender/scripts/courtyard_v2/00_common.py'))
        self.assertEqual(Path(resolve('assets/architecture/courtyard.glb')), ROOT / 'assets/architecture/courtyard.glb')

    def test_mcp_uses_open_blend_without_file_global(self):
        resolve = self.resolver(blend=str(ROOT / 'blender/Courtyard.blend'))
        self.assertEqual(Path(resolve('blender/Atang.blend')), ROOT / 'blender/Atang.blend')

    def test_unsaved_blender_uses_project_working_directory(self):
        self.assertEqual(Path(self.resolver(cwd=ROOT)('assets')), ROOT / 'assets')

    def test_missing_project_fails_explicitly(self):
        with self.assertRaisesRegex(RuntimeError, 'Cannot locate the project'):
            self.resolver()('assets')


class MCPPathTests(unittest.TestCase):
    def test_explicit_server_with_spaces(self):
        spec = importlib.util.spec_from_file_location('unity_mcp_check', ROOT / 'tools/verify-unity-mcp.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory(prefix='MCP path ') as folder:
            executable = Path(folder) / 'mcp-for-unity'
            executable.touch()
            # Windows temp paths can use an 8.3 alias such as RUNNER~1.
            # Both spellings must identify the same executable.
            self.assertTrue(Path(module.resolve_server(str(executable))).samefile(executable))
        with self.assertRaises(FileNotFoundError):
            module.resolve_server('/nonexistent/mcp-for-unity')


if __name__ == '__main__':
    unittest.main()
