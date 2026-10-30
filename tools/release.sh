#!/usr/bin/env bash
# Publish a Wasteland Reborn release (v1.2 and later). It prints every command
# and runs nothing by default; --publish executes them.
#
#   tools/release.sh                       dry run of the next release (v1.2)
#   tools/release.sh --tag v1.3            another tag
#   tools/release.sh --publish             build, upload, publish
#   tools/release.sh --publish --skip-build        reuse apk/ and windows/dist/
#   tools/release.sh --publish --chunked           force chunked EXE uploads
#   tools/release.sh --publish --notes-file X.md   release notes of your choice
#   tools/release.sh --publish --branch main       branch the assemble workflow runs on
#
# Assets (documented in RELEASING.md): Wasteland-arm64.apk,
# Wasteland-HD-arm64.apk, WastelandReborn-Setup.exe, WastelandRebornHD-Setup.exe,
# SHA256SUMS.txt, README.txt, LISEZ-MOI.txt. An EXE is uploaded as verified
# 24 MiB chunks with .github/workflows/assemble-wasteland-release.yml when it
# exceeds GitHub's 2 GiB per-asset limit, or when --chunked asks for a resumable
# upload of a flaky connection (the workflow reassembles, verifies and publishes).
set -euo pipefail
F=$(cd "$(dirname "$0")/.." && pwd)
cd "$F"
REPO=Linutesto/wasteland-reborn-installer
TAG=v1.2
BRANCH=$(git rev-parse --abbrev-ref HEAD)
PUBLISH=0
BUILD=1
FORCE_CHUNKED=0
NOTES=
CHUNK=$((24 * 1024 * 1024))
LIMIT=$((2 * 1024 * 1024 * 1024))   # GitHub's per-asset upload limit
DIST=windows/dist

APKS=(Wasteland-arm64.apk Wasteland-HD-arm64.apk)
EXES=(WastelandReborn-Setup.exe WastelandRebornHD-Setup.exe)
DOCS=(README.txt LISEZ-MOI.txt)
CHUNKED_MANIFESTS=()

usage() { sed -n '2,18p' "$0"; }
need_value() { [ -n "${2:-}" ] || { echo "release.sh: $1 needs a value" >&2; exit 2; }; }
while [ $# -gt 0 ]; do
    case "$1" in
        --publish) PUBLISH=1 ;;
        --dry-run) PUBLISH=0 ;;
        --skip-build) BUILD=0 ;;
        --chunked) FORCE_CHUNKED=1 ;;
        --tag) need_value "$1" "${2:-}"; TAG=$2; shift ;;
        --tag=*) TAG=${1#--tag=} ;;
        --branch) need_value "$1" "${2:-}"; BRANCH=$2; shift ;;
        --branch=*) BRANCH=${1#--branch=} ;;
        --notes-file) need_value "$1" "${2:-}"; NOTES=$2; shift ;;
        --notes-file=*) NOTES=${1#--notes-file=} ;;
        -h|--help) usage; exit 0 ;;
        *) echo "release.sh: unknown argument: $1 (see --help)" >&2; exit 2 ;;
    esac
    shift
done

say() { printf '%s\n' "$*"; }
step() { printf '\n== %s\n' "$*"; }
# run <command ...>: executes it with --publish, otherwise only prints it.
run() {
    if [ "$PUBLISH" = 1 ]; then
        printf '+ '; printf '%q ' "$@"; printf '\n'
        "$@"
    else
        printf 'DRY  '; printf '%q ' "$@"; printf '\n'
    fi
}
# runs <shell string>: for pipelines and redirections.
runs() {
    if [ "$PUBLISH" = 1 ]; then
        printf '+ %s\n' "$1"
        bash -c "$1"
    else
        printf 'DRY  %s\n' "$1"
    fi
}
size_of() { stat -c %s "$1" 2>/dev/null || echo 0; }

