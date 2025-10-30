#!/usr/bin/env python3
"""
Miro integration and upload tools
"""

import time
import re
import requests
from pathlib import Path
from PIL import Image
from urllib.parse import quote
from .utils import resize_keep_width, create_image_on_miro, MIRO_BOARD_ID, MIRO_TOKEN, MIRO_API, handle_miro_api_error
from .configuration import session_state

# Constants for upload optimization
UPLOAD_DELAY_SECONDS = 0.5
BATCH_DELAY_SECONDS = 2
MAX_IMAGES_PER_BATCH = 20
BATCH_ROW_SPACING = 50

def list_miro_boards_tool() -> str:
    """
    List all available Miro boards that the user has access to.
    
    This tool fetches all boards from the user's Miro account and displays them
    with their names, IDs, and creation dates. This helps users choose which
    board to upload their UX benchmark images to.
    
    Returns:
        str: Formatted list of available boards with selection instructions
    """
    try:
        if not MIRO_TOKEN:
            return "❌ No Miro token found. Please set MIRO_TOKEN in your .env file."
        
        headers = {
            "Authorization": f"Bearer {MIRO_TOKEN}",
            "accept": "application/json"
        }
        
        # Fetch boards from Miro API
        response = requests.get(f"{MIRO_API}/boards", headers=headers, timeout=30)
        response.raise_for_status()
        
        boards_data = response.json()
        boards = boards_data.get("data", [])
        
        if not boards:
            return "📋 No boards found in your Miro account. Create a board first in Miro, then try again."
        
        # Format board information
        board_list = []
        for i, board in enumerate(boards, 1):
            board_id = board.get("id", "Unknown")
            board_name = board.get("name", "Unnamed Board")
            created_at = board.get("createdAt", "Unknown date")
            
            # Format creation date
            if created_at != "Unknown date":
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    created_at = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            board_list.append(f"{i}. **{board_name}**\n   📋 ID: `{board_id}`\n   📅 Created: {created_at}")
        
        # Create formatted response
        result = f"📋 **Available Miro Boards** ({len(boards)} found):\n\n"
        result += "\n\n".join(board_list)
        result += f"\n\n🎯 **How to use:**\n"
        result += f"• Copy the board ID you want to use\n"
        result += f"• Update your `.env` file: `MIRO_BOARD_ID=your_board_id`\n"
        result += f"• Or tell me which board number you want to use\n"
        result += f"• Then I can upload your images directly to that board!\n\n"
        result += f"💡 **Tip:** Board names with 'UX', 'Benchmark', or 'Analysis' are great for UX work!"
        
        return result
        
    except requests.exceptions.RequestException as e:
        return handle_miro_api_error(e)
    except Exception as e:
        return f"❌ Error listing Miro boards: {str(e)}"

