"""Offline tests of the interactive/NSIS-silent Windows configuration paths."""
import json
import sys
import tempfile
import types
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'setup'))
import setup  # noqa: E402


class UnattendedSetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.game = root / 'installed/game'
        self.game.mkdir(parents=True)
        (self.game / 'fallout2.cfg').write_text('[system]\n[ai]\nenabled=1\n', encoding='latin-1')
        self.userdata = root / 'installed/userdata'
        self.edition = root / 'edition.json'
        self.edition.write_text(json.dumps({'edition': 'hd'}))
        for attr, value in (('GAME', self.game), ('USERDATA', self.userdata),
                            ('EDITION_FILE', self.edition)):
            patcher = mock.patch.object(setup, attr, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        # common.py owns the actual settings and token paths.
        import common
        for attr, value in (('GAME', self.game), ('USERDATA', self.userdata),
                            ('SETTINGS', self.userdata / 'settings.json'),
                            ('TOKEN', self.userdata / 'token')):
            patcher = mock.patch.object(common, attr, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_no_fallout_does_not_download_or_create_token(self):
        with mock.patch.object(setup, 'find_game', return_value=None), \
             mock.patch.object(setup, 'setup_hd_art') as hd:
            self.assertEqual(setup.unattended_main(), 0)
        hd.assert_not_called()
        self.assertIn('Fallout 2 not found', (self.userdata / 'setup-install.log').read_text())
        self.assertFalse((self.userdata / 'token').exists())

    def test_hd_download_failure_is_logged_and_game_remains_playable(self):
        source = Path(self.tmp.name) / 'gog/Fallout 2'
        source.mkdir(parents=True)
        (source / 'master.dat').write_bytes(b'fixture-master')
        (source / 'critter.dat').write_bytes(b'fixture-critter')
        entrypoint = types.ModuleType('wasteland_hd.__main__')
        entrypoint.ASSETS = 'https://example.invalid/packs.json'
        entrypoint.cmd_install = mock.Mock(side_effect=urllib.error.URLError('offline'))
        with mock.patch.dict(sys.modules, {'wasteland_hd': types.ModuleType('wasteland_hd'),
                                           'wasteland_hd.__main__': entrypoint}), \
             mock.patch.object(setup, 'find_game', return_value=source), \
             mock.patch.object(setup, 'ollama_models', side_effect=AssertionError('should not poll Ollama')):
            self.assertEqual(setup.unattended_main(), 0)
        entrypoint.cmd_install.assert_called_once()
        self.assertEqual((self.game / 'master.dat').read_bytes(), b'fixture-master')
        self.assertEqual((self.game / 'critter.dat').read_bytes(), b'fixture-critter')
        self.assertIn('enabled=0', (self.game / 'fallout2.cfg').read_text())
        log = (self.userdata / 'setup-install.log').read_text()
        self.assertIn('HD packs unavailable for now:', log)
        self.assertIn('Run setup again', log)
        self.assertIn('Game setup complete', log)
        self.assertNotIn((self.userdata / 'token').read_text().strip(), log)

    def test_hd_art_rejects_missing_base_game(self):
        with mock.patch.dict(sys.modules, {'wasteland_hd.__main__': types.ModuleType('wasteland_hd.__main__')}):
            with mock.patch.object(setup, 'yes', side_effect=AssertionError('must not prompt')):
                setup.setup_hd_art(unattended=True)

    def test_missing_hd_art_module_keeps_installer_running(self):
        (self.game / 'master.dat').write_bytes(b'master')
        (self.game / 'critter.dat').write_bytes(b'critter')
        with mock.patch.dict(sys.modules, {'wasteland_hd.__main__': None}), \
             mock.patch.object(setup, 'yes', side_effect=AssertionError('must not prompt')):
            setup.setup_hd_art(unattended=True)

    def test_normal_never_attempts_hd_art(self):
        self.edition.unlink()
        source = Path(self.tmp.name) / 'steam/Fallout 2'
        source.mkdir(parents=True)
        (source / 'master.dat').write_bytes(b'master')
        (source / 'critter.dat').write_bytes(b'critter')
        with mock.patch.object(setup, 'find_game', return_value=source), \
             mock.patch.object(setup, 'setup_hd_art', wraps=setup.setup_hd_art) as hd:
            self.assertEqual(setup.unattended_main(), 0)
        hd.assert_called_once_with(unattended=True)
        self.assertTrue((self.game / 'master.dat').exists())
        self.assertNotIn('HD art (optional)', (self.userdata / 'setup-install.log').read_text())


if __name__ == '__main__':
    unittest.main()
