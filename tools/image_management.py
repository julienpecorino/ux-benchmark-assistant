#!/usr/bin/env python3
"""
Image management and local file handling tools
"""

from pathlib import Path
from .configuration import session_state

def list_local_images_tool(app_name: str = None) -> str:
    """
    List all locally saved images for review.
    
    This tool shows you what images have been extracted and saved locally,
    so you can review them before uploading to Miro.
    
    Args:
        app_name (str, optional): Specific app to list images for. 
                                  If None, lists images for all apps in current session.
                                  Examples: "Willow", "MyApp", None for all apps
    
    Returns:
        str: Formatted list of images with file sizes and timestamps
    
    Examples:
        - list_local_images_tool()  # List all apps
        - list_local_images_tool("Willow")  # List only Willow app images
    """
    try:
        output_dir = session_state["output_dir"]
        
        if app_name:
            apps_to_check = [app_name]
        else:
            apps_to_check = session_state["current_apps"] if session_state["current_apps"] else [d.name for d in output_dir.iterdir() if d.is_dir()]
        
        if not apps_to_check:
            return "📁 No images found. Process a video first!"
        
        result = "📁 Local Images Available:\n\n"
        
        for app in apps_to_check:
            app_dir = output_dir / app
            if not app_dir.exists():
                continue
                
            image_files = list(app_dir.glob("*.jpg"))
            if not image_files:
                continue
                
            result += f"📱 {app}:\n"
            for img_file in sorted(image_files, key=lambda x: x.stat().st_mtime, reverse=True):
                size_mb = img_file.stat().st_size / (1024 * 1024)
                result += f"  • {img_file.name} ({size_mb:.1f}MB)\n"
            result += "\n"
        
        return result
        
    except Exception as e:
        return f"❌ Error listing images: {str(e)}"

def import_manual_screenshots_tool(app_name: str) -> str:
    """
    Import manually added screenshots from the screenshots folder.
    
    This tool registers screenshots that you've manually placed in the 
    screenshots folder, so they can be uploaded to Miro.
    
    Workflow:
    1. Create a folder: screenshots/YourAppName/
    2. Add your screenshot images (.jpg, .jpeg, .png) to that folder
    3. Call this tool to register them: import_manual_screenshots_tool("YourAppName")
    4. Upload to Miro: upload_images_tool("YourAppName")
    
    Args:
        app_name (str): Name of the app folder in screenshots/ directory
    
    Returns:
        str: Summary of found images and next steps
    
    Examples:
        - import_manual_screenshots_tool("iOS App")
        - import_manual_screenshots_tool("Design Mockups")
    """
    try:
        output_dir = session_state["output_dir"]
        app_dir = output_dir / app_name
        
        if not app_dir.exists():
            return f"❌ Folder not found: {app_dir}\n\n💡 To import manual screenshots:\n1. Create folder: screenshots/{app_name}/\n2. Add your images (.jpg, .jpeg, .png) to the folder\n3. Run this tool again"
        
        # Find all image files
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
            image_files.extend(list(app_dir.glob(ext)))
        
        if not image_files:
            return f"❌ No images found in {app_dir}\n\n💡 Add .jpg, .jpeg, or .png files to the folder and try again"
        
        # Register app in session
        if app_name not in session_state["current_apps"]:
            session_state["current_apps"].append(app_name)
        
        # Summary
        total_size = sum(f.stat().st_size for f in image_files)
        size_mb = total_size / (1024 * 1024)
        
        return f"""✅ Imported {len(image_files)} manual screenshots for '{app_name}'
        
📁 Location: {app_dir}
📊 Total size: {size_mb:.1f} MB
📸 Images found: {', '.join([f.name for f in image_files[:5]])}{'...' if len(image_files) > 5 else ''}

🎯 Next steps:
1. Review images in the folder (add/remove as needed)
2. When ready, upload to Miro: upload_images_tool("{app_name}")
3. Configure spacing if needed: configure_settings_tool(image_spacing=150)

💡 Current upload settings: {session_state['image_spacing']}px spacing in {session_state['layout']} layout"""
        
    except Exception as e:
        return f"❌ Error importing screenshots: {str(e)}"
