# Active Spec - rgb-panel

## Goal

Review and improve RGB Studio's lighting-mode reliability and overall device/scene handling, then install and publish the reviewed correction to `main`.

## In Scope

- Resolve mode names case-insensitively while preserving each device's advertised spelling.
- Stop silently replacing unsupported effects; report CLI failures even when OpenRGB exits successfully.
- Explain common-mode filtering for grouped targets and expose each device's advertised modes.
- Discover all reported addressable ARGB zones and store LED counts per zone.
- Preserve target and zone count in scenes; reject stale target or mode references.
- Make settings and scene JSON writes atomic.
- Review repository history, issues, pull requests, and OpenRGB CLI behavior; record findings and follow-on improvements.
- Install the verified app and publish the code/docs correction to `origin/main`, excluding the pre-existing service edit.

## Out Of Scope

- Cycling effects on physical hardware during verification.
- Implementing the longer-term backlog in `DEV/APP_AUDIT.md` (SDK capability discovery, test/CI suite, module split, or packaging).

## Acceptance

- Advertised mode names match regardless of capitalization and the device-native name reaches OpenRGB.
- A selected mode unsupported by any device in its target fails clearly without silently choosing another mode.
- Grouped targets show common effects; individual device and ARGB zone targets show their respective advertised effects.
- Each detected addressable zone has an independent remembered LED count, and existing global zone-count settings remain readable.
- Scenes restore their component, effect, and zone count; stale component/effect references produce an actionable error.
- Syntax and whitespace checks pass, the local service runs the installed source, and the published commit excludes `contrib/rgb-panel.service`.

## Constraints

- Preserve the existing uncommitted edit in `contrib/rgb-panel.service` (`Restart=always`).
- No automated test suite exists; do not run effect sweeps against the hardware.

## Verification Plan

- Run `python3 -m py_compile rgb_panel.py` and `git diff --check`.
- Review the final diff and confirm the installed source matches the repository source.
- Restart the user service and confirm it completes the saved-configuration apply path.
- Confirm only intended source/docs files are included in the `main` update.

## Status

- State: implemented, syntax-checked, installed, and service-verified locally; publish operation in progress.
- Owner: Codex
- Last updated: 2026-11-02
