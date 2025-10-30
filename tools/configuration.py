#!/usr/bin/env python3
"""
Configuration and session management tools
"""

from pathlib import Path

# Global state for the session
session_state = {
    "current_apps": [],
    "output_dir": Path("screenshots"),
    "image_width": 600,  # Increased for better quality
    "image_spacing": 100,
    "layout": "horizontal",
    "max_frames": 0,  # 0 = unlimited, process entire video from start to finish
    "fps": 5,  # Increased from 3 for better transition detection accuracy (200ms frame spacing)
    "diff_thresh": 0.20,  # More sensitive for better transition detection
    "transition_delay": 1.0  # Delay in seconds after detecting a change before capturing screenshot
}

def configure_settings_tool(image_width: int = None, image_spacing: int = None, 
                          layout: str = None, max_frames: int = None, 
                          fps: int = None, diff_thresh: float = None, 
                          transition_delay: float = None) -> str:
    """
    Configure processing settings for video analysis and Miro upload.
    
    This tool lets you customize how videos are processed and how images are arranged.
    All settings are saved for the current session and apply to future operations.
    
    Args:
        image_width (int, optional): Width to resize extracted images to in pixels.
                                     Default: 600. Higher = larger images, more detail.
        image_spacing (int, optional): Gap between images on Miro board in pixels.
                                        Default: 100. Higher = more space between images.
        layout (str, optional): How to arrange images on Miro board.
                                 Options: "horizontal" (side-by-side) or "vertical" (top-to-bottom).
                                 Default: "horizontal".
        max_frames (int, optional): Maximum keyframes to extract per video.
                                     Default: 0 (unlimited - processes entire video).
                                     Set to a specific number to limit frames.
        fps (int, optional): Video sampling rate for change detection.
                              Default: 5. Higher = more frames analyzed, better accuracy, slower processing.
                              At 5 fps, frames are spaced ~200ms apart, providing good granularity
                              for detecting when 1-second transitions complete.
        diff_thresh (float, optional): Sensitivity for detecting screen changes (0.0 to 1.0).
                                         Default: 0.20. Lower = more sensitive, more keyframes.
        transition_delay (float, optional): Delay in seconds after detecting a screen change 
                                             before capturing screenshot. Default: 1.0.
                                             Allows screen transitions to complete before capture.
                                             Higher = safer but may miss fast actions.
    
    Returns:
        str: Confirmation of updated settings or current settings if no changes
    
    Examples:
        - configure_settings_tool(image_width=600)  # Make images bigger
        - configure_settings_tool(image_spacing=200, layout="vertical")  # More space, vertical layout
        - configure_settings_tool(diff_thresh=0.25, max_frames=20)  # More sensitive, more frames
    """
    try:
        changes = []
        
        if image_width is not None:
            session_state["image_width"] = image_width
            changes.append(f"Image width: {image_width}px")
        
        if image_spacing is not None:
            session_state["image_spacing"] = image_spacing
            changes.append(f"Image spacing: {image_spacing}px")
        
        if layout is not None and layout in ["horizontal", "vertical"]:
            session_state["layout"] = layout
            changes.append(f"Layout: {layout}")
        
        if max_frames is not None:
            session_state["max_frames"] = max_frames
            changes.append(f"Max frames: {max_frames}")
        
        if fps is not None:
            session_state["fps"] = fps
            changes.append(f"FPS: {fps}")
        
        if diff_thresh is not None:
            session_state["diff_thresh"] = diff_thresh
            changes.append(f"Change threshold: {diff_thresh}")
        
        if transition_delay is not None:
            session_state["transition_delay"] = transition_delay
            changes.append(f"Transition delay: {transition_delay}s")
        
        if changes:
            return f"✅ Settings updated:\n" + "\n".join(f"  • {change}" for change in changes)
        else:
            return "📊 Current settings:\n" + "\n".join(f"  • {k}: {v}" for k, v in session_state.items() if k != "current_apps")
        
    except Exception as e:
        return f"❌ Error updating settings: {str(e)}"

