# Worklog

Record a short summary here after substantive work.

Use `HANDOFF.md` for the current snapshot and `HANDOFFS/WORKLOG_ARCHIVE.md` for older entries after compaction.

## 2026-11-03 - Restore every configured component after hibernation

- Spec: `DEV/SPECS/ACTIVE.md`
- Changed: persist per-device profiles, migrate the legacy single target, restore motherboard/memory/GPU profiles independently, and document the behavior.
- Why: real resume logs showed that the app restored only GPU `device:3`; the old settings format overwrote earlier device targets.
- Verified: 28 tests, compilation, whitespace checks, matching installed-source hash, and service logs showing ASUS Direct, both Corsair Color Pulse profiles, and Palit Breathe restored with `NRestarts=0`.
- Risks: a real hibernation cycle after the fix remains pending; the motherboard's lost legacy effect was not in the old settings, so the user approved green Direct as its recovered profile.
- Next context: verify the next hibernation; preserve the local service-unit edit.

## 2026-11-03 - Restore RGB lighting after startup and resume

- Spec: `DEV/SPECS/ACTIVE.md`
- Changed: retry device discovery at startup; listen for logind suspend/resume; pause GPU software effects and active OpenRGB clients before sleep; restart SDK and restore saved settings after wake; update tests and user/developer docs.
- Why: the service stays running through sleep, so its startup restore never reruns after the hardware resets; late device discovery also had no retry path.
- Verified: 12 unit tests, compilation, whitespace check, logind signal introspection, active user service, matching installed-source hash, and successful restoration of the saved GPU `Breathe` mode after service restart.
- Risks: actual resume-cycle verification remains pending.
- Next context: observe the next real resume cycle; keep `contrib/rgb-panel.service` user edit untouched.

## 2026-11-03 - Stabilize GPU animation and review application reliability

- Spec: `DEV/SPECS/ACTIVE.md`
- Changed: persistent OpenRGB SDK frame client with controller identity checks; resilient settings/device parsing; type-based device grouping; stale-connection cancellation across sleep; tests and bilingual user/developer documentation.
- Why: the previous GPU Breathe implementation launched one CLI client per frame and logged recurring 45-second timeouts; malformed settings or name collisions could also break startup/targeting.
- Verified: 21 unit tests, compilation, whitespace checks, SDK 6 negotiation, Palit startup restoration, matching installed-source hash, a 3m32s transport run without timeout, and repeat startup restoration on the latest build.
- Risks: actual sleep/resume cycle remains untested; interactive animation stops with an error if its SDK connection is lost mid-run.
- Next context: observe a real resume cycle; preserve the existing service-unit edit.

## 2026-11-03 - Release v0.1.1

- Spec: `DEV/SPECS/ACTIVE.md`
- Changed: versioned the changelog, pinned both READMEs to the release tag, and recorded release verification and rollback details.
- Why: publish the startup/resume restoration and persistent GPU SDK fixes as a traceable patch release.
- Verified: 21 unit tests, Python compilation, whitespace checks, release tag and main branch publication.
- Risks: a real sleep/resume cycle remains untested; hardware behavior depends on OpenRGB and controller versions.
- Next context: monitor the next real resume cycle and preserve the pre-existing service-unit edit.

## 2026-11-02 - Release v0.1.0

- Spec: `DEV/SPECS/ACTIVE.md`
- Changed: structured bilingual changelog, README version/release links, and pinned installation instructions.
- Why: publish the first traceable version of RGB Studio with clear compatibility and feature notes.
- Verified: 4 unit tests, Python compilation, whitespace checks, annotated tag target, and GitHub latest release.
- Risks: release is pre-1.0; hardware support remains OpenRGB/controller-specific; no binary package is attached.
- Next context: release `v0.1.0` is live; monitor service behavior and user reports, preserve the existing local service-unit edit.

## 2026-11-02 - Corsair DRAM and GPU effects

- Spec: `DEV/SPECS/ACTIVE.md`
- Changed: Corsair per-mode color counts; software GPU Blink/Breathe/Rainbow and SDK readiness; regression tests; bilingual docs.
- Why: the memory controller rejected one-color payloads for five modes; the Palit GPU exposes only Direct/Off natively.
- Verified: 4 unit tests passed; both DIMMs accepted all 11 modes; GPU accepted sampled frames for all three effects; hardware restored to green memory Color Pulse and GPU Direct.
- Risks: software GPU effects require RGB Studio to remain running; support varies with OpenRGB and controller versions.
- Next context: commit `c111bab` is on `origin/main`; observe restoration after a full boot and preserve the local service-unit edit.

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
