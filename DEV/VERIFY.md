# Verify

## Latest Verification

- Date: 2026-11-02
- Scope: mode handling, target and scene persistence, local installation, and active service.

## Commands

- `python3 -m py_compile rgb_panel.py` — passed.
- `git diff --check` — passed.
- `systemctl --user restart rgb-panel.service` — completed; service is active and enabled, with `NRestarts=0`.
- Installed source matches repository source; both SHA-256 values are `1b3e73a1c54b9af566869f6cdd558dd347d2513839ec82f85529c6942068ccb6`.
- Startup restore — `settings.json` was rewritten after service restart and continues to record `target=all`, `mode=Direct`, brightness 100, speed 50, and `restore_on_startup=true`.
- `gh issue list` and `gh pr list` for `FernandoBolzan/rgb-studio-cosmic` — both returned empty lists.
- No effect sweep or automated tests were run; the repository has no automated test suite, and changing physical effects was avoided.

## Outcome

- Passed: syntax and whitespace checks; installed-source equality; service restart; persisted startup state.
- Failed: none observed.
- Published: pending commit/push for the current mode and app audit changes. The previous startup-restoration fix is on `origin/main` as `adc6b3a`.
- Pending: observe restoration after a full system boot; a service restart exercised the same app startup path.
