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

## Release Checklist

- Working tree reviewed.
- Release notes updated.
- Improvement log updated or intentionally skipped.
- Installed copy sync status known.
- User told which version future sessions will load.

