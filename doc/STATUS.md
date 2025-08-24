## **Home Assistant Frame Director \- Development Plan**

### **Purpose**

This add-on runs as a persistent service to dynamically manage the artwork on a Samsung The Frame TV. It operates in distinct, user-selectable modes: shuffling local media, shuffling a curated AI art library, or actively generating new "aware" art based on home state (e.g., weather, events). The add-on is fully controllable via Home Assistant services, allowing for seamless integration with dashboards, automations, and on-demand creative direction.

### **How it works (flow)**

1. **Persistent Service:** The add-on starts as a long-running service, launching the main art.py script which enters an infinite rotation loop.  
2. **Operating Modes:** On each rotation, the script checks the current **Operating Mode** stored in a state file. This mode dictates the source of the art.  
   * **Shuffle Local Files:** The default mode. Picks a random image from the /media/frame folder.  
   * **Shuffle AI Library:** Picks a random, pre-generated image from the AI art library, optionally filtered by tags (e.g., show only mood_calm images).  
   * **Generate Aware Art:** Actively generates a new AI image on each rotation.  
3. **Prompt Engine:** When generating art, a "Prompt Engine" combines a user-provided **Base Prompt** (the creative direction, e.g., "forest scenes") with automatic **Context Modifiers** (e.g., rainy, party) to create a unique, final prompt. If no Base Prompt is given, it runs in full-auto mode.  
4. **Image Processing:** The selected or generated image is resized and cropped in memory to the TV's 3840x2160 resolution.  
5. **TV Interaction:** The script connects to the TV, uploads the new image, sets it as the active artwork, and deletes the previously displayed image from the TV's storage.  
6. **Scalable Library:** All generated AI art and its metadata (prompt, tags) are stored in a scalable **SQLite database** (/data/art_library.db), allowing for a fast and reliable library of thousands of images.  
7. **Dashboard Control:** Home Assistant services (set_rotation_mode, generate_single_image, generate_batch_images) can be called at any time to change modes, provide a new Base Prompt, or trigger on-demand generation, giving the user full control from dashboards or automations.

### **Current status (implemented)**

- Basic setup working: connect to Frame, upload, and show artwork in Art Mode.
- Persistent asyncio loop with `rotation_interval`; rotates local images from `/media/frame`.
- Image processing: center-crop/resize to 3840×2160; matte and photo filter supported.
- Tracks last 5 uploaded filenames in `/data/uploaded.json` to reduce repeats.
- Current control: manual commands via `hassio.addon_stdin` (stdin listener). HA services and SQLite library are not yet implemented.

### **Config (key options)**

* tv: IP of The Frame TV  
* rotation\_interval: Time in minutes between art rotations.  
* photo\_filter: Optional photo filter.  
* matte / matte\_color: Matte settings.  
* api\_key: API key for the image generation service.

### **Roadmap**

#### **Phase 1: The Foundation (Essential Fixes)**

* \[x\] Proper resize-and-crop to avoid distortion using Utils and in-memory upload.  
* \[x\] Modernize run.sh with bashio for safe configuration reading.  
* \[x\] Strengthen error handling in art.py and ensure clean shutdowns.

#### **Phase 2: Architectural Shift to a Service & Database**

* [x] Change startup type in config.yaml to services.  
* [x] Add rotation_interval to config.yaml and UI translations.  
* [x] Refactor art.py into a persistent main loop that honors the rotation_interval.  
* [ ] **Implement the SQLite database** (/data/art_library.db) for storing AI art metadata and tags.  
* [ ] Create services.yaml to define the initial set_rotation_mode service.  
* [ ] Implement the state file mechanism (/data/art_mode.json) for the main loop to read the current operating mode.

**Testing Gate (required before Phase 3):** Run in-depth tests of the basic setup (connection, upload, rotation, error handling) and stabilize before starting any AI generation work.

#### **Phase 3: Implementing Operating Modes & The Prompt Engine**

* [ ] Implement the three core operating modes (Shuffle Local Files, Shuffle AI Library, Generate Aware Art) within the art.py main loop.  
* [ ] Implement the core AI image generation logic.  
* [ ] **Build the "Prompt Engine"** to combine a user-provided Base Prompt with automatic Context Modifiers.  
* [ ] Implement the automatic tagging system, saving generated images and their tags to the SQLite database.  
* [x] Add a debug toggle to config.yaml and run.sh for verbose logging.

#### **Phase 4: On-Demand Generation & Dashboard Control**

* \[ \] Implement the generate\_single\_image service for on-demand generation with a custom prompt.  
* \[ \] Implement the generate\_batch\_images service for building themed collections in the library.  
* \[ \] Extend README with detailed examples of dashboard controls (input\_text for Base Prompt, input\_select for modes) and corresponding automations.  
* \[ \] Add simple safeguards: minimum interval and cooldowns to prevent accidental rapid generation and control costs.

### **Files to be Touched/Created**

* homeassistant-samsung-frame-art/art.py  
* homeassistant-samsung-frame-art/run.sh  
* homeassistant-samsung-frame-art/config.yaml  
* homeassistant-samsung-frame-art/services.yaml **(New File)**  
* /data/art\_library.db **(New Database File, created at runtime)**

### **Functionality Test Plan**

#### **Objective**

To verify that the add-on functions correctly as a persistent service, rotates images according to the selected mode, and is fully controllable via Home Assistant services.

#### **Test Cases: Baseline Functionality**

* \[ \] **Test Case 1: Successful Upload (Local Mode)**: In Shuffle Local Files mode, the add-on successfully connects, processes, and displays a local image correctly.  
* \[ \] **Test Case 2: Aspect Ratio Verification**: Non-16:9 images are properly cropped, not distorted.  
* \[ \] **Test Case 3: TV Offline Error Handling**: The add-on logs a clear connection error and continues its loop without crashing if the TV is offline.

#### **Test Cases: Service, Rotation & Mode Functionality**

* \[ \] **Test Case 4: Rotation Test**: The add-on automatically triggers a new rotation after the rotation\_interval has passed.  
* \[ \] **Test Case 5: Service Call (set\_rotation\_mode)**: Calling the service successfully changes the operating mode in /data/art\_mode.json, and the new mode is used on the next rotation.  
* \[ \] **Test Case 6: AI Generation Test (Generate Aware Art mode)**: The add-on successfully generates an image, saves it to the library, stores its metadata in the database, and displays it on the TV.  
* \[ \] **Test Case 7: AI Library Test (Shuffle AI Library mode)**: The add-on successfully queries the database, selects a previously generated image, and displays it.  
* \[ \] **Test Case 8: On-Demand Generation (generate\_single\_image service)**: Calling the service immediately generates and displays a new image, independent of the rotation timer.