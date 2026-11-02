# Worklog

Record a short summary here after substantive work.

Use `HANDOFF.md` for the current snapshot and `HANDOFFS/WORKLOG_ARCHIVE.md` for older entries after compaction.

## 2026-11-02 - Corsair DRAM and GPU effects

- Spec: `DEV/SPECS/ACTIVE.md`
- Changed: Corsair per-mode color counts; software GPU Blink/Breathe/Rainbow and SDK readiness; regression tests; bilingual docs.
- Why: the memory controller rejected one-color payloads for five modes; the Palit GPU exposes only Direct/Off natively.
- Verified: 3 unit tests passed; both DIMMs accepted all 11 modes; GPU accepted sampled frames for all three effects; hardware restored to green memory Color Pulse and GPU Direct.
- Risks: software GPU effects require RGB Studio to remain running; support varies with OpenRGB and controller versions.
- Next context: install current source, restart service to verify saved memory restore, refresh `VERIFY.md`/`HANDOFF.md`, then publish intended paths only; preserve the service-unit edit.

## 2026-11-02 - Mode handling and app audit

- Spec: `DEV/SPECS/ACTIVE.md`
- Changed: normalized mode matching and CLI errors; added per-device targets/all ARGB zones, per-zone LED counts, stricter scene restoration, atomic JSON writes, bilingual docs, and `DEV/APP_AUDIT.md`.
- Why: supported effects could be hidden or silently replaced; scenes could lose target/zone context; the first ARGB zone was the only one exposed.
- Verified: `python3 -m py_compile rgb_panel.py`, `git diff --check`, installed source SHA matches, service active/enabled and startup settings rewritten.
- Risks: no automated tests; effect capabilities and support remain OpenRGB/device-specific; no physical effect sweep.
- Next context: commit `838ccf9` is on `origin/main`; observe restoration after a full boot and keep the local service-unit change uncommitted.

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
