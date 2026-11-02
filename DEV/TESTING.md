# Testing And Verification

## Commands

- `python3 -m py_compile rgb_panel.py`
- `/usr/bin/python3 -m unittest discover -s tests -v`
- `git diff --check`

## Strategy

- Unit tests cover Corsair mode color counts, darker secondary shades, and generated software GPU frames.
- Startup application against real hardware requires running the updated service and observing a subsequent login/boot; do not infer this from compilation alone.
- Physical effect tests change the user's lighting and require an explicit request. When requested, record the tested device/effects and restore the saved configuration afterward.
