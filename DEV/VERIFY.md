# Verify

## Latest Verification

- Date: 2026-11-03
- Scope: application reliability review, persistent GPU SDK frames, robust device/settings parsing, and startup restoration.

## Commands

- `/usr/bin/python3 -m unittest discover -s tests -v` — 21 tests passed. Coverage includes Corsair mode color counts, GPU frame colors and SDK packet encoding/identity, malformed device lists/settings, type-based target grouping, stale SDK connection cancellation, delayed startup, and suspend/resume callbacks.
- `/usr/bin/python3 -m py_compile rgb_panel.py tests/test_rgb_panel_modes.py` — passed.
- `git diff --check` — passed.
- `gdbus introspect --system ... /org/freedesktop/login1` — previously confirmed logind's `PrepareForSleep(b)` signal contract.
- OpenRGB SDK probe — negotiated protocol 6, enumerated four server controllers, and resolved the Palit GeForce RTX 3060 as controller 3 by exact name and GPU type.
- User service logs — the first persistent-transport build completed two stable scans at 12:12:54 and 12:13:04, restored `device:3` in `software:breathe`, and logged the first successful frame at 12:13:09. The latest build repeated startup restoration at 12:19:17 after scans at 12:19:02 and 12:19:12.
- Sustained run — persistent-transport build observed from 12:13:09 through 12:16:41 (3m32s) with `NRestarts=0` and no new timeout/error logs. The latest build ran through 12:20:30 (1m13s after restore) with `NRestarts=0`; process inspection showed only the Python app and SDK server, no CLI client.
- Saved preferences still target Palit `device:3`, green `#2EFF00`, software `Breathe`, brightness 100, speed 100, and `restore_on_startup=true`.
- Installed source matches the repository; both SHA-256 values are `b2508f3718706422e91ae8c00080d33229b3c87604ba3b7a5f06fdb2bb45e729`.
- Prior physical verification exercised all 11 advertised modes on both Corsair DIMMs and Blink/Breathe/Rainbow frames on the Palit GPU; saved lighting was restored afterward.
- A real sleep/resume cycle after the current fix — pending; callback tests and D-Bus introspection do not substitute for hardware wake verification.

## Outcome

- Passed: 21 regression tests, compilation, whitespace checks, stale-connection cancellation, SDK protocol negotiation/controller identity, saved GPU effect restoration, and the sustained animation run without timeout errors.
- Failed: none in automated verification or the observed service interval.
- Pending: verify the next real suspend/resume cycle; hardware behavior depends on OpenRGB and controller versions.
- Published baseline: Corsair/GPU mode work is on `origin/main` as `c111bab`; the earlier mode audit is `838ccf9`; startup restoration is in its published history.
- Release `v0.1.1` contains these verified changes. The pre-existing service-unit edit is preserved locally and excluded from the release.

## Release v0.1.1

- Published GitHub release: https://github.com/FernandoBolzan/rgb-studio-cosmic/releases/tag/v0.1.1
- Annotated tag `v0.1.1` targets the release commit on `main`.
- No database/config migrations or binary attachments; GitHub provides the source archives.
- Rollback: no data migration to reverse; `v0.1.0` remains the prior release.
- Monitoring/owner: no telemetry is configured; the project maintainer can monitor the user service (`systemctl --user status rgb-panel.service`) and user reports.

## Release v0.1.0

- Published GitHub release: https://github.com/FernandoBolzan/rgb-studio-cosmic/releases/tag/v0.1.0
- Annotated tag `v0.1.0` points to `161f6e0`; `main` and the tag were confirmed on `origin`.
- First versioned release; no database/config migrations or binary attachments. GitHub provides the source archives.
- Compatibility and runtime requirements are documented in both READMEs; hardware verification used OpenRGB 1.1 on Pop!_OS with the local Corsair DIMMs and Palit GPU.
- Rollback: no data migration to reverse. If a release regression appears, ship a corrective `v0.1.1`; the pre-release source state is commit `7d5da60`.
- Monitoring/owner: no telemetry is configured; the project maintainer can monitor the user service (`systemctl --user status rgb-panel.service`) and user reports.
