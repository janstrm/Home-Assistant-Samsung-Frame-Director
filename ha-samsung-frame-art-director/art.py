import sys
import random
import json
import os
import asyncio
import logging
import argparse
from utils.utils import Utils


sys.path.append('../')

from samsungtvws.async_art import SamsungTVAsyncArt
from samsungtvws import exceptions



logging.basicConfig(level=logging.INFO) #or logging.DEBUG to see messages

def parseargs():
    # Add command line argument parsing
    parser = argparse.ArgumentParser(description='Example async art Samsung Frame TV.')
    parser.add_argument('--ip', action="store", type=str, default=None, help='ip address of TV (default: %(default)s))')
    parser.add_argument('--filter', action="store", type=str, default="none", help='photo filter to apply (default: %(default)s))')
    parser.add_argument('--matte', action="store", type=str, default="none", help='matte to apply (default: %(default)s))')
    parser.add_argument('--matte-color', action="store", type=str, default="black", help='matte color to apply (default: %(default)s))')
    parser.add_argument('--ai-art', action="store_true", help='Enable AI Art generation')
    parser.add_argument('--prompt', action="store", type=str, default="", help='Prompt for AI Art generation')
    parser.add_argument('--api-key', action="store", type=str, default="", help='API Key for AI service')
    parser.add_argument('--rotation-interval', action="store", type=int, default=15, help='Rotation interval in minutes')
    parser.add_argument('--show-only', action="store_true", help='Only ensure Art Mode is showing the current image')
    parser.add_argument('--debug', action="store_true", help='Enable debug logging')
    return parser.parse_args()
    



# Set the path to the folder containing the images
folder_path = '/media/frame'

uploaded_json_path = '/data/uploaded.json'


# Load the list of last 5 uploaded pictures
if os.path.exists(uploaded_json_path):
    with open(uploaded_json_path, 'r') as file:
        uploaded_photos = json.load(file)
else:
    uploaded_photos = []

# Selection now happens inside the service loop



async def stdin_listener(queue: asyncio.Queue):
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    while True:
        line = await reader.readline()
        if not line:
            await asyncio.sleep(0.1)
            continue
        try:
            message = json.loads(line.decode().strip())
            await queue.put(message)
        except Exception:
            logging.warning('Received invalid JSON on stdin: {}'.format(line))


async def handle_command(tv, command: dict):
    action = command.get('action')
    if action == 'load_image':
        filename = command.get('filename')
        if not filename:
            logging.warning('load_image command missing filename')
            return
        await process_and_show_image(tv, filename)
    else:
        logging.warning('Unknown command: {}'.format(action))


async def process_and_show_image(tv, filename: str, matte_var: str = 'none', photo_filter: str = 'none', selected_photo_name: str = None):
    try:
        with open(filename, "rb") as f:
            image_data = f.read()

        logging.info('Resizing and cropping the image...')
        utils = Utils(None, None)
        file_type = os.path.splitext(filename)[1][1:]
        resized_image_data = utils.resize_and_crop_image(image_data, format_hint=file_type)

        content_id = await tv.upload(resized_image_data.getvalue(), file_type=file_type, matte=matte_var)
        logging.info('uploaded {} to tv as {}'.format(filename, content_id))
        await tv.set_photo_filter(content_id, photo_filter)
        await tv.select_image(content_id, show=False)
        logging.info('set artwork to {}'.format(content_id))
        return content_id
    except FileNotFoundError:
        logging.error('Image file not found at {}. Skipping.'.format(filename))
    except Exception as e:
        logging.error('An error occurred during image processing or upload: {}'.format(e))
    return None


async def main():
    args = parseargs()
    logging.getLogger().setLevel(logging.DEBUG if args.debug else logging.INFO)


    matte = args.matte
    matte_color = args.matte_color

    # Set the matte and matte color

    if matte != 'none':
        matte_var = f"{matte}_{matte_color}"
    else:
        matte_var = matte



    tv = None
    command_queue: asyncio.Queue = asyncio.Queue()
    listener_task = asyncio.create_task(stdin_listener(command_queue))
    interval_seconds = max(1, int(args.rotation_interval) * 60)

    try:
        tv = SamsungTVAsyncArt(host=args.ip, port=8002)
        await tv.start_listening()

        supported = await tv.supported()
        if not supported:
            logging.info('This TV is not supported')
        else:
            logging.info('This TV is supported')

        while True:
            # Process any pending stdin commands first
            try:
                while True:
                    cmd = command_queue.get_nowait()
                    await handle_command(tv, cmd)
            except asyncio.QueueEmpty:
                pass

            try:
                # Ensure TV is reachable and get current state
                tv_on = await tv.on()
                logging.info('tv is on: {}'.format(tv_on))
                art_mode = tv.art_mode
                logging.info('art mode is on: {}'.format(art_mode))

                info = await tv.get_current()
                current_content_id = info.get('content_id') if info else None

                if args.show_only:
                    if current_content_id:
                        await tv.select_image(current_content_id, show=True)
                        logging.info('ensured current artwork is showing: {}'.format(current_content_id))
                else:
                    if args.ai_art:
                        logging.info('AI Art mode enabled; generation not implemented yet')
                    else:
                        photos = [
                            f for f in os.listdir(folder_path)
                            if os.path.isfile(os.path.join(folder_path, f)) and f.lower().endswith((".png", ".jpg"))
                        ]
                        if not photos:
                            logging.info('No PNG or JPG photos found in the folder')
                        else:
                            available_files = [f for f in photos if f not in uploaded_photos] if len(photos) > 5 else photos
                            if not available_files:
                                available_files = photos
                            selected_photo = random.choice(available_files)
                            filename = os.path.join(folder_path, selected_photo)
                            new_filename = os.path.join(folder_path, os.path.basename(filename).lower())
                            if filename != new_filename:
                                try:
                                    os.rename(filename, new_filename)
                                    filename = new_filename
                                except Exception:
                                    filename = new_filename
                            logging.info('Selected photo: {}'.format(filename))

                            content_id = await process_and_show_image(
                                tv, filename, matte_var=matte_var, photo_filter=args.filter, selected_photo_name=selected_photo
                            )
                            if content_id and current_content_id:
                                try:
                                    await tv.delete_list([current_content_id])
                                    logging.info('deleted from tv: {}'.format([current_content_id]))
                                except Exception as e:
                                    logging.warning('Failed to delete previous artwork: {}'.format(e))

                            # Update recent uploads
                            uploaded_photos.append(selected_photo)
                            if len(uploaded_photos) > 5:
                                uploaded_photos.pop(0)
                            try:
                                with open(uploaded_json_path, 'w') as file:
                                    json.dump(uploaded_photos, file)
                            except Exception as e:
                                logging.warning('Failed to update uploaded.json: {}'.format(e))

            except exceptions.ResponseError as e:
                logging.error('Received an error response from the TV: {}'.format(e))
            except exceptions.ConnectionFailure as e:
                logging.error('Could not connect to the TV at {}. Error: {}'.format(args.ip, e))
            except Exception as e:
                logging.error('Unexpected error in loop: {}'.format(e))

            # Wait for either a command or the interval timeout
            try:
                cmd = await asyncio.wait_for(command_queue.get(), timeout=interval_seconds)
                await handle_command(tv, cmd)
            except asyncio.TimeoutError:
                pass


asyncio.run(main())