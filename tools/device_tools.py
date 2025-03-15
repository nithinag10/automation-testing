#!/usr/bin/env python3
"""
Device Tools Module

This module provides tools for interacting with the Android device,
including clicking, performing gestures, and pressing system keys.
"""

import os
from langchain_core.tools import tool

# Import from core modules
from core.device_actions import DeviceActions
from core.grid_overlay import GridOverlay
from core.logger import log_activity

# Initialize device
device = DeviceActions()
grid_overlay = GridOverlay()

@tool
def click_grid(grid_number: int) -> str:
    """Perform a click action at the center of the specified grid cell.
    
    Args:
        grid_number (int): The grid cell number (starting from 1) where the click should occur.
    
    Returns:
        str: Success message with grid number and corresponding screen coordinates,
             or error message if the click failed.
    """
    print(f"\n=== Clicking at grid {grid_number} ===")
    print(f"Screen bounds: 1080x2400")  # Known device resolution
    
    # Convert grid number to screen coordinates
    try:
        x, y = grid_overlay.get_coordinates_for_grid(grid_number)
    except ValueError as e:
        error_msg = f"Invalid grid number: {str(e)}"
        print(f"Error: {error_msg}")
        return error_msg
    
    print(f"Converted grid {grid_number} to screen coordinates ({x}, {y})")
    print("Executing device.click() method...")
    # Use the device's click method directly
    success = device.click(x, y)
    
    if success:
        print("Click action successful")
        return f"Clicked at grid {grid_number} which corresponds to screen coordinates ({x}, {y})."
    else:
        error_msg = f"Failed to click at grid {grid_number}."
        print(f"Error: {error_msg}")
        return error_msg

@tool
def perform_gesture(gesture_type: str) -> str:
    """
    Perform a navigation gesture on the device screen.
    
    Args:
        gesture_type (str): The type of gesture to perform. 
                           Valid options: "scroll_up", "swipe_left", "swipe_right"
    
    Returns:
        str: Success or failure message
    """
    print(f"\n=== Performing Gesture: {gesture_type} ===")
    
    try:
        if gesture_type == "scroll_up":
            if device.scroll_up():
                return "Successfully scrolled up"
            return "Failed to scroll up"
            
        elif gesture_type == "swipe_left":
            if device.swipe_left():
                return "Successfully swiped left"
            return "Failed to swipe left"
            
        elif gesture_type == "swipe_right":
            if device.swipe_right():
                return "Successfully swiped right"
            return "Failed to swipe right"
            
        else:
            error_msg = f"Unknown gesture type: {gesture_type}. Valid options: scroll_up, swipe_left, swipe_right"
            print(f"Error: {error_msg}")
            return error_msg
            
    except Exception as e:
        error_msg = f"Error performing gesture {gesture_type}: {str(e)}"
        print(f"Exception: {error_msg}")
        return error_msg

@tool
def press_system_key(key_name: str) -> str:
    """
    Press a system key on the device.
    
    Args:
        key_name (str): Name of the key to press.
                      Valid options: "home", "back", "enter", "volume_up", "volume_down", "power"
    
    Returns:
        str: Success or failure message
    """
    print(f"\n=== Pressing System Key: {key_name} ===")
    
    key_codes = {
        "home": 3,
        "back": 4,
        "enter": 66,
        "volume_up": 24,
        "volume_down": 25,
        "power": 26
    }
    
    if key_name not in key_codes:
        valid_keys = ", ".join(key_codes.keys())
        error_msg = f"Invalid key name: {key_name}. Valid options: {valid_keys}"
        print(f"Error: {error_msg}")
        return error_msg
    
    key_code = key_codes[key_name]
    success = device.press_key(key_code)
    
    if success:
        result_msg = f"Successfully pressed {key_name} key"
        print(result_msg)
        return result_msg
    else:
        error_msg = f"Failed to press {key_name} key"
        print(f"Error: {error_msg}")
        return error_msg
