#!/usr/bin/env python3
"""Build self-contained editions and deterministic ZIP packages from one source."""
import argparse
from pathlib import Path
import shutil
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent
VERSION = '1.1.0'


def build_at(target):
    for edition in ('codex', 'claude-code'):
        dest = target / edition / 'custom-sim'
        shutil.copytree(ROOT / 'common/custom-sim', dest, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        shutil.copy2(ROOT / 'adapters' / edition / 'runtime.md', dest / 'references/runtime.md')
        if edition == 'codex':
            (dest / 'agents').mkdir()
            shutil.copy2(ROOT / 'adapters/codex/openai.yaml', dest / 'agents/openai.yaml')
        else:
            agent = target / edition / 'agents'
            agent.mkdir()
            shutil.copy2(ROOT / 'adapters/claude-code/sim-builder.md', agent / 'sim-builder.md')


def contents(folder):
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in folder.rglob('*')
            if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if checked-in editions differ from source')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        generated = Path(tmp)
        build_at(generated)
        if args.check:
            if contents(generated) != contents(ROOT / 'editions'):
                raise SystemExit('Editions are out of date. Run python build.py.')
            print('Editions match the canonical source.')
            return
        for edition in ('codex', 'claude-code'):
            dest = ROOT / 'editions' / edition
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(generated / edition, dest)
        (ROOT / 'dist').mkdir(exist_ok=True)
        for edition in ('codex', 'claude-code'):
            path = ROOT / 'dist' / f'qizhi-custom-sim-{edition}-{VERSION}.zip'
            with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
                files = contents(ROOT / 'editions' / edition)
                files['README.md'] = (ROOT / 'README.md').read_bytes()
                files['LICENSE'] = (ROOT / 'LICENSE').read_bytes()
                for name, data in sorted(files.items()):
                    info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o644 << 16
                    z.writestr(info, data)
            print(path)


if __name__ == '__main__':
    main()
