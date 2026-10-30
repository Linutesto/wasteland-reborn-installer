# Tests for linux/install.py: detection, VDF paths, config edits and exact manifest removal.
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from linux import install

class LinuxTests(unittest.TestCase):
    def test_detection(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            roots = [home / '.steam/steam', home / '.var/app/com.valvesoftware.Steam/.local/share/Steam']
            for root in roots:
                game = root / 'steamapps/common/Fallout 2'
                game.mkdir(parents=True)
                (game / 'MASTER.DAT').write_text('m')
                (game / 'CRITTER.DAT').write_text('c')
                self.assertEqual(install.game_dir(game), game)
            self.assertEqual(install.find_game(home), roots[0] / 'steamapps/common/Fallout 2')
            heroic = home / 'Games/Heroic/Fallout 2'; heroic.mkdir(parents=True)
            (heroic / 'master.dat').write_text('m'); (heroic / 'critter.dat').write_text('c')
            for root in roots:
                for p in (root / 'steamapps/common/Fallout 2').iterdir(): p.unlink()
            self.assertEqual(install.find_game(home), heroic)

    def test_lutris_prefix_and_heroic_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            prefix = home / '.local/share/lutris/games/gog-fallout'
            game = prefix / 'drive_c/GOG Games/Fallout 2'
            game.mkdir(parents=True)
            (game / 'master.dat').write_text('m'); (game / 'critter.dat').write_text('c')
            self.assertEqual(install.find_game(home), game)
            for p in game.iterdir(): p.unlink()
            heroic = home / 'custom/Heroic/Fallout 2'; heroic.mkdir(parents=True)
            (heroic / 'master.dat').write_text('m'); (heroic / 'critter.dat').write_text('c')
            meta = home / '.config/heroic/GamesConfig/123.json'; meta.parent.mkdir(parents=True)
            meta.write_text(json.dumps({'install': {'install_path': str(heroic)}}))
            self.assertEqual(install.find_game(home), heroic)

    def test_case_insensitive_music(self):
        with tempfile.TemporaryDirectory() as d:
            music = Path(d) / 'DATA/SOUND/MUSIC'
            music.mkdir(parents=True)
            self.assertEqual(install.case_path(d, 'data/sound/music'), music)

    def test_vdf_extra_library(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d); lib = home / 'other library'
            vdf = home / '.steam/steam/steamapps/libraryfolders.vdf'
            vdf.parent.mkdir(parents=True)
            vdf.write_text('"libraryfolders" { "0" { "path" "' + str(lib) + '" } }')
            game = lib / 'steamapps/common/Fallout 2'; game.mkdir(parents=True)
            (game / 'master.dat').write_text('m'); (game / 'critter.dat').write_text('c')
            self.assertEqual(install.find_game(home), game)

    def test_config_and_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d); config = base / 'fallout2.cfg'
            config.write_text('[ai]\nenabled=0\n[graphics]\ndark_boost=2\n')
            install.cfg_set(config, 'ai', 'enabled', '1')
            install.cfg_set(config, 'graphics', 'hd_art', '1')
            install.cfg_set(config, 'graphics', 'hd_art', '1')
            self.assertEqual(config.read_text().count('hd_art=1'), 1)
            self.assertIn('enabled=1', config.read_text())
            prefix = base / 'installed'; prefix.mkdir()
            owned = prefix / 'owned'; owned.write_text('owned')
            changed = prefix / 'changed'; changed.write_text('old')
            save = prefix / 'savegame'; save.write_text('save')
            (prefix / '.install-manifest.json').write_text(json.dumps({'files': {
                str(owned): install.digest(owned), str(changed): install.digest(changed)}}))
            changed.write_text('new')
            with patch('pathlib.Path.home', return_value=base):
                install.uninstall(prefix)
            self.assertFalse(owned.exists())
            self.assertTrue(changed.exists())
            self.assertTrue(save.exists())
            self.assertFalse((prefix / '.install-manifest.json').exists())

if __name__ == '__main__': unittest.main()
