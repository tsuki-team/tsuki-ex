#!/usr/bin/env python3
"""
tsuki-ex pkg manager
====================
Manages the pkg/ directory for board packages and keeps packages.json in sync.

Usage
-----
  python pkg_manager.py list                       # list all board packages
  python pkg_manager.py validate                   # validate every package
  python pkg_manager.py sync                       # rebuild packages.json from disk
  python pkg_manager.py new <id> [--version 1.0.0] [--desc "..."] [--arch esp32]
  python pkg_manager.py bump <id> <new-version>    # bump version, scaffold new dir

All commands read/write relative to the repo root (one level up from tools/).
"""

import argparse
import json
import os
import re
import shutil
import sys
import textwrap
from pathlib import Path
from typing import Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # pip install tomli
    except ImportError:
        tomllib = None  # type: ignore


# ── Paths ─────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent.resolve()   # <repo>/tools
REPO_ROOT  = SCRIPT_DIR.parent                 # <repo>
PKG_DIR    = REPO_ROOT / 'pkg'                 # <repo>/pkg

GITHUB_RAW_BASE = "https://raw.githubusercontent.com/tsuki-team/tsuki-ex/refs/heads"
MANIFEST_NAME   = "tsuki_board.toml"


def _check_pkg_dir() -> None:
    if not PKG_DIR.exists():
        print(f"[error] pkg/ directory not found at: {PKG_DIR}", file=sys.stderr)
        sys.exit(1)


def _detect_branch() -> str:
    if env := os.environ.get("TSUKI_BRANCH", "").strip():
        return env
    try:
        import subprocess as _sp
        result = _sp.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=5,
        )
        branch = result.stdout.strip()
        if result.returncode == 0 and branch and branch != "HEAD":
            return branch
    except Exception:
        pass
    return "main"


def _registry_url(branch: str | None = None) -> str:
    b = branch or _detect_branch()
    return f"{GITHUB_RAW_BASE}/{b}/pkg"


# ── TOML helpers ──────────────────────────────────────────────────────────────

def read_board_toml(path: Path) -> dict:
    """Parse a tsuki_board.toml, returning a flat dict with all top-level keys."""
    if tomllib is None:
        # Minimal regex fallback — reads [board] and [toolchain] sections
        text = path.read_text(encoding='utf-8')
        result: dict = {}
        current_section = None
        for line in text.splitlines():
            m_section = re.match(r'^\[(\w+)\]', line)
            if m_section:
                current_section = m_section.group(1)
                continue
            m_kv = re.match(r'(\w+)\s*=\s*"([^"]*)"\s*$', line)
            if m_kv and current_section in ('board', 'toolchain', None):
                result[m_kv.group(1)] = m_kv.group(2)
        return result

    with open(path, 'rb') as f:
        raw = tomllib.load(f)

    # Merge [board] fields up to top level for easy access
    flat = {}
    if 'board' in raw:
        flat.update(raw['board'])
    for k, v in raw.items():
        if k != 'board':
            flat[k] = v
    return flat


# ── Package discovery ─────────────────────────────────────────────────────────

def iter_packages():
    """Yield (id, version, toml_path) for every board package on disk."""
    if not PKG_DIR.exists():
        return
    for pkg_dir in sorted(PKG_DIR.iterdir()):
        if not pkg_dir.is_dir() or pkg_dir.name.startswith('.'):
            continue
        for ver_dir in sorted(pkg_dir.iterdir()):
            if not ver_dir.is_dir():
                continue
            toml = ver_dir / MANIFEST_NAME
            if toml.exists():
                yield pkg_dir.name, ver_dir.name, toml


def latest_version(pkg_id: str) -> Optional[tuple]:
    versions = [(ver, toml) for id_, ver, toml in iter_packages() if id_ == pkg_id]
    return sorted(versions)[-1] if versions else None


# ── Registry builder ──────────────────────────────────────────────────────────

def build_registry(branch: str | None = None) -> dict:
    registry_url = _registry_url(branch)
    registry: dict = {"packages": {}, "branch": branch or _detect_branch()}

    all_versions: dict = {}
    for id_, ver, toml_path in iter_packages():
        all_versions.setdefault(id_, {})[ver] = toml_path

    for pkg_id, versions in sorted(all_versions.items()):
        latest_ver = sorted(versions.keys())[-1]
        data = read_board_toml(versions[latest_ver])

        clean_ver   = latest_ver.lstrip('v')
        description = data.get('description', f'{pkg_id} board package')
        author      = data.get('author', 'tsuki-ex')
        arch        = data.get('type', '')   # [toolchain] type = "esp32" etc.
        category    = 'wifi' if arch in ('esp32', 'esp8266') else 'basic'

        version_urls = {}
        for ver, path in versions.items():
            clean = ver.lstrip('v')
            version_urls[clean] = f"{registry_url}/{pkg_id}/{ver}/{MANIFEST_NAME}"

        registry['packages'][pkg_id] = {
            'type':        'board',
            'description': description,
            'author':      author,
            'arch':        arch,
            'category':    category,
            'latest':      clean_ver,
            'versions':    version_urls,
        }

    return registry


