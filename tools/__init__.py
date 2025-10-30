#!/usr/bin/env python3
"""
Benchmark Tools - Modular tool collection for UX video analysis and Miro integration
"""

# Video processing tools
from .video_processing import process_video_tool

# Image management tools
from .image_management import (
    list_local_images_tool,
    import_manual_screenshots_tool
)

# Miro integration tools
from .miro_integration import upload_images_tool, upload_all_images_tool, list_miro_boards_tool, set_miro_board_tool, list_miro_frames_tool

# Configuration and session management tools
from .configuration import (
    configure_settings_tool,
    get_processing_status_tool,
    get_available_settings_tool,
    clear_session_tool
)

# Terminal animations
from .animations import typing

# Export all tools for easy importing
__all__ = [
    # Video processing
    'process_video_tool',
    
    # Image management
    'list_local_images_tool',
    'import_manual_screenshots_tool',
    
    # Miro integration
    'upload_images_tool',
    'upload_all_images_tool',
    'list_miro_boards_tool',
    'set_miro_board_tool',
    'list_miro_frames_tool',
    
    # Configuration
    'configure_settings_tool',
    'get_processing_status_tool',
    'get_available_settings_tool',
    'clear_session_tool',
    
    # Animations
    'typing'
]
