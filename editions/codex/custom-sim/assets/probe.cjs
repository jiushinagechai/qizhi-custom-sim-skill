// Copy to phet-audit/probe-<slug>.cjs. Implement acceptance IDs using real UI actions.
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const puppeteer = require('puppeteer-core');
const {launchOptions} = require('./browser');

const report = {checks: [], errors: [], externalRequests: []};
let browser;
function check(id, passed, detail = '') {
  if (report.checks.some(c => c.id === id)) throw new Error('Duplicate assertion ID: ' + id);
  report.checks.push({id, passed: Boolean(passed), detail});
  console.log((passed ? 'PASS ' : 'FAIL ') + id + ' ' + detail);
}

(async () => {
  try {
    if (!process.env.QIZHI_SIM_FILE || !process.env.QIZHI_CHECK_REPORT) throw new Error('Run with qizhi_sim.py gate');
    browser = await puppeteer.launch(launchOptions());
    const page = await browser.newPage();
    page.on('pageerror', e => report.errors.push(e.message));
    page.on('console', m => { if (m.type() === 'error') report.errors.push(m.text()); });
    page.on('request', r => {
      if (!/^(file:|data:|blob:|about:)/.test(r.url())) report.externalRequests.push(r.url());
    });
    await page.setViewport({width: 1280, height: 800});
    await page.goto(pathToFileURL(process.env.QIZHI_SIM_FILE).href, {waitUntil: 'load', timeout: 60000});

    // Implement [probe:A1], etc. here. Wait for an observable predicate, then assert it.
    // Use page.click / mouse drag / touchscreen paths rather than assigning model state.
    // Exercise the approved small viewport and reset/repeat run where applicable.
    // The template deliberately fails until real behavioral assertions are added.
    check('BEHAVIOR_IMPLEMENTED', report.checks.length > 0, 'Add the acceptance assertions before this line');

    if (process.env.QIZHI_SIM_PHASE === 'integration') {
      const state = await page.evaluate(() => {
        const api = window.qizhiCustomSim;
        return {snapshot: typeof api?.snapshot === 'function' ? String(api.snapshot()) : '', reset: typeof api?.reset === 'function'};
      });
      check('PLATFORM_SNAPSHOT', state.snapshot.length > 0 && state.snapshot.length <= 400);
      check('PLATFORM_RESET', state.reset);
    }
    // Keep these after every interaction: delayed requests/errors must not escape the report.
    check('NO_ERRORS', report.errors.length === 0, report.errors.join(' | '));
    check('OFFLINE', report.externalRequests.length === 0, report.externalRequests.join(' | '));
    await page.screenshot({path: path.join(path.dirname(process.env.QIZHI_CHECK_REPORT), 'final.png'), fullPage: true});
  } catch (e) {
    report.errors.push(String(e.stack || e));
    process.exitCode = 1;
  } finally {
    try { if (browser) await browser.close(); }
    catch (e) { report.errors.push('Browser cleanup: ' + e.message); }
    if (process.env.QIZHI_CHECK_REPORT) fs.writeFileSync(process.env.QIZHI_CHECK_REPORT, JSON.stringify(report, null, 2));
    if (report.errors.length || report.externalRequests.length || !report.checks.length || report.checks.some(c => !c.passed)) process.exitCode = 1;
  }
})();
