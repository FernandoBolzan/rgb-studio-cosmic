# Active Handoff

This file should stay small. Refresh it after substantive work or run `orquestrador-maestro compact-worklog`.

## Snapshot

- Updated: 2026-11-03
- Read order: `INDEX.md` -> `HANDOFF.md` -> `CONTEXT.md` -> `SPECS/ACTIVE.md`
- Active spec: `SPECS/ACTIVE.md`
- Verification source: `VERIFY.md`
- Worklog archive: `HANDOFFS/WORKLOG_ARCHIVE.md`

## Latest Work

- Entry: release `v0.1.1` packages persistent GPU SDK frames and startup/settings hardening.
- Spec: `SPECS/ACTIVE.md`
- Changed: `rgb_panel.py`, regression tests, both READMEs, `CHANGELOG.md`, and developer documentation.
- Verified: 21 unit tests, compilation, whitespace checks, stale-connection cancellation, logind monitoring, persistent SDK protocol 6 connection, saved Palit `Breathe` restoration, a 3m32s transport run without timeout, and matching installed-source hash. Latest build restored again and stayed active for 1m13s. See `VERIFY.md`.
- Risks: no actual sleep/resume cycle has been performed in this run; hardware behavior depends on OpenRGB and controller versions.
- Next context: observe a real resume cycle; preserve the pre-existing service-unit edit.

## Recent Entries

- 2026-11-03: replaced per-frame GPU CLI calls with a persistent SDK client; hardened settings/device parsing and grouping; invalidated stale SDK work across sleep; restored saved GPU Breathe and observed 3m32s without timeout.
- 2026-11-03: released `v0.1.1` with startup/resume, persistent GPU SDK, and settings/device parsing fixes.
- 2026-11-03: added delayed-device startup retries and logind sleep/resume restoration; installed locally and verified startup reapplication.
- 2026-11-02: GitHub release `v0.1.0` published; annotated tag and `main` release commit verified.
- 2026-11-02: Corsair DRAM and software GPU effects are installed and published as `c111bab`; service-unit edit remains local.
- 2026-11-02: startup restoration fix and documentation are on `origin/main` as `adc6b3a`.
- 2026-11-02: mode and scene reliability review installed locally and published as `838ccf9`; local service-unit edit remains uncommitted.
