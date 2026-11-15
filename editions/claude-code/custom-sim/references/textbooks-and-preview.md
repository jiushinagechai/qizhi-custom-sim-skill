# Local textbooks and the user preview loop

## One-time textbook setup

Run commands as the agent using supplied paths. The user can say “my textbooks are in this folder”; do not require them to maintain JSON. Configuration is stored in the checkout's `.qizhi-sim.local.json`, outside the installed skill, so upgrading either edition preserves it. Both editions share the mapping. The tool adds a local Git exclude rule and refuses to store paths in an already-tracked config. Do not force-add it or copy it into shared documentation.

```text
python <skill-dir>/scripts/qizhi_sim.py --repo <qizhi-root> textbooks configure --directory <folder> --curriculum <curriculum.pdf>
python <skill-dir>/scripts/qizhi_sim.py --repo <qizhi-root> textbooks list
python <skill-dir>/scripts/qizhi_sim.py --repo <qizhi-root> textbooks add --id science-5a --grade 5 --semester 上 --publisher <publisher> --edition <edition> --file <book.pdf>
python <skill-dir>/scripts/qizhi_sim.py --repo <qizhi-root> textbooks find --grade 5 --semester 上
```

Directory and curriculum can be configured separately. Relative PDF paths resolve against the configured directory; absolute paths also work. `add` maps a verified book. Inspect its cover/contents to establish publisher, edition and grade. The script checks file existence and PDF extension; PDF content reading/OCR and unit interpretation remain the agent's work.

`list` inventories PDFs and existing mappings. `find` filters by grade and optional semester/publisher/edition, returning all candidates with `selection_required`. Never silently select the first ambiguous match. If a file moved, update it deliberately with `add --replace`. Changing the root preserves existing verified absolute mappings; it does not guess the new location.

After selecting a book, read the table of contents and relevant unit pages. A unit may contain several lessons/experiments: show the candidate activities and confirm the requested experiment or combined scope. Record book ID/edition, printed and physical PDF pages, diagram observations and curriculum evidence in the lesson document, keeping personal absolute paths only in the local config. Reuse extracted text when appropriate, but inspect actual diagrams.

## Document revision and handoff

Read textbook → research mature comparable simulations online → write design, development spec and acceptance list → present the proposal and saved document links. Ask for feedback on a concrete student experience. Revise the same files until approved, retain a short decisions table, and identify the approved revision. No implementation starts while a consequential design question awaits the user's answer.

The development specification must be sufficient for another agent without chat history: apparatus, controls, states, causal rules, parameters and units, responsive layout, feature IDs, reset semantics and test mapping. Give it and the design/acceptance list to the developer. Keep it proportional to the experiment rather than creating technical layers for their own sake.

## Openable preview

```text
python <skill-dir>/scripts/qizhi_sim.py --repo <qizhi-root> preview <slug>
python <skill-dir>/scripts/qizhi_sim.py --repo <qizhi-root> preview <slug> --serve
```

The first command prints the absolute HTML path, file URL and SHA-256; it does not record acceptance. The second is a foreground long-running command: launch it in a managed terminal/background session, retain its process/session ID, and read its first JSON line for the actual URL. Port 0 selects a free port; `--port` chooses a fixed one. It binds only to `127.0.0.1`, serves the simulation directory, disables directory listing and adds `Cache-Control: no-store`. Never serve the repository/textbook root or bind to the LAN by default.

Use the host's browser-opening capability when available and confirm the expected page loads. Keep the server alive across review turns; do not block waiting for it to exit. Reuse the working server and refresh after edits; if it stopped, restart it and deliver the new URL. Stop only the process you own when it is no longer needed. A localhost URL works on its serving machine; use the host's supported port-forwarding/preview for remote sessions or deliver the HTML and explain the limitation. Do not claim a browser was opened unless a tool confirms it.

Each round delivers the preview link/path, current revision/hash, changes, actual checks and 2–4 useful actions to try. Screenshots supplement the interactive page.

## Feedback and decisions

Use the acceptance document's table: user observation → correction → evidence → resolved/pending. Continue until the page satisfies the user. Implementation refinements stay in the Demo loop; changed teaching goals/variables/model boundaries require updating and confirming the affected design. Do not repeatedly approve unchanged decisions.

| Decision | Meaning |
| --- | --- |
| Design approved | Develop the agreed documents; no claim about an unseen page |
| Demo accepted | User inspected and is satisfied with the current page |
| Integration authorized | Proceed with platform changes; one statement can accept Demo and authorize this |
| Platform reviewed | Actual embedded experiment checked; pending items stated |

`mark` supports `design`, `demo`, `integration`, and `platform` with person and evidence. Design/Demo records include artifact hashes. Record the actual statement and revision, never fabricate satisfaction from silence, a refinement request or test results. `STALE` marks outdated machine/device verification. Recorded design, Demo, integration and commit decisions keep their original status; status adds a historical-content-change note instead of revoking them. Design/Demo use their recorded artifact hashes, so unrelated platform files do not invalidate their scope. Limit any re-review to relevant changes. After adding a platform contract, review the adapted platform page instead of demanding duplicate design approval.

While the user edits HTML, do not change it. On handoff, re-read it and refresh affected evidence instead of regenerating from an older version.
