#!/usr/bin/env python3
"""Install a bundled edition into an explicit project or user directory, backing up replacements."""
import argparse
import datetime as dt
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--target', choices=['codex', 'claude-code', 'both'], required=True)
    where = p.add_mutually_exclusive_group(required=True)
    where.add_argument('--repo', type=Path, help='A qizhi project checkout')
    where.add_argument('--user', action='store_true', help='Install for this OS user')
    p.add_argument('--replace', action='store_true', help='Back up existing skills/agent before replacement')
    args = p.parse_args()
    if args.repo:
        base = args.repo.expanduser().resolve()
        if not (base / 'django_site/phet/views.py').is_file():
            p.error('--repo must point to a qizhi checkout')
    else:
        base = Path.home()
    editions = ['codex', 'claude-code'] if args.target == 'both' else [args.target]
    jobs = []
    for edition in editions:
        host_dir = '.agents' if edition == 'codex' else '.claude'
        jobs.append((ROOT / 'editions' / edition / 'custom-sim', base / host_dir / 'skills/custom-sim'))
        if edition == 'claude-code':
            jobs.append((ROOT / 'editions/claude-code/agents/sim-builder.md', base / '.claude/agents/sim-builder.md'))
    for source, dest in jobs:
        if not source.exists():
            p.error('Edition missing; run python build.py first: ' + str(source))
        if dest.exists() and not args.replace:
            p.error('Already exists; use --replace to preserve it as a timestamped backup: ' + str(dest))
        if dest.is_symlink():
            p.error('Refusing to replace a symlink; select the intended real install path: ' + str(dest))
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backups = []
    created = []
    try:
        for source, dest in jobs:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                # Keep backups outside skills/ so auto-discovery cannot load a second stale skill.
                archive = base / ('.agents' if '.agents' in dest.parts else '.claude') / 'skill-backups' / stamp
                archive.mkdir(parents=True, exist_ok=True)
                backup = archive / dest.name
                if backup.exists():
                    raise FileExistsError(backup)
                dest.rename(backup)
                backups.append((dest, backup))
                print('Backup: ' + str(backup))
            created.append(dest)
            if source.is_dir():
                shutil.copytree(source, dest)
            else:
                shutil.copy2(source, dest)
            print('Installed: ' + str(dest))
    except Exception:
        for dest in reversed(created):
            if dest.is_dir():
                shutil.rmtree(dest)
            elif dest.exists():
                dest.unlink()
        for dest, backup in reversed(backups):
            backup.rename(dest)
        raise
    print('Open a fresh agent session in qizhi. Run doctor with the installed script and --repo.')


if __name__ == '__main__':
    main()
