#!/usr/bin/env python3
"""Builds the game profile Wasteland Reborn ships (RPU + FO2Tweaks), without
any of Fallout 2's own files.

Usage:
    mkprofile.py [--dest build/profile] [--no-download]

profile/manifest.json lists the mods with their source URL and the sha256 of
the archive. Archives are cached under mods-cache/<id>/ and extracted once.
The profile gets each mod's files, then the mod's documented Linux installer
script (RPU's rpu-install.sh) runs inside it, then profile/fallout2.cfg and
profile/overlay/ go over it. The player's master.dat, critter.dat and music
are added by the Windows setup (or imported in the phone app) from their own
copy of the game.
"""

from wasteland_locations import write_locations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECIPE = os.path.join(ROOT, "profile")
CACHE = os.path.join(ROOT, "mods-cache")


def log(msg):
    print(f"[mkprofile] {msg}", flush=True)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(mod, no_download):
    d = os.path.join(CACHE, mod["id"])
    os.makedirs(d, exist_ok=True)
    archive = os.path.join(d, mod["archive"])
    if not os.path.exists(archive):
        if no_download:
            sys.exit(f"missing archive {archive} (--no-download)")
        log(f"downloading {mod['source_url']}")
        tmp = archive + ".part"
        with urllib.request.urlopen(mod["source_url"]) as r, open(tmp, "wb") as f:
            shutil.copyfileobj(r, f, 1 << 20)
        os.replace(tmp, archive)
    got = sha256(archive)
    if got != mod["sha256"]:
        sys.exit(f"sha256 mismatch for {archive}: got {got}, manifest says {mod['sha256']}")
    log(f"ok {mod['archive']} sha256={got[:16]}...")
    return archive


def safe_rel(name):
    name = name.replace("\\", "/")
    parts = [p for p in name.split("/") if p not in ("", ".")]
    if name.startswith("/") or ".." in parts:
        sys.exit(f"refusing unsafe archive path: {name}")
    return "/".join(parts)


def extract(mod, archive):
    """Extracts once into mods-cache/<id>/extracted."""
    out = os.path.join(CACHE, mod["id"], "extracted")
    stamp = os.path.join(CACHE, mod["id"], ".extracted-sha256")
    if os.path.isdir(out) and os.path.exists(stamp) and open(stamp).read().strip() == mod["sha256"]:
        return out
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(out)
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            rel = safe_rel(info.filename)
            if not rel:
                continue
            dst = os.path.join(out, rel)
            if info.is_dir():
                os.makedirs(dst, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with z.open(info) as src, open(dst, "wb") as f:
                shutil.copyfileobj(src, f, 1 << 20)
    with open(stamp, "w") as f:
        f.write(mod["sha256"] + "\n")
    log(f"extracted {mod['archive']}")
    return out


def copy_tree(src_root, dest, skip=()):
    n = 0
    for dirpath, _dirs, files in os.walk(src_root):
        for fn in files:
            src = os.path.join(dirpath, fn)
            rel = os.path.relpath(src, src_root)
            if rel.replace(os.sep, "/").lower() in skip:
                continue
            dst = os.path.join(dest, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.lexists(dst):
                os.unlink(dst)
            shutil.copy2(src, dst)
            n += 1
    return n


def build(dest, no_download):
    with open(os.path.join(RECIPE, "manifest.json")) as f:
        m = json.load(f)
    staged = [(mod, extract(mod, fetch(mod, no_download))) for mod in m["mods"]]

    if os.path.exists(dest):
        shutil.rmtree(dest)
    for d in ("data/savegame", "data/sound/music", "mods"):
        os.makedirs(os.path.join(dest, d))

    for mod, staging in staged:
        skip = {safe_rel(s).lower() for s in mod.get("skip_files", [])}
        log(f"{mod['id']}: placed {copy_tree(staging, dest, skip)} files")
        script = mod.get("installer")
        if script:
            log(f"{mod['id']}: running documented installer {script}")
            r = subprocess.run(["bash", script], cwd=dest, capture_output=True, text=True)
            sys.stdout.write(r.stdout)
            sys.stderr.write(r.stderr)
            if r.returncode != 0:
                sys.exit(f"{script} failed with {r.returncode}")

    shutil.copy2(os.path.join(RECIPE, "fallout2.cfg"), os.path.join(dest, "fallout2.cfg"))
    log(f"overlay: {copy_tree(os.path.join(RECIPE, 'overlay'), dest)} files")
    write_locations(dest, "fallout2")
    log(f"done: {dest}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=os.path.join(ROOT, "build", "profile"))
    ap.add_argument("--no-download", action="store_true")
    args = ap.parse_args()
    build(os.path.abspath(args.dest), args.no_download)
