---
name: custom-sim
description: Develop, repair, review, and integrate non-PhET science simulations for the qizhi platform. Use for textbook-based experiments, existing custom-sim changes, or platform integration. Includes staged verification, evidence templates, and portable local checks.
---

# qizhi custom simulations

Build an accurate, explorable experiment for Chinese primary-school students. Honor the user's scope and existing approvals. Student-facing text is Chinese; follow the checkout's convention for developer-facing text.

## Start and route

1. Locate the user's qizhi checkout, read its `AGENTS.md`/`CLAUDE.md`, and inspect `git log --oneline -15` and `git status`. Preserve unrelated edits. Choose the requested branch workflow; use `codex/` only if the checkout calls for it.
2. Read [runtime.md](references/runtime.md) for this edition's invocation and tool mapping. Paths below are relative to **this skill directory**, except paths explicitly relative to the qizhi checkout. Always pass `--repo` to scripts; never infer the checkout from the skill's installation path.
3. For a grade/unit request, resolve the configured textbook before research or drafting: use `textbooks find`, or `textbooks list` and inspect/register an unmapped candidate. Follow [textbooks-and-preview.md](references/textbooks-and-preview.md). Ask for paths only when none are already supplied/configured. Clarify the intended lesson when several editions or activities match.
4. Choose the route below. Resume existing documents and `docs/custom-sims/<slug>/manifest.json` rather than overwriting them. Read only references relevant to this route.

| Request | Route |
| --- | --- |
| New experiment | Configured textbook → unit scope → online research → design/development documents → user revision and approval → demo preview/feedback loop → user satisfaction and integration authorization → platform adaptation and final preview |
| Model, variable, or learning-objective change | Re-read relevant evidence, revise affected design, obtain any missing substantive decision, implement and verify |
| Clear bug, copy, layout, or touch fix | Inspect existing behavior and tests, implement the narrow fix, run affected checks and update cache tags; do not restart research |
| Integrate an existing demo | Inspect the current file and its provenance, verify its behavior, agree on missing design decisions, then integrate |
| Explain or review this skill | Read and report only; do not initiate a simulation or create its ledger |

## Working agreement

- Propose a concrete design before asking for approval. Ask only when a missing decision affects learning objectives, scientific assumptions, scope, or an explicit preference. Resolve routine engineering choices independently. An approval already given in the conversation remains valid; no magic wording is required.
- For a new experiment, present the design, development specification and acceptance list; revise until the user approves, then implement. Design approval authorizes development; it is not acceptance of a page that has not been reviewed. Deliver a working preview after each Demo round and address feedback until the user explicitly accepts the page. Integrate only after that acceptance and authorization to integrate; “满意，可以接入” can establish both. A refinement request, silence or successful tests do not imply acceptance. Preserve prior explicit approval within its scope.
- Before committing/publishing, summarize the diff and use existing authorization; obtain missing authorization only for that action. Local integration is distinct from publishing to students.
- If the user is editing the sim, wait until they hand it back. Then re-read the current file and diff before changing it.
- Keep one canonical design and acceptance list; update them in place. Small fixes do not need new research documents. New experiments keep concise lesson/research notes, design, a development specification, and acceptance evidence in `docs/custom-sims/<slug>/` in the checkout. Keep textbooks, personal data, credentials, and bulky generated output out of Git.
- Use a developer agent and an independent reviewer when supported and appropriate for a substantial change. Give each explicit file ownership. For a small fix, work directly. If agents are unavailable, perform a separate review pass and report that it was not independent; a colleague can complete independent review. See [review-and-integration.md](references/review-and-integration.md).
- If two repair attempts make no progress on the same failure, report the reproduction, root-cause hypothesis, and decision needed. Continue independent work. Do not weaken assertions to turn results green or count ordinary productive iteration as a mandatory stop.

## Stages and evidence

Read [design-and-build.md](references/design-and-build.md) for textbooks, research, design, model boundaries, and UI decisions. Use the templates in `assets/` only when their artifact is needed.

For a new experiment, read actual textbook pages, then research mature comparable simulations online. Open relevant source pages rather than relying only on snippets; retain URLs and adoption/rejection reasons. If network/tools are unavailable, label research pending and obtain an explicit scope exception before skipping the requested research.

Deliver `01-lesson-research.md`, `02-design.md`, `03-acceptance.md`, and `04-development.md`. The development specification includes feature IDs, layout/controls, action → state → visible response, model rules/units, implementation order and feature-to-test mapping. Present these documents together and hand the approved revision to the developer. Existing v1.0 ledgers remain usable: for substantial redesign, create the development document and add its relative `development` path without overwriting previous evidence.

Before changing an existing experiment, initialize its manifest with a **baseline before the change**, or preserve an existing appropriate baseline. The immutable Git commit is how cache verification compares old and new content. Do not reset the baseline to a later commit to hide a missing version bump.

