#!/usr/bin/env python3
"""Portable local workflow checks for a qizhi checkout; Python standard library only."""
import argparse
import ast
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

SKILL = Path(__file__).resolve().parents[1]
VIEWS = 'django_site/phet/views.py'
PROMPTS = 'django_site/phet/prompts.py'
ELEMENTS = 'django_site/static/js/qizhi-phet-elements.js'
TEMPLATE = 'django_site/templates/phet/phet_sim.html'
AUDIT = 'phet-audit/audit.js'
SIM_DIR = 'django_site/static/phet-sims'
SLUG = re.compile(r'^[a-z][a-z0-9_-]*$')


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def read(path):
    return Path(path).read_text(encoding='utf-8-sig')


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')
        temporary = f.name
    os.replace(temporary, path)


def inside(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Path must stay inside the qizhi checkout: ' + str(name))
    return path


def command(argv, cwd, env=None, timeout=120):
    try:
        p = subprocess.run(argv, cwd=cwd, env=env, text=True, encoding='utf-8', errors='replace',
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        return p.returncode, p.stdout
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)


def git(root, *args):
    rc, output = command(['git', *args], root)
    if rc:
        raise ValueError('git: ' + output.strip())
    return output.strip()


def repo_path(value):
    root = Path(value).expanduser().resolve()
    if not (root / VIEWS).is_file() or not (root / SIM_DIR).is_dir():
        raise ValueError('Not a supported qizhi checkout: ' + str(root))
    return root


def manifest_path(root, slug):
    if not SLUG.fullmatch(slug):
        raise ValueError('Use a lowercase slug containing letters, digits, hyphens or underscores.')
    return root / 'docs/custom-sims' / slug / 'manifest.json'


def load_manifest(root, slug):
    path = manifest_path(root, slug)
    m = json.loads(read(path))
    if m.get('schema') != 1 or m.get('slug') != slug:
        raise ValueError('Unsupported manifest schema or slug mismatch: ' + str(path))
    for key in ('file', 'probe', 'bridge', 'acceptance', 'design', 'lesson'):
        if not isinstance(m.get(key), str) or not m[key]:
            raise ValueError('Missing manifest path: ' + key)
        inside(root, m[key])
    return path, m


def literal_assignment(source, name):
    tree = ast.parse(source)
    found = [n.value for n in tree.body if isinstance(n, (ast.Assign, ast.AnnAssign))
             and any(isinstance(t, ast.Name) and t.id == name
                     for t in (n.targets if isinstance(n, ast.Assign) else [n.target]))]
    if len(found) != 1:
        raise ValueError('Expected one literal assignment for ' + name)
    return ast.literal_eval(found[0])


def expression(node, values):
    """Evaluate the small, explicit version-selector syntax, never import Django."""
    if isinstance(node, ast.Name) and node.id in values:
        return values[node.id]
    if isinstance(node, ast.Subscript):
        return expression(node.value, values)[expression(node.slice, values)]
    if isinstance(node, ast.Compare) and len(node.ops) == 1:
        left, right = expression(node.left, values), expression(node.comparators[0], values)
        op = node.ops[0]
        if isinstance(op, ast.Eq):
            return left == right
        if isinstance(op, ast.NotEq):
            return left != right
        if isinstance(op, ast.In):
            return left in right
        if isinstance(op, ast.NotIn):
            return left not in right
    if isinstance(node, ast.BoolOp):
        vals = [expression(v, values) for v in node.values]
        return all(vals) if isinstance(node.op, ast.And) else any(vals)
    return ast.literal_eval(node)


def sim_version(source, slug):
    catalog = literal_assignment(source, 'PHET_SIMS')
    entries = [x for x in catalog if x.get('name') == slug]
    if not entries:
        return None
    if len(entries) != 1:
        raise ValueError('Duplicate PHET_SIMS entry: ' + slug)
    funcs = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'get_phet_sims']
    if len(funcs) != 1:
        raise ValueError('get_phet_sims function not found')
    values = {'sim': entries[0]}

    def visit(nodes):
        for n in nodes:
            if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'version' for t in n.targets):
                values['version'] = expression(n.value, values)
            elif isinstance(n, ast.If):
                visit(n.body if expression(n.test, values) else n.orelse)

    loops = [n for n in funcs[0].body if isinstance(n, ast.For)
             and isinstance(n.iter, ast.Name) and n.iter.id == 'PHET_SIMS']
    if len(loops) != 1:
        raise ValueError('Unsupported get_phet_sims structure; update the adapter before approving cache checks.')
    visit(loops[0].body)
    version = values.get('version')
    if not isinstance(version, str) or not version:
        raise ValueError('Cannot resolve the actual per-sim version')
    return version