def list_miro_frames_tool(board_id: str = None) -> str:
    """
    List all frames in the specified Miro board.
    
    This tool fetches all frames from a Miro board and displays them
    with their names, IDs, positions, and sizes. This helps users choose
    which frame to upload their UX benchmark images into.
    
    Args:
        board_id (str, optional): Miro board ID. If not provided, uses current board ID
    
    Returns:
        str: Formatted list of available frames with selection instructions
    """
    try:
        if not MIRO_TOKEN:
            return "❌ No Miro token found. Please set MIRO_TOKEN in your .env file."
        
        # Use provided board_id or current one
        target_board_id = board_id or MIRO_BOARD_ID
        if not target_board_id:
            return "❌ No board ID specified. Please provide a board ID or set MIRO_BOARD_ID in your .env file."
        
        headers = {
            "Authorization": f"Bearer {MIRO_TOKEN}",
            "accept": "application/json"
        }
        
        # Fetch frames from Miro API
        encoded_board_id = quote(target_board_id, safe='')
        response = requests.get(f"{MIRO_API}/boards/{encoded_board_id}/items?type=frame", headers=headers, timeout=30)
        response.raise_for_status()
        
        frames_data = response.json()
        frames = frames_data.get("data", [])
        
        if not frames:
            return f"📋 No frames found in this board. Create a frame first in Miro, then try again.\n\n💡 **Tip:** Frames are great for organizing UX benchmarks - they keep related screenshots grouped together!"
        
        # Format frame information
        frame_list = []
        for i, frame in enumerate(frames, 1):
            frame_id = frame.get("id", "Unknown")
            frame_name = frame.get("data", {}).get("title", "Unnamed Frame")
            position = frame.get("position", {})
            x = position.get("x", 0)
            y = position.get("y", 0)
            geometry = frame.get("geometry", {})
            width = geometry.get("width", 0)
            height = geometry.get("height", 0)
            
            # Format dimensions
            dimensions = f"{int(width)}×{int(height)}" if width and height else "Unknown size"
            position_str = f"({int(x)}, {int(y)})" if x is not None and y is not None else "Unknown position"
            
            frame_list.append(f"{i}. **{frame_name}**\n   📋 ID: `{frame_id}`\n   📐 Size: {dimensions}\n   📍 Position: {position_str}")
        
        # Create formatted response
        result = f"📋 **Available Frames** ({len(frames)} found):\n\n"
        result += "\n\n".join(frame_list)
        result += f"\n\n🎯 **How to use:**\n"
        result += f"• Tell me which frame number you want to use\n"
        result += f"• Or provide the frame ID directly\n"
        result += f"• I'll upload your images inside that frame\n"
        result += f"• Images will be arranged side-by-side within the frame\n\n"
        result += f"💡 **Tip:** Choose a frame that's large enough for your images!"
        
        return result
        
    except requests.exceptions.RequestException as e:
        return handle_miro_api_error(e)
    except Exception as e:
        return f"❌ Error listing Miro frames: {str(e)}"

def set_miro_board_tool(board_id: str) -> str:
    """
    Set the Miro board ID for uploads.
    
    This tool allows users to dynamically change which Miro board to upload to
    without needing to edit the .env file manually.
    
    Args:
        board_id (str): The Miro board ID to use for uploads
    
    Returns:
        str: Confirmation message with board ID set
    """
    try:
        # Validate the board ID by trying to fetch board info
        headers = {
            "Authorization": f"Bearer {MIRO_TOKEN}",
            "accept": "application/json"
        }
        
        # Test if board exists and is accessible
        response = requests.get(f"{MIRO_API}/boards/{board_id}", headers=headers, timeout=30)
        response.raise_for_status()
        
        board_data = response.json()
        board_name = board_data.get("name", "Unknown Board")
        
        # Update the global board ID
        global MIRO_BOARD_ID
        MIRO_BOARD_ID = board_id
        
        return f"✅ Board ID updated successfully!\n\n📋 **Selected Board:**\n• Name: {board_name}\n• ID: `{board_id}`\n\n🎯 Ready to upload images to this board!"
        
    except requests.exceptions.RequestException as e:
        return handle_miro_api_error(e)
    except Exception as e:
        return f"❌ Error setting board ID: {str(e)}"

def get_frame_start_position(frame_id: str, first_image_width: int, first_image_height: int) -> tuple:
    """
    Get the starting position for images at a frame's location on the board.
    Uses ABSOLUTE board coordinates, not frame-relative coordinates.
    Places images at the frame's location without using the parent field.
    
    Args:
        frame_id: The Miro frame ID
        first_image_width: Width of the first image (to calculate proper offset)
        first_image_height: Height of the first image (to calculate proper offset)
    
    Returns:
        (x, y) ABSOLUTE board coordinates for positioning images at the frame's top-left with padding.
    """
    try:
        headers = {
            "Authorization": f"Bearer {MIRO_TOKEN}",
            "accept": "application/json"
        }
        
        # Fetch frame details
        encoded_board_id = quote(MIRO_BOARD_ID, safe='')
        response = requests.get(f"{MIRO_API}/boards/{encoded_board_id}/items/{frame_id}", headers=headers, timeout=30)
        response.raise_for_status()
        
        frame_data = response.json()
        position = frame_data.get("position", {})
        geometry = frame_data.get("geometry", {})
        
        # Frame's absolute position on the board (center point)
        frame_center_x = position.get("x", 0)
        frame_center_y = position.get("y", 0)
        
        # Frame dimensions
        frame_width = geometry.get("width", 2000)
        frame_height = geometry.get("height", 2000)
        
        print(f"📐 Frame dimensions: {frame_width}×{frame_height}")
        print(f"📍 Frame center on board: ({frame_center_x}, {frame_center_y})")
        
        # Calculate top-left corner of frame in ABSOLUTE board coordinates
        # Frame center - half width/height = top-left corner
        # Add padding from edge, and half image size (since Miro positions by center)
        padding = 300
        start_x = frame_center_x - (frame_width / 2) + padding + (first_image_width / 2)
        start_y = frame_center_y - (frame_height / 2) + padding + (first_image_height / 2)
        
        print(f"📍 Calculated board position (top-left + padding): ({int(start_x)}, {int(start_y)})")
        
        return (start_x, start_y)
        
    except Exception as e:
        print(f"⚠️  Could not get frame position: {e}")
        print(f"⚠️  Frame ID: {frame_id}")
        print(f"⚠️  Image dimensions: {first_image_width}×{first_image_height}")
        print(f"⚠️  Using default position (0, 0)")
        return (0, 0)

