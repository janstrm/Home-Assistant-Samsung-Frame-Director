import sys
import random
import json
import os
import asyncio
import logging
import argparse
from typing import List
from utils.utils import Utils

sys.path.append('../')
from samsungtvws.async_art import SamsungTVAsyncArt
from samsungtvws import exceptions

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
folder_path = '/media/frame'
uploaded_json_path = '/data/uploaded.json'
token_file_path = "/data/token_frame.json"

# --- Argument Parsing ---
def parseargs():
    parser = argparse.ArgumentParser(description='Samsung Frame TV Art Director.')
    parser.add_argument('--ip', required=True, type=str, help='IP address of TV')
    parser.add_argument('--rotation-interval', type=int, default=15, help='Rotation interval in minutes')
    parser.add_argument('--matte', type=str, default="none", help='Matte to apply')
    parser.add_argument('--matte-color', type=str, default="black", help='Matte color')
    parser.add_argument('--filter', type=str, default="none", help='Photo filter')
    parser.add_argument('--debug', action="store_true", help='Enable debug logging')
    parser.add_argument('--power-state-check', action="store_true", help='Only run if the TV is in Art Mode or Standby')
    parser.add_argument('--turn-on-art-mode', action="store_true", help='Turn on Art Mode if the TV is in Standby')
    parser.add_argument('--show-only', action="store_true", help='Only ensure Art Mode is showing the current image')
    return parser.parse_args()

# --- Helper Functions ---
def load_uploaded_history():
    if not os.path.exists(uploaded_json_path): return []
    try:
        with open(uploaded_json_path, 'r') as f: return json.load(f)
    except (json.JSONDecodeError, IOError):
        logging.warning("Could not read uploaded.json, starting fresh.")
        return []

def save_uploaded_history(history: List[str]):
    try:
        with open(uploaded_json_path, 'w') as f: json.dump(history, f)
    except IOError:
        logging.error("Could not write to uploaded.json.")

