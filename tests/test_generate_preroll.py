import unittest
import tempfile
import os
import ast
import types


def load_generatePreRoll():
    """Load the generatePreRoll function from Plex_Trailers.py without executing
    the rest of the script."""
    with open(os.path.join(os.path.dirname(__file__), '..', 'Plex_Trailers.py'), 'r') as f:
        source = f.read()
    tree = ast.parse(source)
    func_node = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == 'generatePreRoll':
            func_node = node
            break
    if func_node is None:
        raise RuntimeError('generatePreRoll not found')
    module = ast.Module(body=[ast.Import(names=[ast.alias(name='os', asname=None)]), func_node], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {}
    exec(compile(module, filename='generatePreRoll', mode='exec'), namespace)
    return namespace['generatePreRoll']


generatePreRoll = load_generatePreRoll()


class TestGeneratePreRoll(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.dir = self.tmpdir.name
        self.file1 = os.path.join(self.dir, "video1.mp4")
        self.file2 = os.path.join(self.dir, "video2.avi")
        self.other = os.path.join(self.dir, "note.txt")
        for path in (self.file1, self.file2, self.other):
            open(path, 'w').close()

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_file_path_returned_unchanged(self):
        result = generatePreRoll(self.file1)
        self.assertEqual(result, self.file1)

    def test_directory_returns_discovered_files(self):
        result = generatePreRoll(self.dir)
        result_set = set(filter(None, result.split(';')))
        expected = {self.file1, self.file2}
        self.assertEqual(result_set, expected)


if __name__ == '__main__':
    unittest.main()
