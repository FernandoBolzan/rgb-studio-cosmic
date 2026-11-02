# Architecture

## Runtime

- `rgb_panel.py` is the GTK 3 desktop app and Ayatana indicator process. `Panel` currently owns UI construction, device discovery, target grouping, scene/preferences persistence, and command orchestration.
- OpenRGB is invoked as a subprocess with `--noautoconnect`. Device listing and lighting operations run through a single-worker executor; completion returns to GTK through `GLib.idle_add`.
- The user systemd service launches the installed script at `~/.local/share/rgb-panel/rgb_panel.py`.

## Device and mode model

- Device IDs, mode names, and zone names come from `openrgb --list-detailed`.
- A device target exposes that device's modes. A group target exposes the case-insensitive intersection so a chosen effect is valid for every device in the group.
- OpenRGB remains the capability authority. Device support, mode controls, and hardware access vary by controller and installed OpenRGB version.
- Corsair DRAM has a focused capability table because five advertised modes require two colors. RGB Studio derives a darker secondary shade from the chosen color before applying those modes.
- GPUs that advertise Direct/Off can use software Blink, Breathe, and Rainbow. RGB Studio starts the local OpenRGB SDK server on demand, waits until the selected GPU appears in its device list, then sends Direct-color frames through the SDK client. The app must remain running for the animation; its server child is stopped when the app exits.
- ARGB targets are created for device-reported zones whose names contain `ARGB` or `addressable`; the LED count is user supplied and stored per zone.

## Local state

- Preferences: `~/.config/rgb-panel/settings.json`.
- Scenes: `~/.config/rgb-panel/presets/*.json`.
- JSON state is written via a temporary sibling file and atomically replaced. Older settings with a single `zone_led_count` remain a fallback during migration.

## Boundaries and follow-up

- Most hardware access crosses the OpenRGB CLI boundary; software GPU animations use the CLI's SDK-client mode and a local SDK server.
- Product categorization still uses device-name substrings, and the large GTK/controller module is not yet split. See `APP_AUDIT.md` for prioritized follow-up work.