# --- Main Logic ---
async def main():
    args = parseargs()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logging.info(f"Add-on started. Rotating every {args.rotation_interval} minutes.")
    interval_seconds = max(60, args.rotation_interval * 60)

    while True:
        logging.info("--- Starting new rotation cycle ---")
        tv = None
        try:
            # 1. Create the TV object.
            tv = SamsungTVAsyncArt(
                host=args.ip,
                port=8002,
                token_file=token_file_path,
                name="HomeAssistant-Frame-Director"
            )

            # 2. Best-effort: verify Art Mode support
            try:
                supported = await asyncio.wait_for(tv.supported(), timeout=5)
            except Exception:
                supported = True
            if not supported:
                logging.info("Art Mode not supported on this TV; skipping cycle.")
                await asyncio.sleep(interval_seconds)
                continue

            # 3. Check TV State (Power & Art Mode)
            power_on = await asyncio.wait_for(tv.on(), timeout=10)
            try:
                art_mode_status = await asyncio.wait_for(tv.get_artmode(), timeout=5)
            except Exception:
                art_mode_status = "unknown"
                logging.warning("Art mode status unavailable (timeout/err); proceeding")
            logging.info(f"TV Power On: {power_on}, Art Mode: {art_mode_status}")

            is_in_art_or_standby = (not power_on) or (art_mode_status == "on")

            if args.power_state_check and not is_in_art_or_standby:
                logging.info("TV is actively in use (e.g., watching a movie). Skipping rotation.")
                await asyncio.sleep(interval_seconds)
                continue

            if args.turn_on_art_mode and not power_on:
                logging.info("TV is in Standby. Sending command to activate Art Mode...")
                try:
                    await tv.set_artmode(True)
                except Exception:
                    # Fallback to power toggle if direct Art Mode fails
                    await tv.send_key("KEY_POWER")
                await asyncio.sleep(5) # Give TV time to wake up

            # 2.5. Show-only path: assert current artwork is shown and skip upload
            if args.show_only:
                try:
                    info = await asyncio.wait_for(tv.get_current(), timeout=5)
                    current_content_id = info.get('content_id') if info else None
                    if current_content_id:
                        await tv.select_image(current_content_id, show=True)
                        logging.info(f"Ensured current artwork is showing: {current_content_id}")
                    else:
                        logging.info("No current artwork found to show.")
                except Exception as e:
                    logging.warning(f"Show-only failed to ensure artwork: {e}")
                logging.info(f"Show-only complete. Sleeping for {args.rotation_interval} minutes...")
                await asyncio.sleep(interval_seconds)
                continue

            # 3. Get Current Artwork (best-effort; don't fail cycle)
            current_content_id = None
            try:
                info = await asyncio.wait_for(tv.get_current(), timeout=5)
                current_content_id = info.get('content_id') if info else None
                logging.info(f"Successfully connected. Current artwork ID: {current_content_id}")
            except Exception as e:
                logging.warning(f"Failed to get current artwork (skipping deletion this cycle): {e}")

            # 4. Select a New Image
            uploaded_photos = load_uploaded_history()
            all_photos = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg'))]
            
            if not all_photos:
                logging.warning(f"No images found in {folder_path}. Skipping rotation.")
                await asyncio.sleep(interval_seconds)
                continue

            available_photos = [p for p in all_photos if p not in uploaded_photos]
            if not available_photos:
                logging.info("All photos have been shown recently. Resetting selection pool.")
                available_photos = all_photos

            selected_photo_name = random.choice(available_photos)
            filename = os.path.join(folder_path, selected_photo_name)
            logging.info(f"Selected new photo: {selected_photo_name}")

            # 5. Process and Upload Image
            with open(filename, "rb") as f: image_data = f.read()
            logging.info("Resizing and cropping image...")
            utils = Utils(None, None)
            # Force JPEG output to match upload file_type below
            resized_image_data = utils.resize_and_crop_image(image_data, format_hint='jpg')

            # Small settle before upload to avoid handshake flakiness
            await asyncio.sleep(0.5)

            matte_var = f"{args.matte}_{args.matte_color}" if args.matte != 'none' else 'none'
            matte_arg = None if matte_var == 'none' else matte_var

            image_bytes = resized_image_data.getvalue()
            logging.info("Prepared JPEG payload bytes: %d (matte=%s)", len(image_bytes), matte_arg or 'omitted')

            # Upload as JPEG as per API docs, with timeout and one retry
            try:
                new_content_id = await asyncio.wait_for(
                    tv.upload(image_bytes, file_type='JPEG', matte=matte_arg), timeout=20
                )
            except Exception as e:
                logging.warning("Upload attempt 1 failed (%s); retrying after short backoff", e)
                await asyncio.sleep(2)
                new_content_id = await asyncio.wait_for(
                    tv.upload(image_bytes, file_type='JPEG', matte=matte_arg), timeout=20
                )

            logging.info(f"Successfully uploaded image as {new_content_id}")

            # 6. Display New Image
            await tv.select_image(new_content_id, show=True)
            if str(args.filter).lower() != 'none':
                try:
                    await tv.set_photo_filter(new_content_id, args.filter)
                except Exception as e:
                    logging.warning(f"Failed to set photo filter '{args.filter}': {e}")
            logging.info("Set new image as active artwork.")

            # 7. Delete Old Image
            if current_content_id and current_content_id != new_content_id and not str(current_content_id).startswith('SAM-'):
                await tv.delete_list([current_content_id])
                logging.info(f"Deleted old artwork: {current_content_id}")

            # 8. Update History
            uploaded_photos.append(selected_photo_name)
            while len(uploaded_photos) > 50: uploaded_photos.pop(0)
            save_uploaded_history(uploaded_photos)
            
            logging.info(f"Rotation cycle complete. Shown: {selected_photo_name} (content_id={new_content_id})")

        except Exception as e:
            logging.error(f"An unexpected error occurred in the rotation cycle:", exc_info=True)
        finally:
            if tv:
                await tv.close()
            logging.info(f"Sleeping for {args.rotation_interval} minutes...")
            await asyncio.sleep(interval_seconds)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Add-on stopped by user.")