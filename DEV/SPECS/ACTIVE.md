# Active Spec - RGB lighting reliability

## Goal

Fix Corsair memory effects that failed because OpenRGB requires multiple colors, add usable blink-style effects for the Palit GPU, and install and publish the verified change to `main`.

## Scope

- Supply the advertised color count for each Corsair DRAM mode, deriving a dark secondary color when two are required.
- Add software Blink, Breathe, and Rainbow effects to GPUs that expose Direct/Off only.
- Wait until the target GPU is visible to the OpenRGB SDK client before starting animation frames.
- Keep the current saved memory target and Color Pulse configuration after tests.
- Add focused regression tests and update user/developer documentation.
- Install the app, restart and verify the user service, then publish intended code/docs to `origin/main`, excluding the pre-existing service-unit edit.

## Acceptance

- All 11 modes advertised by each Corsair DIMM accept the selected color and supported controls without OpenRGB errors.
- GPU Blink, Breathe, and Rainbow frame updates reach the selected GPU via the SDK; starting before GPU discovery does not fail silently.
- Software effects are labeled as app-driven and require RGB Studio to remain active.
- The saved memory target/mode/color remain intact after physical tests and service restart reapplies that state.
- Regression tests, syntax, and whitespace checks pass; installed source matches repository source; service is active and enabled.
- The published `main` commit contains only intended app, test, and documentation files.

## Constraints

- Preserve the pre-existing uncommitted `contrib/rgb-panel.service` edit (`Restart=always`); do not stage or install it as part of this change.
- Physical mode tests visibly change lighting; restore both DIMMs and the GPU to the user's green configuration afterward.

## Verification Plan

- Run `/usr/bin/python3 -m unittest discover -s tests -v`, `/usr/bin/python3 -m py_compile rgb_panel.py tests/test_rgb_panel_modes.py`, and `git diff --check`.
- Test the Corsair effects on both DIMMs and send multiple generated frames for each GPU software mode through a verified SDK connection.
- Restore two DIMMs to Color Pulse green and GPU to Direct green; confirm saved settings still target memory.
- Install current source, restart the user service, and verify active/enabled status, restore logs/state, and installed-source hash.
- Confirm the staged diff excludes `contrib/rgb-panel.service`; commit and push the implementation to `origin/main`.

## Status

- State: implemented, hardware checked, installed, startup restoration verified, and published to `origin/main` as `c111bab`.
- Owner: Codex
- Last updated: 2026-11-02
