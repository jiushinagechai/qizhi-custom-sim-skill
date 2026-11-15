"""Behavioral regression tests with controlled executables; no live browser or app state."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import queue
import threading
import unittest
from urllib.request import urlopen
from urllib.error import HTTPError

PACKAGE = Path(__file__).resolve().parents[1]
SCRIPT = PACKAGE / 'common/custom-sim/scripts/qizhi_sim.py'
spec = importlib.util.spec_from_file_location('qizhi_sim', SCRIPT)
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)

VIEWS = '''PHET_SIMS = [{"name": "example", "label": "示例", "static_file": "扩展-示例example.html"}]
def get_phet_sims():
    result = []
    for sim in PHET_SIMS:
        if sim["name"] == "other":
            version = "other"
        elif sim["name"] in {"example", "another"}:
            version = "20261115a"
        else:
            version = "fallback"
        result.append({**sim, "url": version})
    return result
'''
ELEMENTS = '''window.QIZHI_PHET_ELEMENTS = {"example": {"1": {
operations: [{event: "button_press", label: "开始实验"}], starters: ["如何操作？", "为什么变化？"]
}}};
'''
AUDIT = '''const CUSTOM_SIMS = new Set(['example']);
console.log('example: custom qizhi sim — boots OK, snapshot 1 lines');
'''
PROBE = '''const fs = require('node:fs');
fs.writeFileSync(process.env.QIZHI_CHECK_REPORT, JSON.stringify({
 checks: [{id: 'A1', passed: true, detail: 'controlled fixture outcome'}], errors: [], externalRequests: []
}));
'''


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='qizhi skill test ')
        self.root = Path(self.tmp.name) / '中文 project'
        self.root.mkdir()
        self.sim = 'django_site/static/phet-sims/扩展-示例example.html'
        for name, text in {
            q.VIEWS: VIEWS,
            q.PROMPTS: 'PHET_SIM_PROMPTS = {"example": "观察条件变化。"}\n',
            q.ELEMENTS: ELEMENTS,
            q.TEMPLATE: '<script src="/static/js/qizhi-phet-elements.js?v=20261115a"></script>\n',
            q.AUDIT: AUDIT,
            self.sim: '<!doctype html><button>开始实验</button>\n',
            'phet-audit/probe-example.cjs': PROBE,
            'phet-audit/verify-bridge-example.js': "console.log('VERIFY OK');\n",
        }.items():
            self.put(name, text)
        self.git('init', '-q')
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 '-c', 'commit.gpgsign=false', 'commit', '-qm', 'baseline')
        result = self.cli('init', 'example', '--owner', '测试者', '--file', self.sim)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.mpath = self.root / 'docs/custom-sims/example/manifest.json'
        self.put('docs/custom-sims/example/03-acceptance.md', '# Acceptance\n- [probe:A1] controlled behavior\n')

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def git(self, *args):
        p = subprocess.run(['git', *args], cwd=self.root, text=True, encoding='utf-8',
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.assertEqual(p.returncode, 0, p.stdout)
        return p.stdout.strip()

    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), '--repo', str(self.root), *args],
                              env={**os.environ, 'PYTHONUTF8': '1'}, text=True, encoding='utf-8',
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)

    def manifest(self):
        return json.loads(self.mpath.read_text(encoding='utf-8'))

    def gate(self, phase='integration', expected=0):
        p = self.cli('gate', 'example', '--phase', phase)
        self.assertEqual(p.returncode, expected, p.stdout)
        return self.manifest()['checks']

    def test_control_integration(self):
        checks = self.gate()
        self.assertTrue(checks['passed'])
        self.assertEqual(checks['results']['cache']['status'], 'pass')

    def test_init_creates_development_handoff(self):
        path = self.root / self.manifest()['development']
        self.assertTrue(path.is_file())
        self.assertIn('Functional contract', path.read_text(encoding='utf-8'))
        path.unlink()
        self.assertEqual(self.gate('demo', expected=1)['results']['files']['status'], 'fail')

    def test_v1_ledger_remains_usable(self):
        m = self.manifest()
        del m['development']
        self.mpath.write_text(json.dumps(m), encoding='utf-8')
        self.gate('demo')

    def setup_textbooks(self):
        folder = self.root / '本机 教材'
        folder.mkdir()
        (folder / '五上.pdf').write_bytes(b'%PDF-1.4\ncontrolled fixture')
        (folder / '课标.pdf').write_bytes(b'%PDF-1.4\ncontrolled fixture')
        result = self.cli('textbooks', 'configure', '--directory', str(folder), '--curriculum', '课标.pdf')
        self.assertEqual(result.returncode, 0, result.stdout)
        return folder

    def add_book(self, book_id='science-5a', publisher='测试版'):
        return self.cli('textbooks', 'add', '--id', book_id, '--grade', '5', '--semester', '上',
                        '--publisher', publisher, '--edition', '2025', '--file', '五上.pdf')

    def test_textbook_mapping_persists_and_is_ignored(self):
        folder = self.setup_textbooks()
        result = self.add_book()
        self.assertEqual(result.returncode, 0, result.stdout)
        result = self.cli('textbooks', 'find', '--grade', '5', '--semester', '上')
        self.assertEqual(result.returncode, 0, result.stdout)
        data = json.loads(result.stdout)
        self.assertEqual(data['matches'][0]['file'], str((folder / '五上.pdf').resolve()))
        self.assertTrue(data['matches'][0]['available'])
        self.assertTrue(data['curriculum_available'])
        self.assertFalse(data['selection_required'])
        self.assertEqual(self.git('check-ignore', q.TEXTBOOK_CONFIG), q.TEXTBOOK_CONFIG)

    def test_textbook_ambiguity_is_not_silently_resolved(self):
        self.setup_textbooks()
        self.add_book()
        self.add_book('second-5a', '另一个出版社')
        result = self.cli('textbooks', 'find', '--grade', '5')
        data = json.loads(result.stdout)
        self.assertTrue(data['selection_required'])
        self.assertEqual(len(data['matches']), 2)
        result = self.cli('textbooks', 'find', '--grade', '5', '--publisher', '测试版')
        self.assertEqual(len(json.loads(result.stdout)['matches']), 1)

    def test_textbook_inventory_missing_and_duplicate(self):
        folder = self.setup_textbooks()
        data = json.loads(self.cli('textbooks', 'list').stdout)
        self.assertIn('五上.pdf', data['pdf_candidates'])
        self.assertEqual(self.cli('textbooks', 'find', '--grade', '6').returncode, 1)
        self.add_book()
        self.assertEqual(self.add_book().returncode, 1)
        (folder / '五上.pdf').unlink()
        result = self.cli('textbooks', 'find', '--grade', '5')
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)['matches'][0]['available'])

    def test_tracked_local_config_is_not_overwritten(self):
        self.setup_textbooks()
        self.git('add', '-f', q.TEXTBOOK_CONFIG)
        before = (self.root / q.TEXTBOOK_CONFIG).read_bytes()
        result = self.add_book()
        self.assertEqual(result.returncode, 1)
        self.assertIn('tracked by Git', result.stdout)
        self.assertEqual(before, (self.root / q.TEXTBOOK_CONFIG).read_bytes())

    def test_textbook_replace_and_missing_pdf(self):
        self.setup_textbooks()
        self.add_book()
        result = self.cli('textbooks', 'add', '--id', 'science-5a', '--grade', '5', '--semester', '上',
                          '--publisher', '新版本', '--edition', '2026', '--file', '五上.pdf', '--replace')
        self.assertEqual(result.returncode, 0, result.stdout)
        result = self.cli('textbooks', 'find', '--grade', '5')
        self.assertEqual(json.loads(result.stdout)['matches'][0]['edition'], '2026')
        result = self.cli('textbooks', 'configure', '--curriculum', 'missing.pdf')
        self.assertEqual(result.returncode, 1)

    def test_preview_url_without_acceptance_side_effect(self):
        before = self.mpath.read_bytes()
        result = self.cli('preview', 'example')
        self.assertEqual(result.returncode, 0, result.stdout)
        data = json.loads(result.stdout)
        self.assertEqual(data['url'], (self.root / self.sim).resolve().as_uri())
        self.assertEqual(len(data['sha256']), 64)
        self.assertEqual(before, self.mpath.read_bytes())

    def test_preview_http_refresh_and_directory_boundary(self):
        process = subprocess.Popen([sys.executable, str(SCRIPT), '--repo', str(self.root),
                                    'preview', 'example', '--serve'], stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL, text=True, encoding='utf-8',
                                   env={**os.environ, 'PYTHONUTF8': '1'})
        lines = queue.Queue()
        thread = threading.Thread(target=lambda: lines.put(process.stdout.readline()), daemon=True)
        thread.start()
        try:
            data = json.loads(lines.get(timeout=10))
            self.assertTrue(data['url'].startswith('http://127.0.0.1:'))
            with urlopen(data['url'], timeout=5) as response:
                self.assertEqual(response.headers['Cache-Control'], 'no-store')
                self.assertIn('开始实验', response.read().decode('utf-8'))
            self.put(self.sim, '<button>新的一轮</button>')
            with urlopen(data['url'], timeout=5) as response:
                self.assertIn('新的一轮', response.read().decode('utf-8'))
            base = data['url'].rsplit('/', 1)[0]
            with self.assertRaises(HTTPError) as error:
                urlopen(base + '/', timeout=5)
            self.assertEqual(error.exception.code, 403)
            error.exception.close()
            with self.assertRaises(HTTPError) as error:
                urlopen(base + '/../../../.qizhi-sim.local.json', timeout=5)
            error.exception.close()
        finally:
            process.terminate()
            process.wait(timeout=5)
            process.stdout.close()

    def test_distinct_page_acceptance_and_integration_authorization(self):
        for item in ('design', 'demo', 'integration', 'platform'):
            result = self.cli('mark', 'example', item, '--result', 'pass', '--by', 'user',
                              '--evidence', 'explicit statement for ' + item)
            self.assertEqual(result.returncode, 0, result.stdout)
        human = self.manifest()['human']
        self.assertIn(self.sim, human['demo']['artifacts'])
        self.assertIn(self.manifest()['development'], human['design']['artifacts'])
        self.assertNotEqual(human['design']['evidence'], human['demo']['evidence'])

    def test_missing_demo_cannot_be_marked_accepted(self):
        (self.root / self.sim).unlink()
        result = self.cli('mark', 'example', 'demo', '--result', 'pass', '--by', 'user', '--evidence', 'claim')
        self.assertEqual(result.returncode, 1)
        self.assertNotIn('demo', self.manifest()['human'])

    def test_decisions_survive_unrelated_verification_changes(self):
        for item in ('design', 'demo', 'integration'):
            self.cli('mark', 'example', item, '--result', 'pass', '--by', 'user', '--evidence', 'actual statement')
        self.put(q.VIEWS, VIEWS + '# integration work\n')
        output = self.cli('status', 'example').stdout
        self.assertIn('design: pass; actual statement', output)
        self.assertIn('demo: pass; actual statement', output)
        self.assertIn('integration: pass (historical decision;', output)
        self.put(self.sim, '<button>different behavior</button>')
        self.assertIn('demo: pass (historical decision;', self.cli('status', 'example').stdout)

    def test_demo_needs_no_marker_registration_or_bridge(self):
        self.put(q.VIEWS, 'PHET_SIMS = []\n')
        self.put(q.AUDIT, "throw new Error('must not run in demo')")
        (self.root / 'phet-audit/verify-bridge-example.js').unlink()
        checks = self.gate('demo')
        for key in ('registration', 'audit', 'bridge', 'cache'):
            self.assertEqual(checks['results'][key]['status'], 'not_applicable')

    def test_audit_failure_even_with_success_text(self):
        self.put(q.AUDIT, AUDIT + 'process.exitCode = 1;\n')
        checks = self.gate(expected=1)
        self.assertEqual(checks['results']['audit']['status'], 'fail')

    def test_empty_snapshot_fails(self):
        self.put(q.AUDIT, AUDIT.replace('1 lines', 'EMPTY (check snapshot)') + 'process.exitCode = 1;\n')
        checks = self.gate(expected=1)
        self.assertEqual(checks['results']['audit']['status'], 'fail')

    def test_audit_startup_crash_fails(self):
        self.put(q.AUDIT, "throw new Error('Browser startup failed');")
        self.assertEqual(self.gate(expected=1)['results']['audit']['status'], 'fail')

    def test_zero_exit_without_actual_audit_is_failure(self):
        self.put(q.AUDIT, "const CUSTOM_SIMS = new Set(['example']); console.log('nothing audited');")
        self.assertEqual(self.gate(expected=1)['results']['audit']['status'], 'fail')

    def test_bridge_nonzero_after_success_is_failure(self):
        self.put('phet-audit/verify-bridge-example.js', "console.log('VERIFY OK'); process.exitCode = 1;")
        self.assertEqual(self.gate(expected=1)['results']['bridge']['status'], 'fail')

    def test_unrelated_views_edit_cannot_mask_unchanged_cache(self):
        self.put(self.sim, '<button>changed</button>\n')
        self.put(q.VIEWS, VIEWS + '# unrelated comment\n')
        self.assertEqual(self.gate(expected=1)['results']['cache']['status'], 'fail')

    def test_effective_sim_version_bump_passes(self):
        self.put(self.sim, '<button>changed</button>\n')
        self.put(q.VIEWS, VIEWS.replace('20261115a', '20261115b'))
        self.assertEqual(self.gate()['results']['cache']['status'], 'pass')

    def test_shared_elements_cache_required(self):
        self.put(q.ELEMENTS, ELEMENTS + '\n// new shared content\n')
        self.assertEqual(self.gate(expected=1)['results']['cache']['status'], 'fail')
        self.put(q.TEMPLATE, '<script src="/static/js/qizhi-phet-elements.js?v=20261115b"></script>')
        self.gate()

    def test_comment_only_python_registration_fails(self):
        self.put(q.VIEWS, '# "example"\nPHET_SIMS = []\n')
        self.assertEqual(self.gate(expected=1)['results']['registration']['status'], 'fail')

    def test_comment_only_js_registration_fails(self):
        self.put(q.ELEMENTS, '// "example"\nwindow.QIZHI_PHET_ELEMENTS = {};\n')
        self.assertEqual(self.gate(expected=1)['results']['registration']['status'], 'fail')

    def test_existing_longer_starter_list_is_supported(self):
        self.put(q.ELEMENTS, ELEMENTS.replace('["如何操作？", "为什么变化？"]', '["问题1", "问题2", "问题3", "问题4", "问题5", "问题6"]'))
        self.put(q.TEMPLATE, '<script src="/static/js/qizhi-phet-elements.js?v=20261115b"></script>')
        self.gate()

    def test_comment_only_audit_membership_fails(self):
        self.put(q.AUDIT, '// const CUSTOM_SIMS = new Set(["example"]);\n' + AUDIT.replace("['example']", '[]'))
        self.assertEqual(self.gate(expected=1)['results']['registration']['status'], 'fail')

    def test_missing_file_replaces_previous_pass(self):
        self.gate()
        (self.root / self.sim).unlink()
        checks = self.gate(expected=1)
        self.assertFalse(checks['passed'])
        self.assertEqual(checks['results']['files']['status'], 'fail')
        self.assertIn('gate=FAIL', self.cli('status', 'example').stdout)

    def test_status_stale_after_edit(self):
        self.gate()
        self.put(self.sim, '<button>new</button>')
        self.assertIn('gate=STALE', self.cli('status', 'example').stdout)

    def test_human_mark_revoke_and_stale(self):
        result = self.cli('mark', 'example', 'tablet', '--result', 'pass', '--by', 'tester', '--evidence', 'device evidence')
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('tablet: pass', self.cli('status', 'example').stdout)
        self.put(self.sim, 'changed')
        self.assertIn('tablet: STALE', self.cli('status', 'example').stdout)
        self.cli('mark', 'example', 'tablet', '--result', 'pending', '--by', 'tester', '--evidence', 'needs retest')
        self.assertIn('tablet: pending', self.cli('status', 'example').stdout)

    def test_stale_report_not_reused(self):
        self.gate('demo')
        self.put('phet-audit/probe-example.cjs', "console.log('all checks passed');")
        self.assertEqual(self.gate('demo', expected=1)['results']['probe']['status'], 'fail')

    def test_assertion_coverage_is_checked(self):
        self.put('docs/custom-sims/example/03-acceptance.md', '- [probe:A1] first\n- [probe:A2] missing\n')
        checks = self.gate('demo', expected=1)
        self.assertIn('A2', checks['results']['probe']['detail'])

    def test_false_assertion_cannot_pass_on_zero_exit(self):
        self.put('phet-audit/probe-example.cjs', PROBE.replace('passed: true', 'passed: false'))
        self.assertEqual(self.gate('demo', expected=1)['results']['probe']['status'], 'fail')

    def test_late_network_request_fails(self):
        self.put('phet-audit/probe-example.cjs', PROBE.replace('externalRequests: []', "externalRequests: ['https://example.invalid/late']"))
        self.assertEqual(self.gate('demo', expected=1)['results']['probe']['status'], 'fail')

    def test_probe_timeout_records_failure(self):
        self.put('phet-audit/probe-example.cjs', 'setInterval(() => {}, 1000);')
        p = self.cli('gate', 'example', '--phase', 'demo', '--timeout', '1')
        self.assertEqual(p.returncode, 1, p.stdout)
        self.assertFalse(self.manifest()['checks']['passed'])

    def test_init_preserves_existing_ledger(self):
        before = self.mpath.read_bytes()
        p = self.cli('init', 'example', '--owner', 'other', '--file', self.sim)
        self.assertEqual(p.returncode, 1)
        self.assertEqual(before, self.mpath.read_bytes())

    def test_path_escape_rejected(self):
        m = self.manifest()
        m['file'] = '../outside.html'
        self.mpath.write_text(json.dumps(m), encoding='utf-8')
        p = self.cli('gate', 'example', '--phase', 'demo')
        self.assertEqual(p.returncode, 1)
        self.assertIn('Path must stay inside', p.stdout)

    def test_unknown_version_schema_fails_closed(self):
        self.put(q.VIEWS, VIEWS.replace('"20261115a"', 'lookup_version(sim)'))
        self.assertEqual(self.gate(expected=1)['results']['cache']['status'], 'fail')

    def test_prompt_budget_enforced(self):
        self.put(q.PROMPTS, 'PHET_SIM_PROMPTS = {"example": ' + repr('字' * 301) + '}')
        self.assertEqual(self.gate(expected=1)['results']['registration']['status'], 'fail')


class PackagingTests(unittest.TestCase):
    def run_python(self, *args):
        return subprocess.run([sys.executable, *map(str, args)], cwd=PACKAGE, text=True, encoding='utf-8',
                              env={**os.environ, 'PYTHONUTF8': '1'}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)

    def test_editions_match_canonical_source(self):
        result = self.run_python(PACKAGE / 'build.py', '--check')
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_install_both_and_backup_existing(self):
        with tempfile.TemporaryDirectory(prefix='skill install ') as tmp:
            root = Path(tmp) / '中文 project'
            (root / 'django_site/phet').mkdir(parents=True)
            (root / 'django_site/phet/views.py').write_text('')
            result = self.run_python(PACKAGE / 'install.py', '--target', 'both', '--repo', root)
            self.assertEqual(result.returncode, 0, result.stdout)
            for host in ('.agents', '.claude'):
                skill = root / host / 'skills/custom-sim'
                self.assertTrue((skill / 'references/runtime.md').is_file())
                self.assertTrue((skill / 'scripts/qizhi_sim.py').is_file())
            self.assertTrue((root / '.claude/agents/sim-builder.md').is_file())
            old = root / '.agents/skills/custom-sim/personal.txt'
            old.write_text('preserve me')
            result = self.run_python(PACKAGE / 'install.py', '--target', 'both', '--repo', root)
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(old.exists())
            result = self.run_python(PACKAGE / 'install.py', '--target', 'both', '--repo', root, '--replace')
            self.assertEqual(result.returncode, 0, result.stdout)
            backups = list((root / '.agents/skill-backups').glob('*/custom-sim/personal.txt'))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(), 'preserve me')
            self.assertEqual(len(list((root / '.agents/skills').glob('*/SKILL.md'))), 1)

    def test_package_contains_no_personal_state(self):
        for folder in ['common', 'adapters', 'editions']:
            for path in (PACKAGE / folder).rglob('*'):
                if path.is_file() and '__pycache__' not in path.parts:
                    content = path.read_text(encoding='utf-8')
                    self.assertNotRegex(content, r'/(?:Users|home)/[^/\s]+/', str(path))
                    self.assertNotRegex(content, r'[A-Z]:\\Users\\[^\\]+\\', str(path))
        self.assertFalse(list((PACKAGE / 'editions').rglob('manifest.json')))


if __name__ == '__main__':
    unittest.main()