def upload_all_images_tool(app_name: str, start_x: float = 0, start_y: float = 0, max_images_per_batch: int = MAX_IMAGES_PER_BATCH, frame_id: str = None) -> str:
    """
    Automatically plan and execute all image uploads in multiple batches.
    
    This tool intelligently handles multiple uploads by:
    1. Counting total images
    2. Calculating required batches
    3. Executing each batch automatically
    4. Providing clear progress updates
    5. Optionally uploading inside a specific frame
    
    Args:
        app_name (str): Name of the app to upload images for
        start_x (float, optional): Starting X position on Miro board (default: 0)
        start_y (float, optional): Starting Y position on Miro board (default: 0)
        max_images_per_batch (int, optional): Maximum images per batch (default: 20)
        frame_id (str, optional): Frame ID to upload images inside (default: None for board upload)
    
    Returns:
        str: Complete upload summary with all batches executed
    """
    try:
        output_dir = session_state["output_dir"]
        app_dir = output_dir / app_name
        
        if not app_dir.exists():
            return f"❌ No images found for app '{app_name}'. Process a video first!"
        
        # Get all image files sorted by creation time (chronological order)
        image_files = []
        for file_path in app_dir.glob("*.jpg"):
            if file_path.is_file():
                image_files.append(file_path)
        
        if not image_files:
            return f"❌ No images found for app '{app_name}'"
        
        # Sort by file modification time to get chronological order (oldest first)
        # This ensures correct order: 0.83s, 3.62s, 16.66s (not alphabetical 16.66s, 3.62s, 0.83s)
        image_files.sort(key=lambda x: x.stat().st_mtime)
        total_images = len(image_files)
        
        # Calculate number of batches needed
        total_batches = (total_images + max_images_per_batch - 1) // max_images_per_batch
        
        # If uploading to a frame, calculate proper starting position
        if frame_id and start_x == 0 and start_y == 0:
            # Load first image to get dimensions for proper positioning
            first_img = Image.open(image_files[0])
            first_img = resize_keep_width(first_img, session_state["image_width"])
            frame_start_x, frame_start_y = get_frame_start_position(frame_id, first_img.width, first_img.height)
            start_x = frame_start_x
            start_y = frame_start_y
            print(f"📍 Frame detected - starting at ({int(start_x)}, {int(start_y)}) with 50px padding")
        
        print(f"📊 Found {total_images} total images for '{app_name}'")
        print(f"📦 Planning {total_batches} batch(es) of up to {max_images_per_batch} images each")
        
        if total_batches == 1:
            print("🚀 Single batch upload - executing now...")
            return upload_images_tool(app_name, start_x, start_y, max_images_per_batch, 1, auto_plan=False, frame_id=frame_id)
        
        # Multiple batches - execute each one with proper positioning
        print(f"🚀 Multiple batches required - executing all {total_batches} batches automatically...")
        
        total_uploaded = 0
        total_failed = 0
        current_x = start_x
        current_y = start_y
        
        for batch_num in range(1, total_batches + 1):
            print(f"\n📦 Executing batch {batch_num}/{total_batches}...")
            
            # Calculate batch range
            batch_start_idx = (batch_num - 1) * max_images_per_batch
            batch_end_idx = min(batch_start_idx + max_images_per_batch, total_images)
            batch_images = image_files[batch_start_idx:batch_end_idx]
            
            # Calculate actual dimensions for this batch
            batch_max_height = 0
            batch_total_width = 0
            
            for img_path in batch_images:
                try:
                    img = Image.open(img_path)
                    img = resize_keep_width(img, session_state["image_width"])
                    
                    # Track dimensions
                    batch_max_height = max(batch_max_height, img.height)
                    
                    if session_state["layout"] == "horizontal":
                        batch_total_width += img.width + session_state["image_spacing"]
                    else:
                        batch_total_width = max(batch_total_width, img.width)
                except Exception:
                    continue
            
            # Remove last spacing from width calculation
            if session_state["layout"] == "horizontal" and batch_total_width > 0:
                batch_total_width -= session_state["image_spacing"]
            
            print(f"📐 Batch {batch_num} dimensions: {batch_total_width}×{batch_max_height}")
            
            # Execute this batch
            batch_result = upload_images_tool(app_name, current_x, current_y, max_images_per_batch, batch_num, auto_plan=False, frame_id=frame_id)
            
            # Extract success/failure counts from result
            if "Successfully uploaded" in batch_result:
                # Extract number from "Successfully uploaded X images"
                match = re.search(r'Successfully uploaded (\d+) images', batch_result)
                if match:
                    total_uploaded += int(match.group(1))
            elif "failed" in batch_result:
                # Extract failure count
                match = re.search(r'(\d+) failed', batch_result)
                if match:
                    total_failed += int(match.group(1))
            
            # Update position for next batch
            if session_state["layout"] == "horizontal":
                # For horizontal layout, move to next row
                current_x = start_x
                current_y += batch_max_height + session_state["image_spacing"] + BATCH_ROW_SPACING
            else:
                # For vertical layout, continue down
                current_y += batch_max_height + session_state["image_spacing"] + BATCH_ROW_SPACING
            
            print(f"📍 Next batch will start at ({current_x},{current_y})")
            
            # Small delay between batches to avoid rate limits
            if batch_num < total_batches:
                print("⏳ Brief pause between batches...")
                time.sleep(BATCH_DELAY_SECONDS)
        
        # Final summary
        if total_failed == 0:
            return f"🎉 All uploads completed successfully!\n\n📊 Summary:\n• Total images uploaded: {total_uploaded}\n• Batches executed: {total_batches}\n• All images are now on your Miro board!\n\n✅ Your '{app_name}' UX benchmark is ready!"
        else:
            return f"⚠️ Uploads completed with some issues:\n\n📊 Summary:\n• Images uploaded: {total_uploaded}\n• Images failed: {total_failed}\n• Batches executed: {total_batches}\n\nCheck rate limits and retry failed uploads if needed."
        
    except Exception as e:
        return f"❌ Error in automatic upload planning: {str(e)}"

