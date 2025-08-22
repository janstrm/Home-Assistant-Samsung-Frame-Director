# Samsung Frame Art Mode (Home Assistant Add-on)

[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fjanstrm%2Fhomeassistant-samsungframe-artmode)

A focused, single‑TV Home Assistant add-on to dynamically manage artwork on a Samsung The Frame TV. The add-on runs as a long‑lived service and rotates images on a schedule from your HA Media folder, with a simple path to add AI‑generated images next.

## What this is
- Persistent service (runs in the background) that updates The Frame’s art.
- Sources images from `Media/frame/` (local). AI generation is planned.
- Manual override via `hassio.addon_stdin` to display a specific image on demand.
- Single‑TV scope by design; clear, minimal controls.

## Key features (current)
- Aspect‑correct resize and center‑crop to 3840×2160 (no distortion).
- Interval‑based rotation using a configurable `rotation_interval` (minutes).
- Optional “show only” mode to ensure Art Mode is active without changing the image.
- Matte and photo filter support.
- Robust logging with optional `debug` toggle.

## Install
1. In Home Assistant → Settings → Add-ons → Add-on Store → “Repositories”, add:
   `https://github.com/janstrm/homeassistant-samsungframe-artmode`
2. Install the “Samsung Frame Art Mode” add-on, open it, and configure options.

## Configuration
- `tv` (string): IP address of your Samsung The Frame (use a static IP).
- `rotation_interval` (int): Minutes between automatic image changes.
- `ensure_art_mode_only` (bool): If true, only ensures the current artwork is shown (no upload).
- `photo_filter` (enum|None): Optional TV photo filter to apply.
- `matte` / `matte_color` (enum): Matte settings.
- `ai_art_enabled`, `ai_art_prompt`, `api_key`: Reserved for upcoming AI mode.
- `debug` (bool): Enable verbose logging.

## Usage
### Rotate automatically
Set `rotation_interval` to your desired cadence. The add-on will select a non‑recent image from `Media/frame/`, resize/crop it, upload, and select it on the TV.

### Ensure Art Mode (no change)
Set `ensure_art_mode_only: true` to periodically re‑assert Art Mode using the current artwork (useful if your TV sometimes switches inputs).

### Manual override (display a specific image now)
Call `hassio.addon_stdin` from Developer Tools → Services with a JSON payload:

```yaml
service: hassio.addon_stdin
data:
  addon: local_hass-frame-changer
  input: '{"action":"load_image","filename":"/media/frame/IMAGE.JPG"}'
```

Tip: Add a Lovelace button to trigger the same payload for quick, on‑demand control.

## Roadmap and testing
- Roadmap, baseline test plan, and detailed status live in `doc/STATUS.md`.
- AI generation flow is planned (kept minimal, single‑TV focus).

## Notes
- Place `.jpg`/`.png` images (lowercase extensions recommended) in `Media/frame/`.
- This add-on targets a single Samsung The Frame TV.