def script_version(source):
    from html.parser import HTMLParser

    class Scripts(HTMLParser):
        urls = []
        def handle_starttag(self, tag, attrs):
            if tag == 'script':
                src = dict(attrs).get('src', '')
                if 'qizhi-phet-elements.js' in src:
                    self.urls.append(src)
    parser = Scripts()
    parser.urls = []
    parser.feed(source)
    if len(parser.urls) != 1:
        raise ValueError('Expected one elements.js script tag')
    match = re.search(r'[?&]v=([^&\s]+)', parser.urls[0])
    if not match:
        raise ValueError('Missing elements.js cache version')
    return match.group(1)


def tracked_paths(m):
    return sorted(set([m[k] for k in ('file', 'probe', 'bridge', 'acceptance', 'design', 'lesson')]
                      + [VIEWS, PROMPTS, ELEMENTS, TEMPLATE, AUDIT, 'phet-audit/browser.js',
                         'phet-audit/package.json', 'phet-audit/package-lock.json',
                         'django_site/static/js/qizhi-phet-bridge.js',
                         'django_site/static/js/qizhi-phet-inspect.js',
                         'django_site/static/js/qizhi-phet-pedagogy.js']))


def fingerprint(root, m):
    h = hashlib.sha256()
    config = {k: v for k, v in m.items() if k not in ('checks', 'human')}
    h.update(json.dumps(config, sort_keys=True, ensure_ascii=False).encode())
    for name in tracked_paths(m):
        path = inside(root, name)
        h.update(name.encode())
        h.update(path.read_bytes() if path.is_file() else b'<missing>')
    for path in sorted((SKILL / 'scripts').glob('*')):
        if path.is_file():
            h.update(path.read_bytes())
    return h.hexdigest()


def init(args, root):
    path = manifest_path(root, args.slug)
    if path.exists():
        raise ValueError('Manifest exists; resume it instead of overwriting: ' + str(path))
    sim = inside(root, args.file)
    if sim.parent != root / SIM_DIR or not sim.name.endswith(args.slug + '.html') or not re.match(r'^(?:[一二三四五六][上下]-\d+|扩展-)[^a-z]+[a-z]', sim.name):
        raise ValueError('Use a flat filename such as 五上-1实验example.html or 扩展-实验example.html.')
    base = git(root, 'rev-parse', '--verify', args.base + '^{commit}')
    folder = path.parent.relative_to(root).as_posix()
    m = dict(schema=1, slug=args.slug, owner=args.owner, phase='design', base_ref=base,
             file=sim.relative_to(root).as_posix(), probe='phet-audit/probe-' + args.slug + '.cjs',
             bridge='phet-audit/verify-bridge-' + args.slug + '.js',
             lesson=folder + '/01-lesson-research.md', design=folder + '/02-design.md',
             acceptance=folder + '/03-acceptance.md', checks={}, human={})
    path.parent.mkdir(parents=True, exist_ok=True)
    for key, template in [('lesson', 'lesson-research.md'), ('design', 'design.md'), ('acceptance', 'acceptance.md')]:
        target = inside(root, m[key])
        if not target.exists():
            target.write_text(read(SKILL / 'assets' / template).replace('{{slug}}', args.slug), encoding='utf-8')
    save(path, m)
    print('Created ' + str(path) + '\nBaseline commit: ' + base)
    return 0


def doctor(args, root):
    failures = []
    for name in ('git', 'node', 'npm'):
        found = shutil.which(name)
        print(('PASS ' if found else 'FAIL ') + name + ': ' + (found or 'install it and add it to PATH'))
        if not found:
            failures.append(name)
    required = [AUDIT, 'phet-audit/browser.js', 'phet-audit/package.json', ELEMENTS, PROMPTS, TEMPLATE]
    for name in required:
        if not (root / name).is_file():
            failures.append(name)
            print('FAIL missing platform file: ' + name + '; update your qizhi checkout.')
    if shutil.which('node') and (root / 'phet-audit/browser.js').is_file():
        rc, output = command(['node', '-e', "require('puppeteer-core'); console.log(require('./browser').executablePath())"], root / 'phet-audit')
        print(('PASS ' if rc == 0 else 'FAIL ') + 'browser/dependencies: ' + output.strip())
        if rc:
            failures.append('browser')
            print('Run npm ci in phet-audit (npm install if no lockfile); install Chrome/Edge or set QIZHI_BROWSER.')
    print('INFO textbook extraction: ' + ('pdftotext available' if shutil.which('pdftotext') else 'install Poppler or use your PDF-reading tool'))
    print('INFO local sim checks need no Django server or AI API key. Platform/student checks do.')
    return int(bool(failures))


