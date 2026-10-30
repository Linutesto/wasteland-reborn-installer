"""Offline regression tests for the Windows installer -> Android payload."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'setup'))
import phone  # noqa: E402


class PhonePayloadTests(unittest.TestCase):
    def test_hd_profile_contains_all_rpu_directories_and_skips_saves(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp) / 'game'
            for relative in ('master.dat', 'critter.dat', 'fallout2.cfg',
                             'mods/mod.txt', 'appearance/appearance.txt',
                             'translations/translation.txt', 'data/hd/test.png',
                             'data/savegame/SLOT01/SAVE.DAT', 'ce.dat'):
                path = game / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('[system]\n\n[graphics]\n' if relative == 'fallout2.cfg' else 'fixture')

            sent = {}

            def fake_push(source, remote):
                source = Path(source)
                sent[source.name] = (str(remote), source.read_text() if source.is_file() else '')
                return True

            def fake_adb(*args, **_kwargs):
                if args[:3] == ('shell', 'getprop', 'ro.product.cpu.abi'):
                    return 'arm64-v8a'
                if args[:2] == ('install', '-r'):
                    return 'Success'
                return ''

            with mock.patch.object(phone, 'GAME', game), \
                 mock.patch.object(phone, 'EDITION', {'edition': 'hd'}), \
                 mock.patch.object(phone, 'find_adb', return_value='adb'), \
                 mock.patch.object(phone, 'choose_phone', return_value='test-serial'), \
                 mock.patch.object(phone, 'adb', side_effect=fake_adb), \
                 mock.patch.object(phone, 'push', side_effect=fake_push), \
                 mock.patch.object(phone, 'lan_ip', return_value='127.0.0.1'), \
                 mock.patch.object(phone, 'load_settings', return_value={}), \
                 mock.patch.object(phone, 'save_settings'), \
                 mock.patch.object(phone, 'title'), \
                 mock.patch.object(phone.os, 'system'), \
                 mock.patch.object(phone.time, 'sleep'):
                self.assertEqual(phone.run(interactive_end=False), 'done')

            for name in ('mods', 'appearance', 'translations'):
                self.assertIn(name, sent)
                self.assertTrue(sent[name][0].endswith('/profiles/rpu-plus/'))
            self.assertIn('hd', sent)
            self.assertNotIn('savegame', sent)
            config = sent['fallout2.cfg'][1]
            for key in ('hd_art=1', 'hd_cache_mb=256', 'dark_boost=2'):
                self.assertIn(key, config)

    def test_classic_profile_does_not_force_hd(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp)
            (game / 'fallout2.cfg').write_text('[system]\n[graphics]\n')
            target = game / 'phone.cfg'
            with mock.patch.object(phone, 'GAME', game), \
                 mock.patch.object(phone, 'EDITION', {}), \
                 mock.patch.object(phone, 'lan_ip', return_value='127.0.0.1'):
                phone.phone_cfg(target, {})
            self.assertNotIn('hd_art=', target.read_text())


if __name__ == '__main__':
    unittest.main()