# ── Validation ────────────────────────────────────────────────────────────────

REQUIRED_TOML_FIELDS = ['id', 'name', 'version', 'description', 'author', 'fqbn']
REQUIRED_COMPANION   = ['sandbox.json', 'ports.json', 'README.md']


def validate_package(pkg_id: str, ver: str, toml_path: Path) -> list[str]:
    errors = []
    ver_dir = toml_path.parent

    try:
        data = read_board_toml(toml_path)
    except Exception as e:
        return [f"Cannot parse TOML: {e}"]

    for field in REQUIRED_TOML_FIELDS:
        if field not in data:
            errors.append(f"Missing TOML field: '{field}'")

    if data.get('id') != pkg_id:
        errors.append(f"TOML id '{data.get('id')}' doesn't match directory name '{pkg_id}'")

    for fname in REQUIRED_COMPANION:
        if not (ver_dir / fname).exists():
            errors.append(f"Missing companion file: {fname}")

    return errors


# ── Scaffolding ───────────────────────────────────────────────────────────────

TOML_TEMPLATE = '''\
[board]
id          = "{id}"
name        = "{name}"
version     = "{version}"
description = "{description}"
author      = "tsuki-ex"
fqbn        = "{fqbn}"
variant     = "{id}"
flash_kb    = {flash_kb}
ram_kb      = {ram_kb}

[files]
sandbox = "sandbox.json"
ports   = "ports.json"
readme  = "README.md"

[toolchain]
type        = "{arch}"
upload_tool = "esptool"
upload_baud = 2000000
f_cpu       = {f_cpu}

[detection]
name_patterns = ["{name}"]

[defines]
values = [
  "TSUKI_EX=1",
]
'''

SANDBOX_TEMPLATE = '''\
{{
  "type": "{id}",
  "label": "{name} (ex)",
  "w": 40,
  "h": 60,
  "color": "#1a1a2e",
  "borderColor": "#3d1a7a",
  "category": "mcu",
  "description": "{description}",
  "pins": []
}}
'''

PORTS_TEMPLATE = '''\
{{
  "usb": [
    {{ "vid": "1A86", "pid": "7523", "name": "CH340" }},
    {{ "vid": "0403", "pid": "6001", "name": "FTDI FT232RL" }}
  ],
  "name_patterns": ["{name}"]
}}
'''

README_TEMPLATE = '''\
# {name} (tsuki-ex)

Versión optimizada de {name}.

## Diferencias frente al paquete estándar

| Parámetro | Estándar | tsuki-ex |
|---|---|---|
| Baud subida | 921600 | **2000000** |
| TSUKI_EX | — | **=1** |
'''

ARCH_DEFAULTS = {
    'esp32':   {'fqbn': 'esp32:esp32:{id}',    'flash_kb': 4096, 'ram_kb': 520,  'f_cpu': 80000000},
    'esp8266': {'fqbn': 'esp8266:esp8266:{id}', 'flash_kb': 4096, 'ram_kb': 80,   'f_cpu': 80000000},
    'avr':     {'fqbn': 'arduino:avr:{id}',     'flash_kb': 32,   'ram_kb': 2,    'f_cpu': 16000000},
    'sam':     {'fqbn': 'arduino:sam:{id}',     'flash_kb': 512,  'ram_kb': 96,   'f_cpu': 84000000},
    'rp2040':  {'fqbn': 'rp2040:rp2040:{id}',  'flash_kb': 2048, 'ram_kb': 264,  'f_cpu': 133000000},
}


def scaffold_new(id_: str, version: str, description: str, arch: str, name: str):
    ver_str = f'v{version}'
    ver_dir = PKG_DIR / id_ / ver_str

    if ver_dir.exists():
        print(f'[error] {ver_dir} already exists')
        sys.exit(1)

    ver_dir.mkdir(parents=True)

    defaults = ARCH_DEFAULTS.get(arch, ARCH_DEFAULTS['esp32'])
    fqbn     = defaults['fqbn'].format(id=id_)

    (ver_dir / MANIFEST_NAME).write_text(TOML_TEMPLATE.format(
        id=id_, name=name, version=version, description=description,
        fqbn=fqbn, arch=arch,
        flash_kb=defaults['flash_kb'], ram_kb=defaults['ram_kb'],
        f_cpu=defaults['f_cpu'],
    ))
    (ver_dir / 'sandbox.json').write_text(SANDBOX_TEMPLATE.format(
        id=id_, name=name, description=description,
    ))
    (ver_dir / 'ports.json').write_text(PORTS_TEMPLATE.format(name=name))
    (ver_dir / 'README.md').write_text(README_TEMPLATE.format(name=name))

    print(f'[ok] Scaffolded pkg/{id_}/{ver_str}/')
    print(f'     Edit {MANIFEST_NAME}, sandbox.json, ports.json')
    print(f'     Then run: python pkg_manager.py sync')