def git_blob(root, base, name):
    rc, output = command(['git', 'cat-file', '-e', base + ':' + name], root)
    if rc:
        return None
    rc, output = command(['git', 'show', base + ':' + name], root)
    if rc:
        raise ValueError(output)
    return output


def cache_check(root, m):
    base = git(root, 'rev-parse', '--verify', m['base_ref'] + '^{commit}')
    current = sim_version(read(root / VIEWS), m['slug'])
    if current is None:
        raise ValueError('Sim has no effective catalog version')
    old_views = git_blob(root, base, VIEWS)
    old_version = sim_version(old_views, m['slug']) if old_views else None
    # Git text output normalizes CRLF, as does read_text, avoiding false Windows changes.
    old_sim = git_blob(root, base, m['file'])
    if old_sim is not None and old_sim != read(inside(root, m['file'])) and current == old_version:
        raise ValueError('Sim content changed but its effective ?v= is unchanged: ' + current)
    old_elements = git_blob(root, base, ELEMENTS)
    elements_version = script_version(read(root / TEMPLATE))
    if old_elements is not None and old_elements != read(root / ELEMENTS):
        old_template = git_blob(root, base, TEMPLATE)
        if old_template and script_version(old_template) == elements_version:
            raise ValueError('elements.js changed but its template ?v= is unchanged')
    return 'sim=' + current + '; elements=' + elements_version + '; baseline=' + base[:12]


def gate(args, root):
    path, m = load_manifest(root, args.slug)
    run_dir = root / 'phet-audit/out/skill' / args.slug
    run_dir.mkdir(parents=True, exist_ok=True)
    initial = fingerprint(root, m)
    results = {}

    def check(name, operation):
        try:
            detail = operation()
            results[name] = {'status': 'pass', 'detail': str(detail or 'OK')}
        except Exception as e:
            results[name] = {'status': 'fail', 'detail': str(e)}
        print(results[name]['status'].upper() + ' ' + name + ': ' + results[name]['detail'], flush=True)

    def external(name, argv, success, env=None):
        rc, output = command(argv, root / 'phet-audit', env=env, timeout=args.timeout)
        (run_dir / (name + '.log')).write_text(output, encoding='utf-8')
        if rc != 0 or not success(output):
            raise ValueError('exit=' + str(rc) + '; see ' + str(run_dir / (name + '.log')))
        return 'exit=0; ' + str(run_dir / (name + '.log'))

    def files():
        missing = [x for x in [m['file'], m['probe'], m['acceptance'], m['design'], m['lesson']]
                   if not inside(root, x).is_file()]
        if missing:
            raise ValueError('Missing: ' + ', '.join(missing))
        return 'Source, evidence documents and probe exist'

    check('files', files)

    def probe():
        report = run_dir / 'probe.json'
        if report.exists():
            report.unlink()
        env = {**os.environ, 'QIZHI_CHECK_REPORT': str(report), 'QIZHI_SIM_FILE': str(inside(root, m['file'])),
               'QIZHI_SIM_PHASE': args.phase}
        external('probe', ['node', str(inside(root, m['probe']))], lambda _: True, env)
        data = json.loads(read(report))
        checks = data.get('checks')
        if not isinstance(checks, list) or not checks or any(not isinstance(c, dict) for c in checks):
            raise ValueError('Probe must emit a non-empty checks array')
        ids = [c.get('id') for c in checks]
        if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
            raise ValueError('Every probe assertion needs a unique non-empty ID')
        expected = set(re.findall(r'\[probe:([A-Za-z0-9_-]+)\]', read(inside(root, m['acceptance']))))
        if not expected or not expected.issubset(ids):
            raise ValueError('Acceptance assertion IDs missing: ' + ', '.join(sorted(expected - set(ids))) + '; add real behavioral assertions')
        if any(c.get('passed') is not True for c in checks):
            raise ValueError('Failed assertions: ' + ', '.join(c['id'] for c in checks if c.get('passed') is not True))
        for key in ('errors', 'externalRequests'):
            if data.get(key) != []:
                raise ValueError('Probe must report ' + key + ' as an empty array after all interactions')
        return str(len(checks)) + ' assertions; all acceptance IDs present; review assertion meaning independently'

    check('probe', probe)
    if args.phase == 'integration':
        def registration():
            entries = literal_assignment(read(root / VIEWS), 'PHET_SIMS')
            selected = [x for x in entries if x.get('name') == args.slug]
            if len(selected) != 1 or selected[0].get('static_file') != Path(m['file']).name:
                raise ValueError('PHET_SIMS must contain exactly one matching name and static_file')
            prompts = literal_assignment(read(root / PROMPTS), 'PHET_SIM_PROMPTS')
            if not isinstance(prompts.get(args.slug), str) or not prompts[args.slug].strip():
                raise ValueError('PHET_SIM_PROMPTS entry is missing or empty')
            prefix = '当前实验：' + selected[0].get('label', '') + '；'
            if len(prefix + prompts[args.slug]) > 300:
                raise ValueError('Prompt plus experiment prefix exceeds the documented 300-character budget')
            return external('registration', ['node', str(SKILL / 'scripts/inspect-config.cjs'), str(root), args.slug],
                            lambda out: 'CONFIG OK' in out)
        check('registration', registration)
        check('audit', lambda: external('audit', ['node', 'audit.js', args.slug],
              lambda out: bool(re.search(re.escape(args.slug) + r': custom qizhi sim .*boots OK, snapshot [1-9]\d* lines', out))
              and not re.search(r'BOOT FAILED|not a literal string|✗|: ERROR|snapshot EMPTY|no operations declared', out)))
        check('bridge', lambda: external('bridge', ['node', str(inside(root, m['bridge']))], lambda out: bool(re.search(r'^VERIFY OK\b', out, re.M))))
        check('cache', lambda: cache_check(root, m))
    else:
        for name in ('registration', 'audit', 'bridge', 'cache'):
            results[name] = {'status': 'not_applicable', 'detail': 'Demo phase: platform checks run after integration'}
            print('N/A ' + name + ': demo phase')

    if fingerprint(root, m) != initial:
        results['source_stability'] = {'status': 'fail', 'detail': 'Inputs changed during the run; rerun after edits finish'}
    ok = all(r['status'] in ('pass', 'not_applicable') for r in results.values())
    m['checks'] = dict(phase=args.phase, at=now(), fingerprint=initial, passed=ok, results=results)
    save(path, m)
    print(('PASS' if ok else 'FAIL') + ' overall; ledger updated: ' + str(path))
    return int(not ok)


