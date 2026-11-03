# Active Handoff

This file should stay small. Refresh it after substantive work or run `orquestrador-maestro compact-worklog`.

## Snapshot

- Updated: 2026-11-03
- Read order: `INDEX.md` -> `HANDOFF.md` -> `CONTEXT.md` -> `SPECS/ACTIVE.md`
- Active spec: `SPECS/ACTIVE.md`
- Verification source: `VERIFY.md`
- Worklog archive: `HANDOFFS/WORKLOG_ARCHIVE.md`

## Latest Work

- Entry: per-device RGB profiles fix the hibernation case where only the last saved target was restored.
- Spec: `SPECS/ACTIVE.md`
- Changed: `rgb_panel.py`, regression tests, both READMEs, `CHANGELOG.md`, and developer documentation.
- Verified: the real resume log showed only GPU `device:3` restored because preferences held one target; 28 tests pass, and the installed fix restored the motherboard, both DIMMs, and GPU on service restart. See `VERIFY.md`.
- Risks: a real hibernation cycle after the new fix remains to be observed; hardware behavior depends on OpenRGB and controller versions.
- Next context: confirm all four profiles after the next real hibernation; preserve the pre-existing service-unit edit.

## Recent Entries

- 2026-11-03: replaced per-frame GPU CLI calls with a persistent SDK client; hardened settings/device parsing and grouping; invalidated stale SDK work across sleep; restored saved GPU Breathe and observed 3m32s without timeout.
- 2026-11-03: released `v0.1.1` with startup/resume, persistent GPU SDK, and settings/device parsing fixes.
- 2026-11-03: diagnosed real hibernation partial restoration; the legacy settings format persisted only one target. Added per-device profile migration and multi-target restore for `v0.1.2`.
- 2026-11-03: added delayed-device startup retries and logind sleep/resume restoration; installed locally and verified startup reapplication.
- 2026-11-02: GitHub release `v0.1.0` published; annotated tag and `main` release commit verified.
- 2026-11-02: Corsair DRAM and software GPU effects are installed and published as `c111bab`; service-unit edit remains local.
- 2026-11-02: startup restoration fix and documentation are on `origin/main` as `adc6b3a`.
- 2026-11-02: mode and scene reliability review installed locally and published as `838ccf9`; local service-unit edit remains uncommitted.
