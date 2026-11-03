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
- `~/.local/share/rgb-panel/rgb_panel.py` matches the current repository source; both SHA-256 values are `b2508f3718706422e91ae8c00080d33229b3c87604ba3b7a5f06fdb2bb45e729`.
- RGB Studio has focused color-count metadata for Corsair DRAM and software Blink/Breathe/Rainbow for GPUs exposing Direct/Off. GPU animation uses a persistent OpenRGB TCP SDK connection, validates the selected controller by name and type, and updates the GPU's reported LED count.
- Device grouping prefers OpenRGB controller types; malformed list fields are skipped, and invalid setting values fall back individually.
- Physical verification sent all three generated software effects to the Palit GPU, then restored GPU Direct green and both Corsair modules to green Color Pulse.
- Current saved settings target `device:3`, Palit GeForce RTX 3060 LHR, with software `Breathe`, green `#2EFF00`, brightness 100, speed 100, and `restore_on_startup=true`.
- The service now logs that it is watching logind sleep/resume notifications; it is active with `NRestarts=0` after local restart.
- Mode and scene improvements were pushed to `origin/main` in commit `838ccf9`.
- Exclude the pre-existing service-unit edit from any publish operation.
- No project issues or pull requests were open/listed when checked on 2026-11-02.

## Next Context

- Current saved Palit GPU software `Breathe` configuration remained intact through local install and service restart; latest startup restored it at 12:19:17 and rewrote preferences after the first acknowledged frame.
- The previous persistent-transport build ran for 3m32s without timeout errors. The latest build stayed active for 1m13s after restoration, with `NRestarts=0` and no CLI client in the process list. A real sleep/resume cycle remains untested.
- Latest reliability review, including cancellation of stale SDK connections across sleep, is installed locally and remains uncommitted/unpublished. The unrelated `contrib/rgb-panel.service` change (`Restart=always`) remains preserved.
- Version `v0.1.1` contains the latest startup/resume, GPU SDK, parsing, and grouping fixes; `v0.1.0` remains the rollback point.
- Current local hardware: 2 Corsair Vengeance RGB Pro modules, ASUS PRIME B550M-A, and Palit GeForce RTX 3060; advertised modes vary by controller.