# Split one asset into verified chunks and a manifest the assemble workflow
# understands (github-release-chunks-v1). Re-running keeps verified parts.
chunk_asset() {
    local file=$1 base stage
    base=$(basename "$file")
    stage=$DIST/.chunks-$TAG
    say "   $base: chunked upload (24 MiB parts + manifest)"
    run mkdir -p "$stage"
    if [ "$PUBLISH" = 1 ]; then
        python3 - "$file" "$stage" <<'PY'
import hashlib
import json
import os
import sys
from pathlib import Path

source, stage = Path(sys.argv[1]), Path(sys.argv[2])
stage.mkdir(parents=True, exist_ok=True)
CHUNK = 24 * 1024 * 1024

def sha256_of(path):
    digest = hashlib.sha256()
    with path.open('rb') as inp:
        while block := inp.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()

whole, parts = hashlib.sha256(), []
index = 0
with source.open('rb') as inp:
    while True:
        chunk = inp.read(CHUNK)
        if not chunk:
            break
        whole.update(chunk)
        name = f"{source.name}.part{index:03d}"
        path = stage / name
        digest = hashlib.sha256(chunk).hexdigest()
        if not (path.is_file() and path.stat().st_size == len(chunk)
                and sha256_of(path) == digest):
            temp = stage / (name + '.tmp')
            temp.write_bytes(chunk)
            os.replace(temp, path)
        parts.append({'name': name, 'size': len(chunk), 'sha256': digest})
        index += 1

document = {'format': 'github-release-chunks-v1', 'name': source.name,
            'size': source.stat().st_size, 'sha256': whole.hexdigest(),
            'chunk_size': CHUNK, 'parts': parts}
manifest = stage / f"{source.name}.manifest.json"
if manifest.exists() and json.loads(manifest.read_text()) != document:
    sys.exit(f"{manifest} belongs to an earlier build; delete {stage} and re-run")
manifest.write_text(json.dumps(document, indent=2) + '\n')
print(f"chunked {source.name}: {len(parts)} parts, {document['size']:,} bytes, "
      f"sha256 {document['sha256']}")
PY
    else
        say "DRY  split $file into 24 MiB parts under $stage/ and write $base.manifest.json"
        say "     (format github-release-chunks-v1: name, size, sha256, per-part sha256)"
    fi
    CHUNKED_MANIFESTS+=("$base.manifest.json")
    run gh release upload "$TAG" --repo "$REPO" "$stage/$base.manifest.json"
    if [ "$PUBLISH" = 1 ]; then
        run gh release upload "$TAG" --repo "$REPO" "$stage/$base".part*
    else
        say "DRY  gh release upload $TAG --repo $REPO $stage/$base.partNNN  (every part)"
    fi
}

step "1. build both editions (skip with --skip-build)"
if [ "$BUILD" = 1 ]; then
    run ./bootstrap.sh
    run ./bootstrap.sh --edition hd
    run windows/build.sh
    runs 'EDITION=hd windows/build.sh'
else
    say "   (--skip-build: using apk/ and $DIST/ as they are)"
fi

step "2. release files in $DIST/"
for name in "${APKS[@]}"; do run cp "apk/$name" "$DIST/$name"; done
for name in "${DOCS[@]}"; do run cp "windows/$name" "$DIST/$name"; done
runs "cd $DIST && sha256sum ${APKS[*]} ${EXES[*]} ${DOCS[*]} > SHA256SUMS.txt"

step "3. draft release $TAG and uploads"
if [ -n "$NOTES" ]; then
    run gh release create "$TAG" --repo "$REPO" --draft \
        --title "Wasteland Reborn ${TAG#v}" --notes-file "$NOTES"
else
    say "   (no --notes-file: the release notes are generated from the commits;"
    say "    v1.2 wants its own notes, see RELEASING.md)"
    run gh release create "$TAG" --repo "$REPO" --draft --generate-notes
fi
for name in "${APKS[@]}" "${DOCS[@]}"; do
    run gh release upload "$TAG" --repo "$REPO" "$DIST/$name"
done
for name in "${EXES[@]}"; do
    file=$DIST/$name
    if [ "$(size_of "$file")" -gt "$LIMIT" ] || [ "$FORCE_CHUNKED" = 1 ]; then
        chunk_asset "$file"
    else
        run gh release upload "$TAG" --repo "$REPO" "$file"
    fi
done
run gh release upload "$TAG" --repo "$REPO" "$DIST/SHA256SUMS.txt"

step "4. publish"
if [ "${#CHUNKED_MANIFESTS[@]}" -eq 0 ]; then
    run gh release edit "$TAG" --repo "$REPO" --draft=false --latest
else
    for manifest in "${CHUNKED_MANIFESTS[@]}"; do
        run gh workflow run assemble-wasteland-release.yml --repo "$REPO" \
            --ref "$BRANCH" -f tag="$TAG" -f manifest="$manifest"
    done
    say "   the workflow reassembles, verifies the SHA-256, publishes the release"
    say "   and deletes the chunks. Watch it with:"
    say "     gh run watch --repo $REPO && gh release view $TAG --repo $REPO"
fi

step "5. verify"
run gh release view "$TAG" --repo "$REPO" \
    --json tagName,isDraft,url,assets --jq '.tagName, .isDraft, .url, (.assets[].name)'

if [ "$PUBLISH" = 0 ]; then
    say ""
    say "Dry run: nothing was executed. Re-run with --publish to run the commands above."
fi