def status(args, root):
    paths = [manifest_path(root, args.slug)] if args.slug else sorted((root / 'docs/custom-sims').glob('*/manifest.json'))
    for path in paths:
        try:
            _, m = load_manifest(root, path.parent.name)
            checks = m.get('checks', {})
            current = fingerprint(root, m)
            state = 'NOT RUN' if not checks else ('STALE' if checks.get('fingerprint') != current else 'PASS' if checks.get('passed') else 'FAIL')
            print(m['slug'] + ' | phase=' + m['phase'] + ' | gate=' + state + ' (' + checks.get('phase', '-') + ')')
            for key, result in m.get('human', {}).items():
                state = 'STALE' if result.get('fingerprint') != current else result['status']
                print('  ' + key + ': ' + state + '; ' + result.get('evidence', ''))
        except Exception as e:
            print('FAIL ' + str(path) + ': ' + str(e))
    if not paths:
        print('No manifests. Start with init.')
    return 0


def mark(args, root):
    path, m = load_manifest(root, args.slug)
    m.setdefault('human', {})[args.item] = dict(status=args.result, at=now(), by=args.by,
                                             evidence=args.evidence, fingerprint=fingerprint(root, m))
    save(path, m)
    print('Recorded actual human decision: ' + args.item + '=' + args.result)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, help='Explicit path to a qizhi Git checkout')
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('doctor')
    p = sub.add_parser('init')
    p.add_argument('slug'); p.add_argument('--file', required=True); p.add_argument('--owner', required=True)
    p.add_argument('--base', default='HEAD', help='Commit/ref before this change; stored as an immutable SHA')
    p = sub.add_parser('gate')
    p.add_argument('slug'); p.add_argument('--phase', choices=['demo', 'integration'], required=True)
    p.add_argument('--timeout', type=int, default=420, help='Seconds per child command')
    p = sub.add_parser('status'); p.add_argument('slug', nargs='?')
    p = sub.add_parser('mark')
    p.add_argument('slug'); p.add_argument('item', choices=['design', 'review', 'tablet', 'taskcard', 'csv', 'playtest', 'commit'])
    p.add_argument('--result', choices=['pass', 'fail', 'pending', 'not_applicable'], required=True)
    p.add_argument('--by', required=True); p.add_argument('--evidence', required=True)
    args = parser.parse_args()
    try:
        if getattr(args, 'timeout', 1) <= 0:
            raise ValueError('Timeout must be positive')
        root = repo_path(args.repo)
        return globals()[args.action](args, root)
    except (ValueError, OSError, SyntaxError, KeyError, TypeError) as e:
        print('FAIL ' + str(e), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