def upload_images_tool(app_name: str, start_x: float = 0, start_y: float = 0, max_images: int = 20, batch_number: int = 1, auto_plan: bool = True, frame_id: str = None) -> str:
    """
    Upload existing local images to Miro board with proper batch management.
    
    This tool takes the images you've reviewed and approved locally,
    uploads them to your Miro board with the current layout settings.
    Always starts from the beginning of the image list for consistent ordering.
    
    Args:
        app_name (str): Name of the app to upload images for (must match processed app name)
        start_x (float, optional): Starting X position on Miro board (default: 0)
        start_y (float, optional): Starting Y position on Miro board (default: 0)
        max_images (int, optional): Maximum number of images per batch (default: 20)
        batch_number (int, optional): Which batch to upload (1 = first batch, 2 = second batch, etc.)
    
    Related Settings (configurable via configure_settings_tool):
        - image_width: Resize images to this width before upload (default: 600px)
        - image_spacing: Gap between images (default: 100px)
        - layout: "horizontal" (side-by-side) or "vertical" (top-to-bottom)
    
    Returns:
        str: Success message with upload details and next batch info if applicable
    
    Examples:
        - upload_images_tool("Willow")  # Upload first 20 images at default position
        - upload_images_tool("MyApp", batch_number=2)  # Upload second batch of 20 images
        - upload_images_tool("MyApp", max_images=10)  # Upload only 10 images
    """
    try:
        output_dir = session_state["output_dir"]
        app_dir = output_dir / app_name
        
        if not app_dir.exists():
            return f"❌ No images found for app '{app_name}'. Process a video first!"
        
        # Get all image files sorted by creation time (chronological order)
        image_files = []
        for file_path in app_dir.glob("*.jpg"):
            if file_path.is_file():
                image_files.append(file_path)
        
        if not image_files:
            return f"❌ No images found for app '{app_name}'"
        
        # Sort by file modification time to get chronological order (oldest first)
        # This ensures correct order: 0.83s, 3.62s, 16.66s (not alphabetical 16.66s, 3.62s, 0.83s)
        image_files.sort(key=lambda x: x.stat().st_mtime)
        
        # Calculate batch range
        total_images = len(image_files)
        start_idx = (batch_number - 1) * max_images
        end_idx = min(start_idx + max_images, total_images)
        
        if start_idx >= total_images:
            return f"❌ Batch {batch_number} is beyond available images. Total images: {total_images}"
        
        # Get images for this batch
        batch_images = image_files[start_idx:end_idx]
        
        # If uploading to a frame, calculate proper starting position
        if frame_id and start_x == 0 and start_y == 0:
            # Load first image to get dimensions for proper positioning
            first_img = Image.open(batch_images[0])
            first_img = resize_keep_width(first_img, session_state["image_width"])
            frame_start_x, frame_start_y = get_frame_start_position(frame_id, first_img.width, first_img.height)
            start_x = frame_start_x
            start_y = frame_start_y
            print(f"📍 Frame detected - starting at ({int(start_x)}, {int(start_y)}) with 50px padding")
        
        print(f"📊 Found {total_images} total images for '{app_name}'")
        print(f"📦 Uploading batch {batch_number}: images {start_idx+1}-{end_idx} ({len(batch_images)} images)")
        
        x = start_x
        y = start_y
        successful_uploads = 0
        failed_uploads = 0
        current_row_height = 0  # Track height of current row for batch spacing
        
        for i, img_path in enumerate(batch_images, 1):
            temp_path = None
            try:
                # Load and resize image
                img = Image.open(img_path)
                img = resize_keep_width(img, session_state["image_width"])
                
                # Calculate image dimensions after resize
                img_width = img.width
                img_height = img.height
                
                # Update current row height if this image is taller
                current_row_height = max(current_row_height, img_height)
                
                # Save resized image to temporary file and upload directly
                temp_path = output_dir / f"_temp_{img_path.name}"
                img.save(temp_path, format="JPEG", quality=95, optimize=True, progressive=True)
                img_item = create_image_on_miro(MIRO_BOARD_ID, temp_path, x, y, frame_id)
                
                print(f"  [{i}/{len(batch_images)}] {img_path.name} -> uploaded at ({x},{y}) [{img_width}×{img_height}]")
                successful_uploads += 1
                
                # Update position for next image
                if session_state["layout"] == "horizontal":
                    x += img_width + session_state["image_spacing"]
                else:
                    y += img_height + session_state["image_spacing"]
                
                # Rate limiting: small delay between uploads
                if i < len(batch_images):  # Don't delay after last image
                    time.sleep(UPLOAD_DELAY_SECONDS)
                    
            except Exception as e:
                print(f"  [{i}/{len(batch_images)}] {img_path.name} -> FAILED: {e}")
                failed_uploads += 1
            finally:
                # Always clean up temp file, whether upload succeeded or failed
                if temp_path and temp_path.exists():
                    temp_path.unlink()
        
        # Summary with batch information
        remaining_images = total_images - end_idx
        if failed_uploads == 0:
            if remaining_images > 0:
                return f"✅ Successfully uploaded batch {batch_number} ({successful_uploads} images) for '{app_name}' to Miro board!\n📦 Next batch: {remaining_images} images remaining. Use batch_number={batch_number + 1} to continue."
            else:
                return f"✅ Successfully uploaded all {successful_uploads} images for '{app_name}' to Miro board! 🎉"
        else:
            return f"⚠️  Uploaded {successful_uploads} images successfully, {failed_uploads} failed. Check rate limits and try again later."
        
    except Exception as e:
        return f"❌ Error uploading images: {str(e)}"