def bump_version(pkg_id: str, new_version: str):
    latest = latest_version(pkg_id)
    if not latest:
        print(f'[error] Package {pkg_id!r} not found')
        sys.exit(1)

    old_ver, old_toml = latest
    old_dir = old_toml.parent
    new_ver = f'v{new_version}'
    new_dir = PKG_DIR / pkg_id / new_ver

    if new_dir.exists():
        print(f'[error] {new_dir} already exists')
        sys.exit(1)

    shutil.copytree(old_dir, new_dir)
    toml_path = new_dir / MANIFEST_NAME
    text = toml_path.read_text(encoding='utf-8')
    text = re.sub(r'^version\s*=\s*"[^"]*"', f'version     = "{new_version}"', text, flags=re.MULTILINE)
    toml_path.write_text(text, encoding='utf-8')
    print(f'[ok] Bumped {pkg_id}: {old_ver} → {new_ver}')
    print(f'     Edit pkg/{pkg_id}/{new_ver}/{MANIFEST_NAME}, then run: python pkg_manager.py sync')


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_list(_args):
    _check_pkg_dir()
    rows = []
    for id_, ver, toml_path in iter_packages():
        try:
            data = read_board_toml(toml_path)
            desc = data.get('description', '')[:55]
            arch = data.get('type', '?')
        except Exception:
            desc, arch = '(parse error)', '?'
        rows.append((id_, ver, arch, desc))

    if not rows:
        print('No board packages found in', PKG_DIR)
        return

    c1 = max(len(r[0]) for r in rows) + 2
    c2 = max(len(r[1]) for r in rows) + 2
    c3 = 10
    print(f"{'ID':<{c1}} {'VERSION':<{c2}} {'ARCH':<{c3}} DESCRIPTION")
    print('─' * 90)
    for id_, ver, arch, desc in rows:
        print(f'{id_:<{c1}} {ver:<{c2}} {arch:<{c3}} {desc}')


def cmd_validate(_args):
    _check_pkg_dir()
    found_errors = False
    for id_, ver, toml_path in iter_packages():
        errors = validate_package(id_, ver, toml_path)
        if errors:
            found_errors = True
            print(f'[FAIL] {id_}/{ver}')
            for e in errors:
                print(f'       • {e}')
        else:
            print(f'[ OK ] {id_}/{ver}')
    if found_errors:
        sys.exit(1)


def cmd_sync(args):
    _check_pkg_dir()
    branch   = getattr(args, 'branch', None) or None
    resolved = branch or _detect_branch()
    registry = build_registry(branch=resolved)
    out_path = PKG_DIR / 'packages.json'
    out_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    n = len(registry['packages'])
    print(f'[ok] Wrote packages.json ({n} board package{"s" if n != 1 else ""}) — branch: {resolved}')


def cmd_new(args):
    scaffold_new(
        id_=args.id,
        version=args.version,
        description=args.desc or f'{args.id} board package (tsuki-ex)',
        arch=args.arch,
        name=args.name or args.id,
    )
    cmd_sync(args)


def cmd_bump(args):
    bump_version(args.id, args.new_version)
    cmd_sync(args)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='tsuki-ex pkg manager — board packages',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python pkg_manager.py list
              python pkg_manager.py validate
              python pkg_manager.py sync
              python pkg_manager.py sync --branch dev
              python pkg_manager.py new myboard --arch esp32 --desc "My custom board"
              python pkg_manager.py bump esp32 1.1.0
        """),
    )
    sub = parser.add_subparsers(dest='cmd', required=True)

    branch_flag = argparse.ArgumentParser(add_help=False)
    branch_flag.add_argument('--branch', default='', metavar='BRANCH')

    sub.add_parser('list',     help='List all board packages')
    sub.add_parser('validate', help='Validate package structure')
    sub.add_parser('sync',     help='Rebuild packages.json from disk', parents=[branch_flag])

    p_new = sub.add_parser('new', help='Scaffold a new board package', parents=[branch_flag])
    p_new.add_argument('id')
    p_new.add_argument('--version', default='1.0.0')
    p_new.add_argument('--desc',    default='')
    p_new.add_argument('--arch',    default='esp32',
                       choices=['esp32', 'esp8266', 'avr', 'sam', 'rp2040'])
    p_new.add_argument('--name',    default='')

    p_bump = sub.add_parser('bump', help='Bump board package version', parents=[branch_flag])
    p_bump.add_argument('id')
    p_bump.add_argument('new_version')

    args = parser.parse_args()
    dispatch = {
        'list':     cmd_list,
        'validate': cmd_validate,
        'sync':     cmd_sync,
        'new':      cmd_new,
        'bump':     cmd_bump,
    }
    dispatch[args.cmd](args)


if __name__ == '__main__':
    main()
