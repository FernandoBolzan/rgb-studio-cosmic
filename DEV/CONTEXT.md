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
- Very old settings without a target still fall back to all devices and a fixed-color mode; the single-target schema migrates that one profile, while v0.1.2 stores every configured component independently.
- `~/.local/share/rgb-panel/rgb_panel.py` matches the repository source after installation; both SHA-256 values are `ae53ec702c656ff0c460057668c78db195dee681707813722ce5b4f2f13e59b6`.
- RGB Studio has focused color-count metadata for Corsair DRAM and software Blink/Breathe/Rainbow for GPUs exposing Direct/Off. GPU animation uses a persistent OpenRGB TCP SDK connection, validates the selected controller by name and type, and updates the GPU's reported LED count.
- Device grouping prefers OpenRGB controller types; malformed list fields are skipped, and invalid setting values fall back individually.
- Physical verification sent all three generated software effects to the Palit GPU, then restored GPU Direct green and both Corsair modules to green Color Pulse.
- Current saved settings retain the active target as Palit `device:3` with software `Breathe`, green `#2EFF00`, brightness 100, speed 100, and `restore_on_startup=true`; `target_profiles` also stores ASUS `device:2` Direct and both Corsair DIMMs Color Pulse in green.
- OpenRGB reports the local Corsair DIMMs as devices 0/1, ASUS PRIME B550M-A as 2, and Palit GeForce RTX 3060 LHR as 3. The previous settings schema saved only the last target; the new schema stores profiles per device.
- The service now logs that it is watching logind sleep/resume notifications; it is active with `NRestarts=0` after local restart.
- Mode and scene improvements were pushed to `origin/main` in commit `838ccf9`.
- Exclude the pre-existing service-unit edit from any publish operation.
- No project issues or pull requests were open/listed when checked on 2026-11-02.

## Next Context

- A real hibernation before the fix restored only GPU `device:3`; the old JSON had no motherboard or memory profiles. After installing the fix, service restart restored motherboard Direct, both DIMMs Color Pulse, and GPU Breathe at 13:48, with `NRestarts=0`.
- The per-device restoration fix is installed locally and prepared as release `v0.1.2`; a real hibernation cycle after the fix remains pending.
- The pre-existing `contrib/rgb-panel.service` change (`Restart=always`) remains preserved and excluded from the app release.
- Version `v0.1.1` contains startup/resume, GPU SDK, parsing, and grouping fixes; `v0.1.2` adds per-device restoration. `v0.1.1` is the rollback point.
- Current local hardware: 2 Corsair Vengeance RGB Pro modules, ASUS PRIME B550M-A, and Palit GeForce RTX 3060; advertised modes vary by controller.
