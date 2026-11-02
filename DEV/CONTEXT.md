# Current Context

## State

- Project: `rgb-panel`
- Active handoff: `HANDOFF.md`
- Active spec: `SPECS/ACTIVE.md`
- Update this file when commands, architecture, environment, risks, or active decisions change.

## Commands

- Install: see `README.md`; user service runs `~/.local/share/rgb-panel/rgb_panel.py`.
- Development: `/usr/bin/python3 -m py_compile rgb_panel.py tests/test_rgb_panel_modes.py`.
- Tests: `/usr/bin/python3 -m unittest discover -s tests -v`.
- Build: Python script; no separate build step.

## Constraints And Risks

- `contrib/rgb-panel.service` already has an uncommitted user change (`Restart=always`); preserve it.
- Legacy settings do not identify the previous target or effect; first restore defaults to all devices and fixed color.
- The current memory/GPU source is installed at `~/.local/share/rgb-panel/rgb_panel.py`; its SHA-256 matches the repository version.
- RGB Studio has focused color-count metadata for Corsair DRAM and software Blink/Breathe/Rainbow for GPUs exposing Direct/Off. The SDK readiness check waits for the selected GPU by ID, name, and type.
- Physical verification sent all three generated software effects to the Palit GPU, then restored GPU Direct green and both Corsair modules to green Color Pulse.
- The user service restarted successfully, is active/enabled, and reports `NRestarts=0`; its startup restore rewrote settings while preserving the saved memory target and effect.
- Mode and scene improvements were pushed to `origin/main` in commit `838ccf9`.
- Exclude the pre-existing service-unit edit from any publish operation.
- No project issues or pull requests were open/listed when checked on 2026-11-02.

## Next Context

- Current saved settings target both Corsair modules with green Color Pulse and `restore_on_startup=true`; preserve these through service restart.
- The memory/GPU correction is installed locally and published as `c111bab`; prior mode/scene work remains in its history.
- The first versioned release `v0.1.0` is published on GitHub; its annotated tag targets `161f6e0` on `main`.
- Current local hardware: 2 Corsair Vengeance RGB Pro modules, ASUS PRIME B550M-A, and Palit GeForce RTX 3060; advertised modes vary by controller.
