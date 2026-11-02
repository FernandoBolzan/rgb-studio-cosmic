# Current Context

## State

- Project: `rgb-panel`
- Active handoff: `HANDOFF.md`
- Active spec: `SPECS/ACTIVE.md`
- Update this file when commands, architecture, environment, risks, or active decisions change.

## Commands

- Install: see `README.md`; user service runs `~/.local/share/rgb-panel/rgb_panel.py`.
- Development: `python3 -m py_compile rgb_panel.py`.
- Tests: no automated test suite is defined.
- Build: Python script; no separate build step.

## Constraints And Risks

- `contrib/rgb-panel.service` already has an uncommitted user change (`Restart=always`); preserve it.
- Legacy settings do not identify the previous target or effect; first restore defaults to all devices and fixed color.
- The active installed source now matches this repository version.
- Exclude the pre-existing service-unit edit from the release commit.
- Fix is installed and pushed to `origin/main` as commit `246e7c3`.

## Next Context

- Future settings now preserve target and effect; the legacy settings on this machine were migrated to `target=all`.
