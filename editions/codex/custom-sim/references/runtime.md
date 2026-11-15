# Codex edition

Install `custom-sim/` in the qizhi checkout's `.agents/skills/`, or `~/.agents/skills/` for user-wide availability. Explicit invocation is `$custom-sim`. Use a fresh session if the running client does not refresh newly installed skills.

Resolve `<skill-dir>` from this loaded SKILL.md. The project path is supplied by the user/session; do not confuse it with a global skill path. The skill is usable with local shell and file tools; browser/search and agent tools are optional capabilities provided by the user's runtime, not bundled services.

Use the available Codex file, shell, browser, search, and PDF tools by capability. No named MCP connector or external research skill is mandatory. For substantial work, where agent tools are enabled, spawn an implementation worker with explicitly owned files and a reviewer in a clean context. Give both enough source evidence. If delegation or visual tools are unavailable, disclose the remaining review work rather than claiming it happened.

Respect host permissions and existing authorization. A local skill does not grant network access, publication rights, or permission to edit outside allowed roots. The user may explicitly authorize a complete implementation or publication in the initial request; keep that authorization effective through the workflow.

Follow the checkout's branch and documentation conventions. The packaged commands work on macOS/Linux with `python3` and Windows with `py -3`; examples use `python` as a neutral placeholder.
