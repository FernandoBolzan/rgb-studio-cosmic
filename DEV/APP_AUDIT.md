# RGB Studio app audit

## Scope and evidence

- Reviewed device discovery, target grouping, effect selection/application, startup restoration, ARGB zone sizing, scene persistence, GTK layout, and the OpenRGB CLI boundary in `rgb_panel.py`.
- Checked the project GitHub issues and pull requests on 2026-11-02. Both lists were empty: [issues](https://github.com/FernandoBolzan/rgb-studio-cosmic/issues) and [pull requests](https://github.com/FernandoBolzan/rgb-studio-cosmic/pulls).
- OpenRGB documents modes as device-specific and exposes speed/brightness according to mode support in its [CLI source](https://github.com/CalcProgrammer1/OpenRGB/blob/master/cli.cpp). Its [release page](https://openrgb.org/releases.html) is the reference for the current compatible release.
- The local installation has two Corsair Vengeance RGB Pro memory modules, an ASUS PRIME B550M-A motherboard, and a Palit GeForce RTX 3060. The advertised mode lists differ across these controllers.

## Findings addressed in this change

1. **Mode matching was case-sensitive.** Modes advertised with different capitalization could disappear from grouped targets or be rejected even when supported. Matching now uses Unicode case folding and sends the spelling advertised by each device.
2. **Unsupported effects could silently become another effect.** Application previously fell back to Direct, Static, or the first mode. It now rejects an unsupported explicit effect before issuing the combined OpenRGB command. Saved startup effects that are no longer common to their target report an error instead of changing unexpectedly. CLI `Error:` output is treated as a failure even if the process exits with status zero.
3. **Grouped targets hid why effects were missing.** The selector now explains that grouped targets show only common effects and directs users to an individual device for its full list.
4. **Only the first motherboard ARGB zone was exposed.** All device-reported zones whose names contain “ARGB” or “addressable” are now selectable, and each device also receives an individual target.
5. **ARGB sizes were shared globally and omitted from scenes.** LED counts are stored per zone, with the old global setting retained as a migration fallback. Scenes now preserve the target identity and zone count, reject unavailable targets/effects, and clamp numeric values to supported ranges.
6. **Interrupted JSON writes could truncate settings or scenes.** Settings and scenes now replace their files atomically.
7. **Corsair DRAM modes were missing required colors.** Color Shift, Color Pulse, Color Wave, Visor, and Rain require two colors; the CLI warning can exit successfully. RGB Studio now supplies a darker second shade, and a retry handles OpenRGB's color-count warning.
8. **The Palit GPU only exposes Direct and Off.** RGB Studio now offers software Blink, Breathe, and Rainbow. It waits for the selected GPU to appear in the SDK device list before starting frames, preventing a startup race while OpenRGB scans hardware.

## Hardware verification

- Both Corsair memory modules were exercised through all 11 advertised modes; each command completed without an OpenRGB error.
- The Palit GeForce RTX 3060 accepted Blink, Breathe, and Rainbow frame updates through the SDK client. The GPU was restored to Direct green, and both memory modules were restored to green Color Pulse.
- Regression tests cover the color counts and generated animation frames; see `DEV/VERIFY.md` for the current run.

## Remaining improvement backlog

### P1 — mode capability discovery

OpenRGB's basic device listing does not give RGB Studio a complete capability matrix for every mode's color, speed, and brightness controls. The UI has focused metadata for Corsair DRAM, but other controllers still use generic dynamic controls. A broader capability query should drive these controls per effect and show clear unsupported-control feedback.

### P1 — automated regression coverage and CI

The initial regression suite covers Corsair color counts and generated GPU frames. Extend it with isolated tests for device-list parsing, case-insensitive mode intersection, device-native mode resolution, target restoration after device reordering, scene validation, and per-zone migration; add a CI syntax/build gate.

### P2 — stable device identity and classification

OpenRGB numeric device IDs may change, while device categories are inferred from product-name substrings such as “ASUS”, “Corsair”, and “GeForce”. Prefer stable vendor/product identifiers from the SDK where available, make category metadata explicit, and keep a safe generic target when metadata is missing.

### P2 — split the GTK/controller module

`rgb_panel.py` owns UI, discovery, target construction, CLI calls, and persistence in one large module. Separate the OpenRGB adapter and configuration/preset model from GTK widgets so each boundary can be maintained and tested independently.

### P2 — reconnect and failure recovery

Startup restoration has a bounded retry window. Add a user-visible reconnect action and retain retry state when OpenRGB starts late or the daemon restarts after the initial attempts.

### P3 — packaging and contributor workflow

Add a dependency manifest or distro package metadata, document supported Python/OpenRGB versions, and provide a repeatable development install. Keep build, lint, and CI commands documented in `DEV/TESTING.md` once configured.

## Limits

Device behavior remains bounded by the modes and capabilities OpenRGB reports. These tests used the current local OpenRGB 1.1 build and hardware; they do not establish compatibility with every controller or OpenRGB release.
