// Evaluate the trusted checkout's pure element dictionary, without importing the app.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const [root, slug] = process.argv.slice(2);

// Preserve strings while removing comments so commented-out registrations cannot pass.
function withoutComments(source) {
  return source.replace(/("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`)|(\/\/[^\n]*|\/\*[\s\S]*?\*\/)/g,
    (match, quoted) => quoted || match.replace(/[^\n]/g, ' '));
}

try {
  if (!root || !slug) throw new Error('Usage: inspect-config.cjs <qizhi-root> <slug>');
  const source = fs.readFileSync(path.join(root, 'django_site/static/js/qizhi-phet-elements.js'), 'utf8');
  const context = vm.createContext({window: {}}, {codeGeneration: {strings: false, wasm: false}});
  vm.runInContext(source, context, {timeout: 2000});
  const config = context.window.QIZHI_PHET_ELEMENTS?.[slug]?.['1'];
  if (!config || !Array.isArray(config.operations) || !config.operations.length) throw new Error('Missing screen 1 operations');
  const seen = new Set();
  for (const op of config.operations) {
    if (!['button_press', 'select_change', 'value_change'].includes(op.event) ||
        typeof op.label !== 'string' || !/[\u3400-\u9fff]/.test(op.label)) throw new Error('Invalid event or non-Chinese operation label');
    const key = op.event + ':' + op.label;
    if (seen.has(key)) throw new Error('Duplicate operation ' + key);
    seen.add(key);
  }
  if (!Array.isArray(config.starters) || !config.starters.length ||
      config.starters.some(x => typeof x !== 'string' || !x.trim())) throw new Error('Provide non-empty starter questions');
  const audit = withoutComments(fs.readFileSync(path.join(root, 'phet-audit/audit.js'), 'utf8'));
  const match = /^\s*const\s+CUSTOM_SIMS\s*=\s*new\s+Set\s*\(\s*(\[[\s\S]*?\])\s*\)/m.exec(audit);
  if (!match) throw new Error('Cannot parse the literal CUSTOM_SIMS declaration; update the adapter');
  const stringsOnly = /^\[\s*(?:(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")\s*,?\s*)*\]$/;
  if (!stringsOnly.test(match[1])) throw new Error('CUSTOM_SIMS must be a literal string array');
  const slugs = vm.runInNewContext(match[1], {}, {timeout: 1000});
  if (!slugs.includes(slug)) throw new Error('Slug is absent from CUSTOM_SIMS');
  console.log('CONFIG OK: real screen 1 operations, starters and CUSTOM_SIMS entry');
} catch (e) {
  console.error('CONFIG FAILED: ' + e.message);
  process.exitCode = 1;
}
