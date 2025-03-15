#!/usr/bin/env python3
"""
Helpers Module

This module provides utility functions used across the Android automation system.
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

def timestamp() -> str:
    """
    Get a formatted timestamp string.
    
    Returns:
        str: Formatted timestamp (YYYYMMDD_HHMMSS)
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def ensure_directory(path: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path (str): Directory path to ensure exists
        
    Returns:
        bool: True if directory exists or was created, False on error
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error ensuring directory {path}: {str(e)}")
        return False

def save_json(data: Dict[str, Any], filepath: str, indent: int = 2) -> bool:
    """
    Save data as JSON to a file.
    
    Args:
        data (dict): Data to save
        filepath (str): Path to save the file
        indent (int): Indentation level for the JSON
        
    Returns:
        bool: True if save was successful, False on error
    """
    try:
        # Ensure the directory exists
        directory = os.path.dirname(filepath)
        ensure_directory(directory)
        
        # Write the file
        with open(filepath, "w") as f:
            json.dump(data, f, indent=indent, default=lambda o: o.__dict__)
        return True
    except Exception as e:
        print(f"Error saving JSON to {filepath}: {str(e)}")
        return False

def load_json(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Load JSON data from a file.
    
    Args:
        filepath (str): Path to the JSON file
        
    Returns:
        dict or None: Loaded JSON data, or None if loading failed
    """
    try:
        if not os.path.exists(filepath):
            return None
            
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON from {filepath}: {str(e)}")
        return None

def wait_for(seconds: float) -> None:
    """
    Wait for the specified number of seconds.
    
    Args:
        seconds (float): Number of seconds to wait
    """
    time.sleep(seconds)

def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds as a human-readable string.
    
    Args:
        seconds (float): Duration in seconds
        
    Returns:
        str: Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"

def truncate_string(text: str, max_length: int = 100) -> str:
    """
    Truncate a string to a maximum length.
    
    Args:
        text (str): String to truncate
        max_length (int): Maximum length
        
    Returns:
        str: Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."
