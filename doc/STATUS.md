## **Home Assistant Samsung Frame Art Director - Development Status**

### **Purpose**

This add-on runs as a persistent service to dynamically manage the artwork on a Samsung The Frame TV. It automatically rotates images on a schedule, sourcing them from either a local Home Assistant Media folder or by generating new AI art based on various "aware" modes (e.g., weather, home state). The add-on is fully controllable via Home Assistant services, allowing for seamless integration with dashboards and automations.

### **How it works (current flow)**

1. The add-on starts as a long-running service, launching the main `art.py` script.
2. `art.py` runs an asyncio loop governed by `rotation_interval` (minutes).
3. On each loop:
   - If `--show-only` is enabled (via `ensure_art_mode_only`), it ensures the current artwork is shown.
   - Else if AI mode is enabled, it logs a placeholder (generation to be implemented next).
   - Else it selects a non-recent image from `/media/frame`, resizes/crops in memory to 3840x2160, uploads, selects it, and deletes the previous artwork.
4. `art.py` also listens on stdin for JSON commands (via `hassio.addon_stdin`) to perform manual actions immediately (e.g., load a specific image).

### **Config (key options)**

* tv: IP of The Frame TV  
* rotation_interval: Time in minutes between art rotations.  
* ensure_art_mode_only: If true, only show current artwork (no upload).  
* photo_filter: Optional photo filter.  
* matte / matte_color: Matte settings.  
* ai_art_enabled, ai_art_prompt, api_key: Inputs for AI mode.  
* debug: Enable verbose logging.

### **Roadmap**

#### **Phase 1: The Foundation (Essential Fixes)**

* \[x\] Proper resize-and-crop to avoid distortion using Utils and in-memory upload.  
* \[x\] Modernize run.sh with bashio for safe configuration reading.  
* \[x\] Strengthen error handling in art.py and ensure clean shutdowns.

#### **Phase 2: Architectural Shift to a Long-Running Service**

* \[x\] Change startup type in `config.yaml` to `services`.  
* \[x\] Add `rotation_interval` to `config.yaml` and UI translations.  
* \[x\] Refactor `art.py` into a persistent asyncio loop that honors `rotation_interval`.  
* \[x\] Enable `stdin` control and add a listener for `hassio.addon_stdin` JSON commands.  
* \[ \] (Optional) Implement a state file mechanism (`/data/art_mode.json`) if we add modes later.

#### **Phase 3: Implementing Aware Modes & AI Generation**

* \[ \] Implement the core AI image generation logic in `art.py` when AI mode is active.  
* \[ \] (Optional) Add simple mode handling if needed (could use a small state file).  
* \[ \] Extend README with examples of a dashboard button calling `hassio.addon_stdin` for manual image loads.  
* \[x\] Add a debug toggle to `config.yaml`/`run.sh` and `--debug` in Python for verbose logging.

#### **Phase 4: Advanced AI Control & Interaction**

* \[ \] Implement the generate\_ai\_art service to allow for on-demand generation with a custom prompt, bypassing the rotation timer.  
* \[ \] Add advanced prompt controls: main topic anchor, sub-prompts, negative prompts, style presets.  
* \[ \] Create a prompt variation engine to rotate sub-prompts over time while preserving a main theme.  
* \[ \] Implement lightweight caching/history (/data/ai\_history.json) to avoid repeats and manage retention.  
* \[ \] Add simple safeguards: minimum interval and cooldowns to prevent accidental rapid generation and control costs.

### **Files updated**

* homeassistant-samsung-frame-art/art.py  
* homeassistant-samsung-frame-art/run.sh  
* homeassistant-samsung-frame-art/utils/utils.py  
* homeassistant-samsung-frame-art/config.yaml  
* homeassistant-samsung-frame-art/translations/en.yaml  
* homeassistant-samsung-frame-art/Dockerfile

### **Functionality Test Plan**

#### **Objective**

To verify that the add-on functions correctly as a persistent service, rotates images on schedule, and is fully controllable via Home Assistant services.

#### **Prerequisites**

* Add-on Installed & Configured with a static TV IP.  
* At least 6 test images of various aspect ratios are present in /media/frame/.

#### **Test Cases: Baseline Functionality**

* \[ \] **Test Case 1: Successful Upload**: On first start, the add-on successfully connects, processes, and displays a local image correctly.  
* \[ \] **Test Case 2: Aspect Ratio Verification**: Non-16:9 images are properly cropped, not distorted.  
* \[ \] **Test Case 3: "Do Not Repeat" Functionality**: The uploaded.json correctly tracks the last 5 local images.  
* \[ \] **Test Case 4: TV Offline Error Handling**: The add-on logs a clear connection error and continues its loop without crashing if the TV is offline.

#### **Test Cases: Service & Rotation Functionality**

* \[ \] **Test Case 5: Rotation Test**: After `rotation_interval` minutes, the add-on selects a new image and updates the TV.  
* \[ \] **Test Case 6: Manual Override via stdin**:  
  1. From Developer Tools → Services, call `hassio.addon_stdin`.  
  2. Use your add-on slug (e.g., `local_ha-samsung-frame-art-director`) and provide a JSON payload like:  
     ```yaml
     service: hassio.addon_stdin
     data:
       addon: local_ha-samsung-frame-art-director
       input: '{"action":"load_image","filename":"/media/frame/IMAGE.JPG"}'
     ```  
  3. Verify the requested image is immediately processed and shown on the TV.  
* \[ \] **Test Case 7: Dashboard Button**:  
  1. Create a Lovelace button that triggers the `hassio.addon_stdin` call above.  
  2. Pressing the button should immediately display the configured image on the TV.