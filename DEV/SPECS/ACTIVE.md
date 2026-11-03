# Active Spec - RGB reliability review

## Goal

Reliably apply and restore RGB settings across device discovery, login, and resume, while keeping GPU software effects stable and correctly targeting the selected OpenRGB controller.

## Scope

- Retry device discovery and saved target resolution when hardware appears late during startup; require two stable device scans before applying.
- Subscribe to logind's `PrepareForSleep` signal and close software animation SDK connections and active OpenRGB CLI clients before sleep.
- After resume, wait for hardware initialization, restart the SDK server, rediscover devices, and reapply saved settings.
- Use one persistent TCP SDK connection for GPU animation frames, select Direct once, validate the selected controller identity, and wait for frame acknowledgements.
- Treat a GPU software effect as restored only after its first frame succeeds; retry if that frame fails.
- Prefer OpenRGB controller types for device grouping and recover valid settings fields when other JSON fields are malformed.
- Add regression tests and update user and developer documentation.
- Install the verified app locally and confirm startup restoration through the user service.

## Acceptance

- Saved settings are retried up to 24 times at five-second intervals when devices or targets are initially unavailable; first application waits for two stable scans.
- Sleep notification pauses the GPU effect, closes its SDK connection, and terminates in-flight CLI clients.
- Resume resets stale restore state, waits eight seconds, refreshes devices, restarts the SDK server, and reapplies saved settings.
- GPU animation frames do not spawn per-frame CLI clients; the SDK controller identity matches the saved GPU.
- Malformed settings roots and invalid numeric fields do not crash startup or discard valid saved fields.
- Device classification prefers OpenRGB types and avoids grouping unrelated peripherals by vendor name.
- Failed startup GPU frames schedule restoration again; restoration completes only after a successful frame.
- 21 regression tests, Python compilation, and whitespace checks pass.
- Installed source matches the repository, service is active, and logs confirm saved GPU restoration and sustained SDK frames.

## Constraints

- Preserve the pre-existing uncommitted `contrib/rgb-panel.service` edit (`Restart=always`).
- Keep the existing saved RGB settings and verify the effect configured by the user after installing.
- Do not claim a full hibernation cycle was physically verified unless the machine actually performs one during this task.

## Verification Plan

- Run `/usr/bin/python3 -m unittest discover -s tests -v`, `/usr/bin/python3 -m py_compile rgb_panel.py tests/test_rgb_panel_modes.py`, and `git diff --check`.
- Verify logind's D-Bus signal contract and exercise sleep/resume callbacks with regression tests.
- Install the current source, restart `rgb-panel.service`, and inspect active state, logs, saved configuration, installed-source hash, and child processes after a multi-minute run.
- Record whether a real sleep/resume cycle was performed; callback simulation does not substitute for hardware wake verification.

## Status

- State: persistent SDK transport, settings hardening, type-based grouping, pending-connection invalidation, 21 regression tests, local installation, and startup restoration verified. GPU Breathe ran beyond the previous timeout window without CLI frame processes; an actual sleep/resume cycle remains untested.
- Owner: Codex
- Last updated: 2026-11-03
