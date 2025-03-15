#!/usr/bin/env python3
"""
Input Tools Module

This module provides tools for inputting text on the Android device.
"""

from langchain_core.tools import tool

# Import from core modules
from core.device_actions import DeviceActions
from core.logger import log_activity

# Initialize device
device = DeviceActions()

@tool
def input_text(text: str) -> str:
    """
    Input text on the device.
    
    This tool allows inputting text into the currently focused text field on the device.
    
    Args:
        text (str): The text to input
    
    Returns:
        str: Success or failure message
    """
    print(f"\n=== Inputting Text: {text} ===")
    
    try:
        success = device.input_text(text)
        
        if success:
            result_msg = f"Successfully input text: '{text}'"
            print(result_msg)
            return result_msg
        else:
            error_msg = "Failed to input text"
            print(f"Error: {error_msg}")
            return error_msg
            
    except Exception as e:
        error_msg = f"Error inputting text: {str(e)}"
        print(f"Exception: {error_msg}")
        return error_msg
