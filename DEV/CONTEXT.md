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
- The current mode/scene improvements are installed at `~/.local/share/rgb-panel/rgb_panel.py`; its SHA-256 matches the repository source.
- The user service is active and enabled after restart, with no systemd restarts reported.
- Mode and scene improvements were pushed to `origin/main` in commit `838ccf9`.
- Exclude the pre-existing service-unit edit from any publish operation.
- No project issues or pull requests were open/listed when checked on 2026-11-02.

## Next Context

- Future settings preserve target, effect, and per-zone LED counts; the existing settings still restore `target=all`, `mode=Direct`.
- Current local hardware: 2 Corsair Vengeance RGB Pro modules, ASUS PRIME B550M-A, and Palit GeForce RTX 3060; advertised modes vary by controller.
