#!/usr/bin/env python3
"""
Screen Tools Module

This module provides tools for capturing and analyzing device screens.
"""

import os
import json
from datetime import datetime
from langchain_core.tools import tool

# Import from core modules
from core.device_actions import DeviceActions
from core.screenshot_analyzer import ScreenshotAnalyzer
from core.grid_overlay import GridOverlay
from core.logger import log_activity

# Initialize required components
device = DeviceActions()
screenshot_analyzer = ScreenshotAnalyzer()
grid_overlay = GridOverlay()

@tool
def get_screen_data() -> str:
    """
    Capture the current screen, analyze it using Gemini Vision, and apply grid overlay.
    
    This tool takes a screenshot of the current screen, applies a numbered grid overlay,
    and uses Gemini Vision to extract text and analyze UI elements.
    
    Returns:
        str: JSON string containing screen analysis including text content, UI elements, 
             and grid information
    """
    print("\n=== Capturing and Analyzing Screen ===")
    
    # Create timestamped output directories if they don't exist
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"results/screen_capture_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Capture screenshot
    screenshot_path = os.path.join(output_dir, "screenshot.png")
    print(f"Taking screenshot: {screenshot_path}")
    screenshot_result = device.take_screenshot(screenshot_path)
    
    if not screenshot_result:
        error_msg = "Failed to capture screenshot"
        print(f"Error: {error_msg}")
        return json.dumps({"error": error_msg})
    
    # Apply grid overlay
    grid_overlay_path = os.path.join(output_dir, "screenshot_with_grid.png")
    print(f"Applying grid overlay: {grid_overlay_path}")
    grid_overlay.apply_grid_to_image(screenshot_path, grid_overlay_path)
    
    # Use screenshot analyzer to extract text
    print("Analyzing screenshot with Gemini Vision...")
    text_result = screenshot_analyzer.extract_text(screenshot_path)
    
    # Analyze UI elements
    print("Analyzing UI elements...")
    ui_elements = screenshot_analyzer.analyze_ui_elements(screenshot_path)
    
    # Compose response
    result = {
        "timestamp": timestamp,
        "screenshot_path": screenshot_path,
        "grid_overlay_path": grid_overlay_path,
        "text_content": text_result,
        "ui_elements": ui_elements
    }
    
    print("Screen analysis complete")
    return json.dumps(result, indent=2)

@tool
def get_grid_info() -> str:
    """
    Get information about the grid overlay system.
    
    Returns information about the grid system used for touch interaction,
    including grid dimensions and how to reference grid cells.
    
    Returns:
        str: JSON string with grid information
    """
    print("\n=== Getting Grid Information ===")
    
    grid_info = {
        "grid_size": grid_overlay.grid_size,
        "grid_dimensions": f"{grid_overlay.columns}x{grid_overlay.rows}",
        "total_cells": grid_overlay.columns * grid_overlay.rows,
        "cell_width": grid_overlay.cell_width,
        "cell_height": grid_overlay.cell_height,
        "usage": "Grid cells are numbered starting from the top-left (1) to the bottom-right. "
                "Use these numbers with the click_grid tool to interact with specific areas."
    }
    
    print(f"Grid dimensions: {grid_info['grid_dimensions']}")
    print(f"Total cells: {grid_info['total_cells']}")
    
    return json.dumps(grid_info, indent=2)
