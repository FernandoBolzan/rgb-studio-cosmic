# Active Handoff

This file should stay small. Refresh it after substantive work or run `orquestrador-maestro compact-worklog`.

## Snapshot

- Updated: 2026-11-02
- Read order: `INDEX.md` -> `HANDOFF.md` -> `CONTEXT.md` -> `SPECS/ACTIVE.md`
- Active spec: `SPECS/ACTIVE.md`
- Verification source: `VERIFY.md`
- Worklog archive: `HANDOFFS/WORKLOG_ARCHIVE.md`

## Latest Work

- Entry: first versioned GitHub release `v0.1.0` published with updated bilingual README and changelog.
- Spec: `SPECS/ACTIVE.md`
- Changed: `rgb_panel.py`, regression tests, both READMEs, `CHANGELOG.md`, and app audit/architecture notes; release tag targets `161f6e0`.
- Verified: 4 unit tests; both DIMMs across 11 modes; generated frames for all 3 GPU effects through SDK; hardware restored to green; installed hash and service startup restore verified. See `VERIFY.md`.
- Risks: software GPU effects require RGB Studio to remain active; hardware behavior depends on OpenRGB and controller versions.
- Next context: observe startup restoration after a full boot; keep the pre-existing local service-unit edit uncommitted and see `APP_AUDIT.md` for follow-up work.

## Recent Entries

- 2026-11-02: GitHub release `v0.1.0` published; annotated tag and `main` release commit verified.
- 2026-11-02: Corsair DRAM and software GPU effects are installed and published as `c111bab`; service-unit edit remains local.
- 2026-11-02: startup restoration fix and documentation are on `origin/main` as `adc6b3a`.
- 2026-11-02: mode and scene reliability review installed locally and published as `838ccf9`; local service-unit edit remains uncommitted.
