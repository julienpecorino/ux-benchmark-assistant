#!/usr/bin/env python3
"""
Video processing and keyframe extraction tools
"""

import cv2
from pathlib import Path
from .utils import hsv_hist, hist_distance, bgr_to_pil, resize_keep_width
from .configuration import session_state

def save_image_locally(img, app_name: str, timestamp: float, output_dir: Path) -> Path:
    """Save image locally with timestamp"""
    app_dir = output_dir / app_name
    app_dir.mkdir(exist_ok=True)
    
    timestamp_str = f"{timestamp:.2f}s"
    filename = f"{timestamp_str}.jpg"
    filepath = app_dir / filename
    
    img.save(filepath, "JPEG", quality=85, optimize=True)
    return filepath

def process_video_tool(video_name: str, app_name: str, max_frames: int = None, chunk_size: int = 50) -> str:
    """
    Process a video file and extract keyframes, saving them locally for review.
    
    This tool analyzes the video for screen changes and extracts important frames.
    Images are saved locally first so users can review and delete unwanted ones.
    
    Args:
        video_name (str): Name of video file in the 'video/' folder (e.g., "willo.MP4", "app-demo.mp4")
        app_name (str): Friendly name for the app being analyzed (e.g., "Willow", "MyApp")
        max_frames (int, optional): Maximum number of keyframes to extract. 
                                     Defaults to session setting (currently 0 = unlimited).
                                     Processes entire video from start to finish by default.
        chunk_size (int, optional): Number of frames to process at once to avoid memory issues.
                                    Default: 50. Lower values use less memory.
    
    Related Settings (configurable via configure_settings_tool):
        - image_width: Resize extracted images to this width (default: 600px)
        - fps: Sample video at this rate for change detection (default: 5 fps for better accuracy)
        - diff_thresh: Sensitivity for detecting changes (0-1, default: 0.20, lower=more sensitive)
        - transition_delay: Delay after detecting change before capturing (default: 1.0s)
                           Ensures screenshots are taken after screen transitions complete.
                           Frame spacing is handled automatically - no separate stride parameter needed.
    
    Returns:
        str: Success message with path to saved images and next steps
    
    Examples:
        - process_video_tool("willo.MP4", "Willow")
        - process_video_tool("demo.mp4", "MyApp", max_frames=20)
        - process_video_tool("long-video.mp4", "App", max_frames=50, chunk_size=100)
    """
    try:
        # Use session defaults if not specified
        if max_frames is None:
            max_frames = session_state["max_frames"]
        
        # Try exact match first
        video_path = Path("video") / video_name
        if not video_path.exists():
            # Try case-insensitive match
            video_dir = Path("video")
            if video_dir.exists():
                # Get all video files
                video_files = list(video_dir.glob("*"))
                # Find case-insensitive match
                for video_file in video_files:
                    if video_file.name.lower() == video_name.lower():
                        video_path = video_file
                        break
                else:
                    # Still not found, provide helpful error
                    available_videos = [f.name for f in video_files if f.is_file()]
                    if available_videos:
                        return f"❌ Video file not found: {video_name}\n💡 Available videos: {', '.join(available_videos)}"
                    else:
                        return f"❌ Video file not found: {video_name}\n💡 No videos found in 'video/' folder"
        
        output_dir = session_state["output_dir"]
        output_dir.mkdir(exist_ok=True)
        
        # Add to current apps
        if app_name not in session_state["current_apps"]:
            session_state["current_apps"].append(app_name)
        
        print(f"🎬 Processing video: {video_name}")
        print(f"📱 App name: {app_name}")
        print(f"📊 Max frames: {max_frames}")
        
        # Open video
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return f"❌ Cannot open video: {video_name}"
        
        video_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        every = max(int(round(video_fps / session_state["fps"])), 1)
        
        # Calculate frame timestamps based on frame index and FPS for accuracy
        def get_frame_timestamp(frame_idx):
            return (frame_idx / video_fps)
        
        keyframes_saved = 0
        last_hist = None
        last_keep_idx = -10**9
        idx = 0
        chunk_count = 0
        
        # Change detection with automatic transition delay
        transition_delay = session_state["transition_delay"]
        
        # Track pending captures: stores (capture_timestamp, change_timestamp, change_frame, change_hist, prev_hist)
        # prev_hist is the histogram of the frame before current, used for stability checking
        pending_captures = []
        
        # Track last processed frame for cleanup
        last_processed_frame = None
        last_processed_timestamp = 0.0
        prev_frame_hist = None  # Previous frame histogram for stability checking
        
        while keyframes_saved < max_frames or max_frames == 0:
            # Process in chunks
            chunk_frames = []
            for _ in range(chunk_size):
                ret, frame = cap.read()
                if not ret:
                    break
                chunk_frames.append((idx, frame))
                idx += 1
            
            if not chunk_frames:
                break
            
            # Process chunk
            for frame_idx, frame in chunk_frames:
                if frame_idx % every != 0:
                    continue
                    
                t = get_frame_timestamp(frame_idx)
                h = hsv_hist(frame)
                
                # Track last processed frame for cleanup
                last_processed_frame = frame
                last_processed_timestamp = t
                
                # Check for pending captures that are ready
                ready_captures = [pc for pc in pending_captures if t >= pc[0]]
                captures_to_remove = []
                captures_to_add = []
                
                for capture_info in ready_captures:
                    capture_time, change_time, change_frame, change_hist, prev_hist_check = capture_info if len(capture_info) == 5 else (*capture_info, None)
                    
                    # Verify screen is stable by comparing consecutive frames
                    # If consecutive frames are similar, the screen has stabilized
                    # Stability threshold is automatically calculated as 40% of diff_thresh
                    # This is more lenient than change detection, allowing for subtle animations
                    if prev_frame_hist is not None:
                        consecutive_d = hist_distance(prev_frame_hist, h)
                        # Automatic stability threshold: more lenient for mobile app transitions
                        stability_threshold = session_state["diff_thresh"] * 0.4
                        
                        if consecutive_d < stability_threshold:
                            # Consecutive frames are similar - screen is stable, capture it
                            img = bgr_to_pil(frame)
                            img = resize_keep_width(img, session_state["image_width"])
                            save_image_locally(img, app_name, t, output_dir)
                            keyframes_saved += 1
                            last_hist = h
                            last_keep_idx = frame_idx
                            prev_frame_hist = h  # Update for next iteration
                            print(f"  ✅ Saved keyframe at {t:.2f}s (after {t - change_time:.1f}s delay from change at {change_time:.2f}s)")
                            captures_to_remove.append(capture_info)
                        else:
                            # Consecutive frames still different - transition ongoing, extend delay
                            new_capture_time = t + transition_delay
                            captures_to_remove.append(capture_info)
                            captures_to_add.append((new_capture_time, change_time, frame, h, h))
                            print(f"  ⏳ Transition ongoing at {t:.2f}s (change detected at {change_time:.2f}s), extending delay to {new_capture_time:.2f}s")
                    else:
                        # No previous frame to compare - capture anyway (shouldn't happen often)
                        img = bgr_to_pil(frame)
                        img = resize_keep_width(img, session_state["image_width"])
                        save_image_locally(img, app_name, t, output_dir)
                        keyframes_saved += 1
                        last_hist = h
                        last_keep_idx = frame_idx
                        prev_frame_hist = h  # Update for next iteration
                        print(f"  ✅ Saved keyframe at {t:.2f}s (after {t - change_time:.1f}s delay from change at {change_time:.2f}s)")
                        captures_to_remove.append(capture_info)
                
                # Update pending captures list
                for item in captures_to_remove:
                    pending_captures.remove(item)
                pending_captures.extend(captures_to_add)
                
                if last_hist is None:
                    # First frame - always save immediately
                    img = bgr_to_pil(frame)
                    img = resize_keep_width(img, session_state["image_width"])
                    save_image_locally(img, app_name, t, output_dir)
                    keyframes_saved += 1
                    last_hist = h
                    last_keep_idx = frame_idx
                    prev_frame_hist = h  # Update for next iteration
                    print(f"  ✅ Saved keyframe at {t:.2f}s (first frame)")
                else:
                    d = hist_distance(last_hist, h)
                    
                    # Check if this is a significant change
                    # Note: Frame spacing is now handled automatically by transition_delay
                    if d >= session_state["diff_thresh"]:
                        # Don't capture immediately - schedule capture after transition_delay
                        capture_timestamp = t + transition_delay
                        # Store with previous histogram for stability checking
                        pending_captures.append((capture_timestamp, t, frame, h, prev_frame_hist))
                        # Update tracking but don't save yet
                        last_hist = h
                        prev_frame_hist = h  # Update for next iteration
                        print(f"  🔍 Change detected at {t:.2f}s (distance: {d:.3f}), will capture at {capture_timestamp:.2f}s")
                    else:
                        # No change detected, just update previous histogram
                        prev_frame_hist = h
            
            chunk_count += 1
            print(f"  📦 Processed chunk {chunk_count}, total keyframes: {keyframes_saved}")
            
            if max_frames > 0 and keyframes_saved >= max_frames:
                break
        
        # Process any remaining pending captures before closing
        if pending_captures:
            # Capture using the last processed frame (best approximation)
            if last_processed_frame is not None:
                for capture_info in pending_captures:
                    capture_time = capture_info[0]
                    change_time = capture_info[1]
                    # Use the last processed frame for more accurate capture
                    img = bgr_to_pil(last_processed_frame)
                    img = resize_keep_width(img, session_state["image_width"])
                    save_image_locally(img, app_name, last_processed_timestamp, output_dir)
                    keyframes_saved += 1
                    print(f"  ✅ Saved final keyframe at {last_processed_timestamp:.2f}s (pending capture from {change_time:.2f}s)")
            else:
                # Fallback: use stored frame from when change was detected
                for capture_info in pending_captures:
                    capture_time = capture_info[0]
                    change_time = capture_info[1]
                    change_frame = capture_info[2]
                    img = bgr_to_pil(change_frame)
                    img = resize_keep_width(img, session_state["image_width"])
                    save_image_locally(img, app_name, capture_time, output_dir)
                    keyframes_saved += 1
                    print(f"  ✅ Saved final keyframe at {capture_time:.2f}s (pending capture from {change_time:.2f}s)")
        
        cap.release()
        
        warning_msg = ""
        if keyframes_saved > 20:
            warning_msg = f"\n⚠️  WARNING: {keyframes_saved} images is a lot! Consider deleting some before uploading to avoid rate limits.\n"
        elif keyframes_saved > 15:
            warning_msg = f"\n💡 TIP: {keyframes_saved} images is quite a few. You might want to review and delete some before uploading.\n"
        
        return f"✅ Processing complete! {keyframes_saved} keyframes saved to {output_dir / app_name}{warning_msg}\n📁 Next step: Review the images in the screenshots folder and delete any you don't want to keep.\n\n🎯 When you're ready, I can upload the remaining images to your Miro board with the current spacing settings (currently {session_state['image_spacing']}px between images in {session_state['layout']} layout).\n\nJust say 'upload to Miro' or 'proceed with upload' when you're ready!"
        
    except Exception as e:
        return f"❌ Error processing video: {str(e)}"
