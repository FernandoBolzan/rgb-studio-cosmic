# Testing And Verification

## Commands

- `python3 -m py_compile rgb_panel.py`
- `/usr/bin/python3 -m unittest discover -s tests -v`
- `git diff --check`

## Strategy

- Unit tests cover Corsair mode color counts, generated software GPU frames, OpenRGB device parsing and type-based grouping, partial settings corruption, SDK packet framing/controller identity, per-target preference migration and restoration, startup retry, and suspend/resume callbacks.
- Startup and resume application against real hardware require running the updated service and observing the restored device state; do not infer this from compilation alone.
- Physical effect tests change the user's lighting and require an explicit request. When requested, record the tested device/effects and restore the saved configuration afterward. Long-running animation checks should confirm that the service does not spawn one OpenRGB client per frame.
