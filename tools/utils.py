#!/usr/bin/env python3
"""
Shared utilities and constants for benchmark tools
"""

import os
import cv2
import numpy as np
from PIL import Image
import requests
import json
from pathlib import Path
from urllib.parse import quote
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Miro API configuration
MIRO_TOKEN = os.getenv("MIRO_TOKEN", "").strip()
MIRO_BOARD_ID = os.getenv("MIRO_BOARD_ID", "").strip()  # This will be updated dynamically
MIRO_API = "https://api.miro.com/v2"

def hsv_hist(bgr: np.ndarray) -> np.ndarray:
    """Calculate HSV histogram for change detection"""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0,1], None, [50,60], [0,180,0,256])
    cv2.normalize(hist, hist)
    return hist

def hist_distance(h1: np.ndarray, h2: np.ndarray) -> float:
    """Calculate histogram distance for change detection"""
    return float(cv2.compareHist(h1, h2, cv2.HISTCMP_BHATTACHARYYA))

def bgr_to_pil(bgr: np.ndarray) -> Image.Image:
    """Convert OpenCV BGR to PIL RGB"""
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)

def resize_keep_width(img: Image.Image, target_w: int) -> Image.Image:
    """Resize image keeping aspect ratio"""
    if target_w <= 0:
        return img
    w, h = img.size
    if w <= target_w:
        return img
    new_h = int(round(h * (target_w / float(w))))
    return img.resize((target_w, new_h), Image.LANCZOS)

def handle_miro_api_error(e: requests.exceptions.RequestException) -> str:
    """Centralized Miro API error handling"""
    if e.response and e.response.status_code == 401:
        return "❌ Invalid Miro token. Please check your MIRO_TOKEN in the .env file."
    elif e.response and e.response.status_code == 403:
        return "❌ Access denied. Your Miro token doesn't have the required permissions."
    elif e.response and e.response.status_code == 404:
        return "❌ Resource not found. The board or item doesn't exist or you don't have access to it."
    elif e.response and e.response.status_code == 429:
        return "❌ Rate limit exceeded. Please wait a moment and try again."
    else:
        return f"❌ Miro API error: {str(e)}"

def create_image_on_miro(board_id: str, image_path: Path, x: float, y: float, frame_id: str = None) -> dict:
    """Create image on Miro board via direct file upload, optionally inside a frame"""
    encoded_board_id = quote(board_id, safe='')
    url = f"{MIRO_API}/boards/{encoded_board_id}/images"
    
    headers = {
        "Authorization": f"Bearer {MIRO_TOKEN}",
        "accept": "application/json"
    }
    
    # Prepare position data
    # Solution #1: Use absolute board coordinates, don't use parent field
    # This positions images at the frame's location without trying to make them children of the frame
    # The frame_id is passed for reference but we don't use it in the API call
    position_data = {"position": {"x": x, "y": y}}
    
    # NOTE: Not using parent field - it causes "outside of parent boundaries" errors
    # Instead, we calculate absolute board coordinates that match the frame's position
    
    position_json = json.dumps(position_data)
    
    with open(image_path, 'rb') as img_file:
        files = {
            'data': (None, position_json, 'application/json'),
            'resource': (image_path.name, img_file, 'image/jpeg')
        }
        response = requests.post(url, headers=headers, files=files, timeout=60)
    
    # Enhanced error handling to show Miro's error details
    if not response.ok:
        try:
            error_details = response.json()
            error_msg = error_details.get('message', response.text)
            raise requests.exceptions.HTTPError(
                f"{response.status_code} {response.reason}: {error_msg}\nPayload: {position_json}"
            )
        except json.JSONDecodeError:
            response.raise_for_status()
    
    return response.json()
