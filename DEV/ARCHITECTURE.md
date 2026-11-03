# Architecture

## Runtime

- `rgb_panel.py` is the GTK 3 desktop app and Ayatana indicator process. `Panel` currently owns UI construction, device discovery, target grouping, scene/preferences persistence, and command orchestration.
- OpenRGB CLI commands run through a single-worker executor; completion returns to GTK through `GLib.idle_add`. Animated GPU effects keep one TCP SDK connection open and send LED frames over it instead of launching a CLI process for every frame.
- The user systemd service launches the installed script at `~/.local/share/rgb-panel/rgb_panel.py`.
- The app listens for logind's system-bus `PrepareForSleep` signal. It stops software GPU frames and pending CLI clients before sleep, then restarts the SDK server, rediscovers devices, and reapplies saved settings after resume.
- Startup restoration waits for two stable device scans and retries discovery/target resolution up to 24 times at five-second intervals, covering hardware that becomes available after the desktop service starts.

## Device and mode model

- Device IDs, mode names, and zone names come from `openrgb --list-detailed`.
- A device target exposes that device's modes. A group target exposes the case-insensitive intersection so a chosen effect is valid for every device in the group.
- OpenRGB remains the capability authority. Device support, mode controls, and hardware access vary by controller and installed OpenRGB version.
- Corsair DRAM has a focused capability table because five advertised modes require two colors. RGB Studio derives a darker secondary shade from the chosen color before applying those modes.
- GPUs that advertise Direct/Off can use software Blink, Breathe, and Rainbow. RGB Studio starts the local OpenRGB SDK server on demand, resolves the selected controller by its name and type, selects Direct once, then sends acknowledged LED-color frames through one persistent SDK connection. The app must remain running for the animation; its client connection and server child are stopped on sleep, effect changes, and app exit.
- ARGB targets are created for device-reported zones whose names contain `ARGB` or `addressable`; the LED count is user supplied and stored per zone.

## Local state

- Preferences: `~/.config/rgb-panel/settings.json`; each configured device or ARGB zone has its own restorable profile, while the latest UI target remains available for selection.
- Scenes: `~/.config/rgb-panel/presets/*.json`.
- JSON state is written via a temporary sibling file and atomically replaced. Older settings with a single `zone_led_count` remain a fallback during migration.

## Boundaries and follow-up

- Most non-animated hardware access crosses the OpenRGB CLI boundary; GPU animations use the OpenRGB TCP SDK and a local SDK server.
- Controller type now drives motherboard, DRAM, and GPU grouping when OpenRGB provides it. Name-based fallback is limited to controllers with missing or unknown type metadata. The large GTK/controller module is not yet split; see `APP_AUDIT.md` for follow-up work.