```text
python <skill-dir>/scripts/qizhi_sim.py --repo <qizhi-root> doctor
python <skill-dir>/scripts/qizhi_sim.py --repo <qizhi-root> init <slug> --owner <name> --file django_site/static/phet-sims/<final-name>.html
```

For changes already committed, pass `--base <commit-before-change>` to `init`. For an existing ledger, deliberately set `base_ref` to that commit before a new work cycle and record the reason in the acceptance notes; previous results become stale. `phase` is the human-maintained workflow stage, while `checks.phase` records the exact verification mode. Run `status` to distinguish them.

### Demo

Create the final flat, Chinese-prefixed filename in `django_site/static/phet-sims/`. Demo requires no `logEvent`, `qizhiCustomSim`, or platform registration. Do not remove those from an already-integrated sim during a repair.

Adapt `assets/probe.cjs` into the checkout's `phet-audit/` and implement the assertions promised by the acceptance list. The gate consumes a JSON report generated on **this run**, with unique IDs matching `[probe:ID]` entries. A success log alone is insufficient. Never implement a placeholder assertion such as `check('A1', true)`.

```text
python <skill-dir>/scripts/qizhi_sim.py --repo <qizhi-root> gate <slug> --phase demo
```

Every run writes its result to the ledger. Platform-only checks are explicitly not applicable. Review the visible result, screenshots, scientific claims, and probe meaning before presenting the demo for acceptance.

### Preview and refinement

After each checked Demo iteration, show an openable page with the host browser tools or provide the absolute HTML path and a verified local preview URL. `preview <slug> --serve` starts a loopback-only server; keep it alive while the user checks the page. Follow [textbooks-and-preview.md](references/textbooks-and-preview.md) for lifecycle and feedback handling. Include the revision, changes and concrete actions to try; a screenshot alone is not an interactive delivery.

Record feedback and its disposition in the acceptance document. Implement changes, run affected checks, update the design/development documents when behavior changes, and refresh the preview. Continue until the user is satisfied. When waiting for the user's observations, do not invent feedback or advance stages. The two-unproductive-repair rule is not a cap on ordinary feedback rounds.

Record actual page acceptance using `mark <slug> demo`, and integration authorization separately as `integration`; the same explicit statement may supply both. Never infer them from tests. Preserve user edits and re-read after handoff.

### Integration

Read [review-and-integration.md](references/review-and-integration.md). Add the marker after successful initialization, stable Chinese event labels, snapshot/reset, and optional inspect/persistence support. Finish catalog, prompts, element declarations, and `CUSTOM_SIMS` registration **before** asking any agent to pass the platform audit.

```text
python <skill-dir>/scripts/qizhi_sim.py --repo <qizhi-root> gate <slug> --phase integration
python <skill-dir>/scripts/qizhi_sim.py --repo <qizhi-root> status <slug>
```

The gate is evidence, not scientific approval. It checks subprocess exits, assertion coverage IDs, real registrations, audit output, bridge success, and actual cache versions against the baseline. It does not prove every assertion is meaningful or that a lesson is scientifically correct. If the checkout changes the supported config structure, it must fail clearly until the adapter is updated.

After the gate, open the actual local platform experiment page and verify iframe dimensions, controls, reset, optional ask-about-element, and task rules in student mode. Preserve existing database/environment settings and use authorized accounts. Fix platform-specific problems and provide a platform preview for review. If access is unavailable, report “contract checks passed; real platform adaptation pending” and the exact missing step. Record actual platform review with `mark <slug> platform`.

## Invariants

- Prefer a self-contained offline HTML. Inline authored CSS/JS and required libraries. Avoid CDN/fonts/network dependencies. If the user authorizes packaged local assets, track every asset and follow the checkout's deployment and version rules.
- A custom sim is one platform screen, index `1`, name `''`. If it has multiple benches, snapshot begins with the active bench. Do not introduce quizzes, scores, or gated steps unless explicitly part of the approved design.
- Emit literal Chinese operation labels and use the same event/label pairs in element declarations. Keep model changes and visible results consistent. Snapshot uses display units and fits the checkout's state budget (currently 400 characters); confirm the prompt budget (currently 300 characters including the prefix) in the checkout.
- Publish `window.qizhiCustomSim` only after initialization succeeds. A string within the last 4 KB is not evidence of initialization order; review ordering and exercise boot failures. `reset()` restores the expected initial behavior and permits a second run.
- Check real UI paths, not only internal variable assignments. Use deterministic seeds where needed; test trends, boundaries, repeatability, and off-path invariance according to the model, with numerical tolerances justified by sources.
- Bump each changed sim's effective `?v=` and changed shared scripts' template tags. Update the appropriate existing `README.md` or `AGENTS.md` with meaningful changes. Follow the checkout's migration, authentication, publication, and CSS rules; do not bypass them for a sim.

## Completion report

Report what changed, what was actually tested, links to evidence, remaining human checks, and whether the work is demo-ready or integration-ready. Never mark student trials, real-device checks, or user approvals as complete without evidence. See `scripts/qizhi_sim.py --help` and the repository README for installation and command details.