def get_processing_status_tool() -> str:
    """
    Get current processing status and session information.
    
    This tool shows you the current state of your session including:
    - Which apps have been processed
    - Current settings and their values
    - How many images are available for each app
    
    Returns:
        str: Formatted status report with session details and settings
    
    Examples:
        - get_processing_status_tool()  # Show current status
    """
    try:
        output_dir = session_state["output_dir"]
        
        status = "📊 Current Status:\n\n"
        status += f"📱 Apps in session: {', '.join(session_state['current_apps']) if session_state['current_apps'] else 'None'}\n"
        status += f"📁 Output directory: {output_dir}\n"
        status += f"⚙️ Settings:\n"
        for key, value in session_state.items():
            if key != "current_apps":
                status += f"  • {key}: {value}\n"
        
        # Check for existing images
        if session_state["current_apps"]:
            status += "\n📸 Available images:\n"
            for app in session_state["current_apps"]:
                app_dir = output_dir / app
                if app_dir.exists():
                    image_count = len(list(app_dir.glob("*.jpg")))
                    status += f"  • {app}: {image_count} images\n"
                else:
                    status += f"  • {app}: No images\n"
        
        return status
        
    except Exception as e:
        return f"❌ Error getting status: {str(e)}"

def get_available_settings_tool() -> str:
    """
    Display all configurable parameters and their current values.
    
    This tool provides a comprehensive reference of all settings you can control,
    their current values, valid ranges, and examples of how to change them.
    
    Returns:
        str: Formatted guide showing all available settings and how to configure them
    
    Examples:
        - get_available_settings_tool()  # Show settings reference
    """
    try:
        settings_guide = """📋 Available Settings Reference:

🔧 PROCESSING SETTINGS:
• image_width: Output image width in pixels
  Current: {image_width}px | Range: 100-2000 | Example: configure_settings_tool(image_width=600)

• max_frames: Maximum keyframes to extract per video
  Current: {max_frames} (0=unlimited, processes entire video) | Example: configure_settings_tool(max_frames=20)

• fps: Video sampling rate for change detection
  Current: {fps} | Range: 1-10 | Example: configure_settings_tool(fps=5)
  Note: Higher values = better accuracy for transition detection, slightly slower processing

• diff_thresh: Change detection sensitivity (0-1)
  Current: {diff_thresh} | Range: 0.1-0.9 | Example: configure_settings_tool(diff_thresh=0.20)
  Note: Lower values = more sensitive = more keyframes

• transition_delay: Delay after detecting change before capturing screenshot
  Current: {transition_delay}s | Range: 0.5-3.0 | Example: configure_settings_tool(transition_delay=1.5)
  Note: Ensures screenshots are taken after screen transitions complete, not during animations.
       Frame spacing is now handled automatically by this parameter, no separate stride needed.

🎨 LAYOUT SETTINGS:
• image_spacing: Gap between images on Miro board
  Current: {image_spacing}px | Range: 0-500 | Example: configure_settings_tool(image_spacing=200)

• layout: How to arrange images
  Current: {layout} | Options: "horizontal", "vertical" | Example: configure_settings_tool(layout="vertical")

💡 COMMON CONFIGURATIONS:
• "I want bigger images" → configure_settings_tool(image_width=600)
• "300px gap between images" → configure_settings_tool(image_spacing=300)
• "More sensitive detection" → configure_settings_tool(diff_thresh=0.20)
• "Vertical layout" → configure_settings_tool(layout="vertical")
• "Extract 20 frames" → configure_settings_tool(max_frames=20)

🔄 TO RESET ALL SETTINGS:
• clear_session_tool()""".format(
            image_width=session_state["image_width"],
            max_frames=session_state["max_frames"],
            fps=session_state["fps"],
            diff_thresh=session_state["diff_thresh"],
            transition_delay=session_state["transition_delay"],
            image_spacing=session_state["image_spacing"],
            layout=session_state["layout"]
        )
        
        return settings_guide
        
    except Exception as e:
        return f"❌ Error getting settings reference: {str(e)}"

def clear_session_tool() -> str:
    """
    Clear current session and reset settings to defaults.
    
    This tool resets your session by:
    - Clearing the list of processed apps
    - Resetting all settings to their default values
    - Note: This does NOT delete local image files
    
    Returns:
        str: Confirmation that session has been cleared
    
    Examples:
        - clear_session_tool()  # Reset everything
    """
    try:
        session_state["current_apps"] = []
        return "✅ Session cleared! All apps and settings reset to defaults."
    except Exception as e:
        return f"❌ Error clearing session: {str(e)}"
