# Active Spec - rgb-panel

## Goal

Restore the last applied RGB configuration after RGB Studio detects hardware at startup.

## In Scope

- Persist target, mode, brightness, speed, color, and ARGB LED count after a successful apply.
- Restore saved values once per app start, with bounded retries if OpenRGB is temporarily unavailable.
- Document behavior for older settings files that lack target and effect details.

## Out Of Scope

- Creating a tagged GitHub release.

## Acceptance

- Saved settings are applied after device discovery when the app starts.
- New applies persist enough state to restore the chosen target and effect.
- Older settings remain readable and restore their saved color with documented defaults.

## Structural Prevention

- Change class: local bug fix.
- Structural adjustment if this is a local remediation: none; keep startup restoration in `Panel` and reuse existing OpenRGB apply paths.

## Constraints

- Preserve the existing uncommitted edit in `contrib/rgb-panel.service`.
- Exclude that service-unit edit from the release commit.

## Verification Plan

- Run `python3 -m py_compile rgb_panel.py` and `git diff --check`.
- Install and restart the user service, then confirm the saved settings are reapplied.
- Push the reviewed correction to `origin/main`, excluding the pre-existing service edit.

## Status

- State: installed, verified, and pushed to `origin/main` as `246e7c3`
- Owner: Codex
- Last updated: 2026-11-02
