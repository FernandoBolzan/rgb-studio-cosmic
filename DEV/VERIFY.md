# Verify

## Latest Verification

- Date: 2026-11-02
- Scope: Corsair DRAM effects, software GPU effects, saved startup restoration, local installation, and active service.

## Commands

- `/usr/bin/python3 -m unittest discover -s tests -v` — 4 tests passed, covering all Corsair mode color counts, dark secondary shades, black preservation, and changing GPU frame colors.
- `/usr/bin/python3 -m py_compile rgb_panel.py tests/test_rgb_panel_modes.py` — passed.
- `git diff --check` — passed.
- Corsair hardware — both DIMMs accepted all 11 modes with no OpenRGB error; green Color Pulse was restored.
- GPU hardware — Palit GeForce RTX 3060 was verified in the SDK device list before updates; Blink sent green/off/green frames, Breathe sent three intensity frames, and Rainbow sent three hue frames. GPU restored to Direct green.
- `systemctl --user restart rgb-panel.service` — completed; service is active and enabled, with `NRestarts=0`.
- Installed source matches repository source; both SHA-256 values are `b7ffebbb4591c955bc9dd179ac780b53bbcd798a5a8f2f41e23fc4c2660fe133`.
- Startup restore — after the async device scan completed, `settings.json` was rewritten and still records `target=memory:0,1`, `mode=Color Pulse`, `color=#2EFF00`, brightness 100, speed 60, and `restore_on_startup=true`.
- `gh issue list` and `gh pr list` for `FernandoBolzan/rgb-studio-cosmic` — both returned empty lists.
- The selected lighting was restored after the hardware tests; software GPU animations require RGB Studio to remain running.

## Outcome

- Passed: regression tests; 22 Corsair mode applications; 9 sampled GPU frames; syntax and whitespace checks; installed-source equality; service restart; persisted startup state.
- Failed: none observed.
- Published: this memory/GPU change is pending; the earlier mode/app audit is on `origin/main` as `838ccf9`, and startup restoration is in its history as `adc6b3a`.
- Pending: observe restoration after a full system boot; a service restart exercised the same app startup path.
