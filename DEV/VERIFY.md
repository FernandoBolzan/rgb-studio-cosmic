# Verify

## Latest Verification

- Date: 2026-11-02
- Scope: startup restoration change, local installation, and active service.

## Commands

- `python3 -m py_compile rgb_panel.py` — passed.
- `git diff --check` — passed.
- `systemctl --user restart rgb-panel.service` — completed; service is active.
- Startup restore — OpenRGB process exited and `settings.json` now records `target=all`, `mode=Direct`, brightness 100, speed 50, and `restore_on_startup=true`.

## Outcome

- Passed: syntax and whitespace checks; the service completed the apply path and persisted the restored state.
- Failed: none.
- Published: commit `246e7c3` is on `origin/main`.
- Pending: observe restoration on a later full system boot; service restart verified the same startup path.
