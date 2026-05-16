# Skill Sync

Use this reference when a skill is edited in a repository but may also exist as an installed copy.

## Check

- Identify the edited source path.
- Identify the installed skill path when relevant.
- Compare whether they are the same directory.

## Report

If paths differ, say:

- repo/source version was updated;
- installed copy may still be older;
- syncing requires explicit approval before overwriting files.

## Sync Rules

- Do not overwrite installed skill files without user approval.
- Do not assume future sessions load the repo copy.
- Preserve user edits in the installed copy.
- Prefer a clear copy/sync step over manual partial edits.

## External Skill Intake

Before installing, copying, or recommending a third-party skill, plugin, MCP server, or agent bundle:

- Treat stars and popularity as discovery signals, not trust signals.
- Inspect `SKILL.md`, scripts, dependencies, install steps, licenses, recent maintenance, and open issues.
- Identify tool access, filesystem/network reach, credentials, external services, and generated commands.
- Reject or sandbox anything that handles untrusted input, executes broad shell commands, requests secrets, or has unclear provenance.
- Prefer official or already-installed skills when they cover the need with lower risk.

## Release Checklist

- Working tree reviewed.
- Release notes updated.
- Improvement log updated or intentionally skipped.
- `python scripts/test_all.py` run before syncing or committing meaningful skill changes.
- `python scripts/self_test.py` run when a focused marker check is enough.
- `python scripts/generate_dashboard.py` run when the user wants an operational status page or release/test evidence.
- `python scripts/serve_dashboard.py` used when the user wants the page to refresh while Codex sessions are active.
- `scripts/start_dashboard.ps1` and `scripts/stop_dashboard.ps1` preferred for non-technical local dashboard operation.
- `reports/dashboard-config.json` reviewed when project-specific dashboard checks should target a real app instead of the skill repo.
- Installed copy sync status known.
- User told which version future sessions will load.
