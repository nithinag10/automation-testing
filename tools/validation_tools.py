#!/usr/bin/env python3
"""
Validation Tools Module

This module provides tools for validating screen states and actions.
"""

import json
from typing import Dict, Any
from langchain_core.tools import tool

# Import from core modules
from core.device_actions import DeviceActions
from core.screenshot_analyzer import ScreenshotAnalyzer
from core.logger import log_activity

# Initialize components
device = DeviceActions()
screenshot_analyzer = ScreenshotAnalyzer(device)

@tool
def match_screen_with_description(expected_screen_description: str) -> str:
    """
    Validate whether the current screen matches an expected description.
    
    This tool takes a screenshot, analyzes it using Gemini Vision, and 
    determines if it matches the provided description.
    
    Args:
        expected_screen_description (str): Description of the expected screen state
    
    Returns:
        str: JSON string indicating whether the screen matches and confidence level
    """
    print(f"\n=== Validating Screen Against Description ===")
    print(f"Expected: {expected_screen_description}")
    
    # Capture the current screen
    screenshot_path = "results/validation_screenshot.png"
    device.take_screenshot(screenshot_path)
    
    # Extract text and analyze UI
    screen_text = screenshot_analyzer.extract_text(screenshot_path)
    ui_elements = screenshot_analyzer.analyze_ui_elements(screenshot_path)
    
    # Build a description of the current screen
    current_screen = {
        "text_content": screen_text,
        "ui_elements": ui_elements
    }
    
    # Use Gemini to compare the current screen with the expected description
    comparison_result = screenshot_analyzer.compare_screen_with_description(
        screenshot_path, 
        expected_screen_description,
        screen_text,
        json.dumps(ui_elements)
    )
    
    # Format result
    result = {
        "matches": comparison_result["matches"],
        "confidence": comparison_result["confidence"],
        "explanation": comparison_result["explanation"],
        "current_screen_details": {
            "text_content": screen_text
        }
    }
    
    print(f"Validation result: {'Match' if result['matches'] else 'No match'}")
    print(f"Confidence: {result['confidence']}")
    
    return json.dumps(result, indent=2)
    
@tool
def verify_element_exists(element_description: str) -> str:
    """
    Verify if a specific UI element exists on the current screen.
    
    Args:
        element_description (str): Description of the UI element to look for
    
    Returns:
        str: JSON string indicating whether the element exists and its location
    """
    print(f"\n=== Verifying Element Exists: {element_description} ===")
    
    # Capture the current screen
    screenshot_path = "results/element_verification.png"
    device.take_screenshot(screenshot_path)
    
    # Use Gemini to find the element
    element_result = screenshot_analyzer.find_element(screenshot_path, element_description)
    
    if element_result["found"]:
        result = {
            "element_found": True,
            "element_description": element_description,
            "location": element_result["location"],
            "grid_position": element_result["grid_position"] if "grid_position" in element_result else None,
            "confidence": element_result["confidence"]
        }
        print(f"Element found: {element_description}")
        print(f"Location: {element_result['location']}")
    else:
        result = {
            "element_found": False,
            "element_description": element_description,
            "reason": element_result["reason"] if "reason" in element_result else "Element not found on screen"
        }
        print(f"Element not found: {element_description}")
    
    return json.dumps(result, indent=2)
