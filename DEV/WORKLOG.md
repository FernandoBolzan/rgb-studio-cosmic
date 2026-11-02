# Worklog

Record a short summary here after substantive work.

Use `HANDOFF.md` for the current snapshot and `HANDOFFS/WORKLOG_ARCHIVE.md` for older entries after compaction.

## 2026-11-02 - Mode handling and app audit

- Spec: `DEV/SPECS/ACTIVE.md`
- Changed: normalized mode matching and CLI errors; added per-device targets/all ARGB zones, per-zone LED counts, stricter scene restoration, atomic JSON writes, bilingual docs, and `DEV/APP_AUDIT.md`.
- Why: supported effects could be hidden or silently replaced; scenes could lose target/zone context; the first ARGB zone was the only one exposed.
- Verified: `python3 -m py_compile rgb_panel.py`, `git diff --check`, installed source SHA matches, service active/enabled and startup settings rewritten.
- Risks: no automated tests; effect capabilities and support remain OpenRGB/device-specific; no physical effect sweep.
- Next context: publish intended files to `origin/main` without staging `contrib/rgb-panel.service`; observe behavior on a full boot.

## 2026-11-02 - Restore saved RGB settings on startup

- Spec: `DEV/SPECS/ACTIVE.md`
- Changed: `rgb_panel.py`, both READMEs, and `CHANGELOG.md`; added compact `DEV/` project memory.
- Why: startup loaded the saved color into the UI but never sent the configuration to OpenRGB.
- Verified: `python3 -m py_compile rgb_panel.py`, `git diff --check`, service restart, and persisted startup state passed.
- Risks: legacy settings lack target/effect and first restore defaults to all devices.
- Next context: commit `246e7c3` was pushed to `origin/main`; observe the behavior after a full system boot and keep the service-unit user edit local.

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
