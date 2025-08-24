## **Add-on Development & Testing Workflow (Local HA + Samba)**

### **Prerequisites**

- A running Home Assistant instance (OS or Supervised).  
- Install the official **Samba share** add-on in Home Assistant (Add-on Store → Samba share → Install).  
- Configure Samba with a username/password.

### **1\. Copy the add-on into your HA instance**

1. From Windows File Explorer, open the share: `\\homeassistant\\addons\\local` (replace `homeassistant` with your HA hostname or IP).  
2. Copy the folder `ha-samsung-frame-art-director` from this repository into `\\addons\\local\\` so it becomes:  
   `\\homeassistant\\addons\\local\\ha-samsung-frame-art-director`  
3. Ensure `config.yaml` inside that folder has the `image` line commented (local build). This repo already comments it out.

### **2\. Prepare media**

1. Open the `media` share: `\\homeassistant\\media`.  
2. Create a folder `frame` if it does not exist.  
3. Copy at least 6 images (lowercase `.jpg`/`.png` extensions recommended) into `\\homeassistant\\media\\frame`.

### **3\. Install and configure the add-on**

1. In Home Assistant → Settings → Add-ons → Add-on Store: menu (⋮) → **Check for updates**.  
2. Open the "Samsung Frame Art Director" add-on (under Local add-ons) and click **Install** (or Rebuild if needed).  
3. Configuration tab: set options:  
   - `tv`: IP of your Frame (static)  
   - `rotation_interval`: 1–2 (for testing)  
   - `ensure_art_mode_only`: false (for baseline tests)  
   - `power_state_check`: true  
   - `turn_on_art_mode`: true  
   - `debug`: true (turn off later)  
   - Optional: `photo_filter`, `matte`, `matte_color`
4. Save. If you edited `config.yaml` (e.g., enabling `host_network: true`), click **Rebuild**.

### **4\. Run baseline tests**

1. Start the add-on → Logs: confirm connection and an image upload/selection occurs.  
2. Verify the TV shows the image in Art Mode.  
3. Wait `rotation_interval` minutes and confirm a new image is selected and pushed.

### **4.5\. Ensure Art Mode only (no upload)**

1. Set `ensure_art_mode_only: true` in the add-on configuration → Save → Restart the add-on.  
2. Logs should show the current `content_id`, then “Ensured current artwork is showing”.  
3. Reset `ensure_art_mode_only: false` to resume uploads.

### **5\. Manual override (show a specific image)**

Home Assistant → Developer Tools → Services → call `hassio.addon_stdin` with:

```yaml
service: hassio.addon_stdin
data:
  addon: local_ha-samsung-frame-art-director
  input: '{"action":"load_image","filename":"/media/frame/IMAGE.JPG"}'
```

Expected: the requested image is processed and shown immediately; logs reflect the action.

### **6\. Art Mode toggle (on/off)**

- Turn ON:
```yaml
service: hassio.addon_stdin
data:
  addon: local_ha-samsung-frame-art-director
  input: '{"action":"set_art_mode","on": true}'
```

- Turn OFF:
```yaml
service: hassio.addon_stdin
data:
  addon: local_ha-samsung-frame-art-director
  input: '{"action":"set_art_mode","on": false}'
```

Expected: Logs show the action; TV enters/exits Art Mode if supported by firmware.

### **9\. Troubleshooting**

- Upload retry/AssertionError: Ensure `host_network: true` is present in `config.yaml`, then **Rebuild**. Confirm the TV and HA host are on the same subnet/VLAN and your AP/router doesn’t isolate clients.  
- Slow status calls (get_artmode/get_current): Expected on some firmware; the add-on proceeds even if these time out.  
- No images found: Place `.jpg`/`.png` (lowercase extensions recommended) in `media/frame`.  
- Interval too low: The add-on enforces a minimum of 60 seconds even if `rotation_interval` is set to 0 or a fraction.

### **7\. Optional: Dashboard buttons**

Create Lovelace buttons that call `hassio.addon_stdin` with the above payloads to quickly trigger `load_image` or toggle Art Mode.

### **8\. Final deployment**

Once tests pass, continue using the add-on from your main HA instance. To update: copy changed files over the Samba share and click **Rebuild** on the add-on.