import unittest
import tempfile
import os
import ast
import textwrap
from unittest import mock


def load_namespace():
    names = ['getArguments', 'generatePreRoll', 'getConfig', 'main']
    path = os.path.join(os.path.dirname(__file__), '..', 'Plex_Trailers.py')
    with open(path, 'r') as f:
        tree = ast.parse(f.read())
    func_nodes = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            func_nodes[node.name] = node
    module = ast.Module(body=[
        ast.Import(names=[ast.alias(name='os', asname=None)]),
        ast.ImportFrom(module='configparser', names=[ast.alias(name='ConfigParser', asname=None)], level=0),
        ast.ImportFrom(module='datetime', names=[ast.alias(name='datetime', asname=None)], level=0),
    ] + [func_nodes[name] for name in names if name in func_nodes], type_ignores=[])
    ast.fix_missing_locations(module)
    ns = {}
    exec(compile(module, filename='Plex_Trailers', mode='exec'), ns)
    return ns


class TestGetConfig(unittest.TestCase):
    def setUp(self):
        self.ns = load_namespace()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.tmpdir.name, 'config.ini')
        self.ns['__file__'] = os.path.join(self.tmpdir.name, 'Plex_Trailers.py')

    def tearDown(self):
        self.tmpdir.cleanup()

    def write_config(self, content):
        with open(self.config_path, 'w') as f:
            f.write(textwrap.dedent(content))

    def test_get_config_returns_expected_values(self):
        self.write_config('''
            [SERVER]
            plex_url = http://example.com
            plex_token = token123

            [PATHS]
            host_dir = /host
            docker_dir = /docker

            [MONTHS]
            Jan = /docker/jan/preroll.mp4
        ''')
        cfg = self.ns['getConfig']()
        self.assertEqual(cfg['plex_url'], 'http://example.com')
        self.assertEqual(cfg['plex_token'], 'token123')
        # Month keys are lowercased by ConfigParser
        self.assertIn('jan', cfg)
        self.assertEqual(cfg['jan'], '/docker/jan/preroll.mp4')


class TestMain(unittest.TestCase):
    def setUp(self):
        self.ns = load_namespace()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.ns['__file__'] = os.path.join(self.tmpdir.name, 'Plex_Trailers.py')
        with open(os.path.join(self.tmpdir.name, 'config.ini'), 'w') as f:
            f.write(textwrap.dedent('''
                [SERVER]
                plex_url = http://example.com
                plex_token = token

                [PATHS]
                host_dir = /host

                [MONTHS]
                Jan = /docker/preroll.mp4
            '''))

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_main_updates_preroll_setting(self):
        # Stub out unused argument handling
        self.ns['getArguments'] = lambda: None

        # Patch datetime to return January
        base_dt = self.ns['datetime']
        class DummyDate(base_dt):
            @classmethod
            def today(cls):
                return cls(2024, 1, 5)
        self.ns['datetime'] = DummyDate

        # Mock PlexServer
        plex_instance = mock.MagicMock()
        plex_server_mock = mock.MagicMock(return_value=plex_instance)
        self.ns['PlexServer'] = plex_server_mock

        # Minimal requests stub
        class DummyRequests:
            class packages:
                class urllib3:
                    @staticmethod
                    def disable_warnings():
                        pass
            def Session(self):
                class S: pass
                s = S(); s.verify = False; return s
        self.ns['requests'] = DummyRequests()

        self.ns['main']()

        plex_instance.settings.get.return_value.set.assert_called_with('/docker/preroll.mp4')
        plex_instance.settings.save.assert_called_once()


if __name__ == '__main__':
    unittest.main()
