# Testing And Verification

## Commands

- `python3 -m py_compile rgb_panel.py`
- `git diff --check`

## Strategy

- No automated test suite is defined. For code changes, run syntax and whitespace checks, then review the code path.
- Startup application against real hardware requires running the updated service and observing a subsequent login/boot; do not infer this from compilation alone.
