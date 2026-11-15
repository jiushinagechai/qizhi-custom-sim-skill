# Claude Code edition

Install `custom-sim/` in the qizhi checkout's `.claude/skills/`, or `~/.claude/skills/` for user-wide availability. Explicit invocation is `/custom-sim`. Start a fresh session if the running client does not discover the installation immediately.

Resolve `<skill-dir>` from this loaded SKILL.md. Always pass the actual qizhi checkout with `--repo`, including when the skill is installed globally. This package uses ordinary Read/Edit/Write and shell capabilities. Browser, PDF, search, and subagent tools depend on the user's environment; no paid connector or named third-party skill is mandatory.

The project installer also installs `.claude/agents/sim-builder.md`. Use it for substantial implementation work, specifying demo or integration mode and owned files. A general reviewer agent should receive requirements, model evidence, acceptance criteria, source paths, and logs in a fresh context. Do not give it only the author's verdict. If agent tools are unavailable, do the work directly and label independent review as pending.

Honor the user's permissions and prior approvals. Do not use bypass-permissions modes. Changes outside approved roots, network operations, and publication follow the host's normal permission system. Prefer existing authorization over repeated checkpoint questions.

Examples use `python`; use `python3` on macOS/Linux or `py -3` on Windows when needed. The workflow scripts do not require Bash.
