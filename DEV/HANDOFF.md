# Active Handoff

This file should stay small. Refresh it after substantive work or run `orquestrador-maestro compact-worklog`.

## Snapshot

- Updated: 2026-11-02
- Read order: `INDEX.md` -> `HANDOFF.md` -> `CONTEXT.md` -> `SPECS/ACTIVE.md`
- Active spec: `SPECS/ACTIVE.md`
- Verification source: `VERIFY.md`
- Worklog archive: `HANDOFFS/WORKLOG_ARCHIVE.md`

## Latest Work

- Entry: Corsair DRAM effects now send the required color count; Palit GPU gets software Blink/Breathe/Rainbow.
- Spec: `SPECS/ACTIVE.md`
- Changed: `rgb_panel.py`, regression tests, both READMEs, `CHANGELOG.md`, and app audit/architecture notes.
- Verified: 4 unit tests; both DIMMs across 11 modes; generated frames for all 3 GPU effects through SDK; hardware restored to green; installed hash and service startup restore verified. See `VERIFY.md`.
- Risks: software GPU effects require RGB Studio to remain active; hardware behavior depends on OpenRGB and controller versions.
- Next context: publish intended code/test/docs paths to `origin/main`; preserve the pre-existing local service-unit edit.

## Recent Entries

- 2026-11-02: startup restoration fix and documentation are on `origin/main` as `adc6b3a`.
- 2026-11-02: mode and scene reliability review installed locally and published as `838ccf9`; local service-unit edit remains uncommitted.
