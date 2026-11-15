# Review and platform integration

## Independent review method

Provide the approved design and development specification/model sources, acceptance list, sim path, **probe source path**, current logs, and screenshots. A clean reviewer should not inherit the developer's claimed verdict or repair history, but needs enough evidence to assess correctness. Ask it to:

1. Map each `[probe:ID]` to its actual assertion and confirm actions/results are meaningful, not constant true values or copied model calculations.
2. Open the browser and inspect `[visual:ID]` conditions at the relevant viewports and modes. Without a browser or screenshots, mark visual items unverified.
3. Read source by search first, then complete relevant functions and callers. Do not impose an arbitrary ±20-line cap or load bundled third-party code unnecessarily.
4. Report reproducible findings with severity, location, expected/actual result, and the smallest correction. The developer implements fixes; the reviewer verifies them.

Use a separate agent with a clean context when the runtime supports it; otherwise disclose a separate self-review or request a colleague's review at the final acceptance point. Give workers explicit file ownership and instruct them to preserve others' edits. Do not hand all integration files to multiple agents at once.

## Ordered integration

First verify the conversation/evidence contains acceptance of the reviewed Demo and authorization to integrate. Design approval alone is insufficient. Honor an existing statement that covers both, without asking twice. For an already-integrated experiment repair, use the user's existing repair authorization rather than treating it as a new Demo.

1. The developer re-reads the user-edited HTML, then adds `logEvent`, snapshot/reset, and the marker after successful initialization. Preserve the approved experiment. Optional persistence must use the actual platform contract, with reload/reset checks; do not invent a new backend.
2. The main session (or one explicitly assigned integration worker) changes the following together:

| Location in qizhi | Required change |
| --- | --- |
| `django_site/static/phet-sims/<final-name>.html` | Final flat filename and standalone sim contract |
| `django_site/phet/views.py` | One `PHET_SIMS` entry with matching `static_file`; actual per-sim cache version in `get_phet_sims()` |
| `django_site/phet/prompts.py` | Source-grounded `PHET_SIM_PROMPTS[slug]`, within the actual S2 budget including prefix |
| `django_site/static/js/qizhi-phet-elements.js` | Screen `"1"`: whitelisted `{event,label}` operations, nonempty starters (normally 2–3; preserve justified existing choices), optional inspect cards with `match.domKeys` |
| `phet-audit/audit.js` | Actual slug in `CUSTOM_SIMS` |
| `django_site/templates/phet/phet_sim.html` | New `?v=` for changed elements.js or other referenced scripts |
| Existing `README.md` / `AGENTS.md` | Appropriate feature/setup or mechanism note |

3. Only after registration is complete, run the real `audit.js`, real bridge verifier, and the integration gate. The builder cannot fix missing registration by repeatedly rewriting HTML.

The real bridge verifier normally starts from the checkout's `verify-bridge-water.js` or a newer matching example. Exercise marker boot (not loading timeout), `sim_load`, one-screen replay, nonempty bounded snapshot delegation, reset and a second run, every declared event/label, and every visible inspect target's real `elementFromPoint(...).closest(...)` hit. If persisting progress, check reload, task/session isolation, and reset clearing. Assertions must fail the process with a nonzero exit; print `VERIFY OK` only when all assertions pass. Cleanup must run in `finally`.

Custom sims do not expose PhET Properties/watchlists. Task rules use the sim's declared events on screen 1. DOM inspect is optional, but marked targets must map to actual cards and be hit-testable in the relevant mode. Adding a catalog entry is not publishing to students: use the checkout's admin publication workflow with authorization.

4. After contract checks, open the actual local Django experiment page using its configured environment/database and authorized session. Check iframe size, scroll/touch conflicts, reset/reload, current snapshot, ask-about-element when present, and task rules in student mode. Fix integration-specific issues and show the adapted page to the user. If local Django/session access is missing, record the exact blocker and pending checks; passing a no-Django wrapper is not real-platform acceptance. Do not publish to students as part of this verification without authorization.

## Gate and report contract

The portable Python gate replaces the old shell gate. No Bash, Django import, or API key is required. It checks:

- Demo: files, fresh JSON probe report, every acceptance assertion ID, errors and remote requests after all interactions.
- Integration: all Demo checks plus AST-read Python catalog/prompts, evaluated pure JS element dictionary, literal `CUSTOM_SIMS`, audit exit **and** output, bridge exit **and** success marker, effective cache tags compared to the immutable baseline.

Python source is parsed, not imported. The version adapter supports the current `get_phet_sims()` per-sim `if/elif` selectors (`==`, `in`, boolean combinations). Unknown structures fail explicitly. JavaScript inspection runs the trusted checkout's pure dictionary in a bounded Node VM; it is not a security sandbox for untrusted repositories. `CUSTOM_SIMS` must be a literal string array. Do not broaden matching to pass an unsupported schema; update the adapter and its regression tests.

The probe writes to `QIZHI_CHECK_REPORT` with `checks: [{id, passed, detail}], errors: [], externalRequests: []`. The gate sets `QIZHI_SIM_FILE` and `QIZHI_SIM_PHASE`. Keep each `passed` a boolean and every ID unique. Use the included template; legacy probes can retain their existing assertions and add this report contract. A legacy success log alone deliberately fails.

Every gate run overwrites its machine result, including ordinary missing-source/script and timeout failures. File/config validation errors return nonzero and are shown by status as invalid/stale rather than a fresh pass. Fingerprints cover the sim, probes, evidence docs, platform files, manifest settings, and skill scripts. Changed inputs mark verification results stale; actual design/Demo/integration/commit decisions remain historical evidence with a scope-change note. Design/Demo decisions compare their reviewed artifact hashes. Fingerprints are not a security guarantee or a substitute for review. `status` never treats missing evidence as passed. Human items support pass/fail/pending/not_applicable with a person and evidence; record only actions actually performed.

## Human acceptance and completion

Automate task-rule triggering and CSV schema/value consistency when fixtures make that practical. Real device usability, student comprehension, and actual class trials still need people. Verify task cards in student mode, not author preview. Pending classroom trials do not prevent a clearly labelled local demo or authorized development commit, but must not be reported as completed deployment validation.

Before final review, ensure console/network checks ran **after** interactions, visual evidence covers the target sizes, and the current fingerprint matches the checked content. Present changed files, model limitations, measurements, machine results, and pending human items. Honor prior explicit commit/push authorization; never auto-publish to a classroom just because a local integration gate passes.
