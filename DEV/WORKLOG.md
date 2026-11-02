# Worklog

Record a short summary here after substantive work.

Use `HANDOFF.md` for the current snapshot and `HANDOFFS/WORKLOG_ARCHIVE.md` for older entries after compaction.

## 2026-11-02 - Restore saved RGB settings on startup

- Spec: `DEV/SPECS/ACTIVE.md`
- Changed: `rgb_panel.py`, both READMEs, and `CHANGELOG.md`; added compact `DEV/` project memory.
- Why: startup loaded the saved color into the UI but never sent the configuration to OpenRGB.
- Verified: `python3 -m py_compile rgb_panel.py`, `git diff --check`, service restart, and persisted startup state passed.
- Risks: legacy settings lack target/effect and first restore defaults to all devices.
- Next context: commit and push intended files; keep the service-unit user edit out of the commit.

## Template

```text
## YYYY-MM-DD - Short task title

- Spec: `DEV/SPECS/ACTIVE.md` or equivalent task doc
- Changed: paths or areas touched
- Why: one sentence
- Verified: command or manual check
- Risks: only active risks
- Next context: only what the next AI needs
```
