# Evidence, design, and implementation

## Textbooks and research

Reuse supplied PDFs, paths, and extracted lesson notes. Ask for missing sources only after checking the material already provided. Never assume a username, Desktop layout, textbook publisher, or grade mapping. Check each PDF's text layer; scanned material requires rendered-page reading/OCR and verification.

Record edition, book, lesson, printed page, and PDF physical page separately. Look at diagrams for apparatus, connections, materials, and observed phenomena even when a text layer exists. Quote only the relevant activity excerpt, identify its column (focus/exploration/discussion/extension), and separate quotation from interpretation. Verify the applicable curriculum edition rather than carrying an old code forward.

Research comparable interactions using available search/browser tools. Each useful conclusion includes its URL/source, what was observed, and why to adopt/reject it. A compact summary is enough; retain citations rather than dumping raw results. Finding no suitable precedent is a valid result. Compare an existing PhET experiment against the actual approved goal; do not replace a request for a custom sim solely because an embed exists. Reuse interaction ideas; include external art/code only with a verified applicable license and attribution.

## Design approval

The first section states: lesson and pages; scope; student-controlled variables; fixed variables; observables; explicitly excluded features; chosen interaction. Then specify:

- Learning objective and curriculum evidence.
- A complete student path, including recoveries, reset, and repeated runs.
- Model rules, units, source-backed constants, estimated values, random seed policy, and limitations.
- Appropriate rendering (2D/3D), apparatus, and responsive layout.
- Acceptance conditions: setup → real action → observable result → scientific basis → evidence ID.

Use `[probe:A1]` for automated assertions and `[visual:V1]` for screenshot/browser review. Numerical thresholds must come from a source, calculation, or explicitly justified modeling choice; never derive the expected answer only from the implementation being tested. Visual review can cover labels, diagrams, timing, and legibility; hit testing, overflow, and target sizes can also be automated.

Present the proposed design and unresolved consequential choices together. Ordinary implementation decisions do not need repeated approval. When a requirement changes, update the design and acceptance list before claiming the implementation meets it.

## Implementation

Use `docs/demo/` layouts and the checkout's current title convention when present. If missing, explain and use a small equivalent layout; the skill package deliberately does not redistribute the platform's art/templates. Start from a fitting shell and delete irrelevant controls, dialogs, and dead CSS. Keep visible keyboard focus, keyboard-operable DOM controls, usable touch targets (normally at least 44 CSS px), and operable controls at the design's supported viewport sizes. Test on both sides of the actual breakpoint and inside the platform iframe; 900 px is an existing convention, not a proof of tablet usability.

Concentrate adjustable constants; explain non-obvious scientific decisions. Keep state ownership explicit, pause deterministic, reset complete, and rendering synchronized after every mutation. Use the checkout's documented experience only where it applies.

Animation should reveal a process, direction, delay, or cause. A static equilibrium need not move. Make controlled-variable differences visible without blocking exploration, unless the approved task requires a restriction. Each designed component needs an observable purpose; that may be a qualitative effect rather than an invented numerical meter.

Examples of conditional rules:

- Infectious-disease models: distinguish attack rate from peak demand; gate interventions by route and test off-route invariance with the same seed.
- Erosion comparisons: a rate may be a fairer metric than a total when durations vary. This is not a universal rule for every experiment.
- Stochastic models: changing the seed requires rechecking the conclusions and relevant probe expectations, comments, and teacher prompt.

Run real clicks, drags, slider changes, pause/resume, reset, and repeated runs as relevant. For touch-dependent experiments include touch input, cancellation, scrolling conflicts, and real-device follow-up. A screenshot alone does not test dragging; changing an internal variable does not test a pointer path.

## Evidence size

Keep the three concise lesson/design/acceptance documents in the experiment's docs folder. Small repairs update existing documents instead of creating another set. Store generated logs/screenshots under `phet-audit/out/skill/<slug>/`; summarize key measurements in the acceptance document. Do not commit copyrighted textbooks, student exports, device profiles, or personal absolute paths.
