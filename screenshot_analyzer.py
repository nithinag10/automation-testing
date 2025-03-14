#!/usr/bin/env python3
"""
Screenshot Analyzer Module

This module captures screenshots from Android emulators, applies a grid overlay,
and uses Gemini 2.0 Flash to extract text from the images.
"""

import os
import json
from typing import Literal, List, Dict, Union, Optional
from datetime import datetime
from typing_extensions import TypedDict, Annotated
from PIL import Image

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

from device_actions import DeviceActions
from grid_overlay import GridOverlay

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Environment variables loaded from .env file")
except ImportError:
    print("Warning: python-dotenv not available. Environment variables must be set manually.")

# Try to import Google Generative AI SDK
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    print("Warning: Google Generative AI SDK not available. Text extraction will be disabled.")
    GENAI_AVAILABLE = False

# Try to import UI Automator for device control
try:
    import uiautomator2 as u2
    UI_AUTOMATOR_AVAILABLE = True
except ImportError:
    print("Warning: uiautomator2 not available. Device interactions will be disabled.")
    UI_AUTOMATOR_AVAILABLE = False

class ScreenshotAnalyzer:
    """
    A class that combines functionality for capturing screenshots from Android emulators,
    adding a grid overlay, and extracting text using Gemini 2.0 Flash multimodal model.
    """
    
    def __init__(self, device_serial=None):
        """xw
        Initialize the ScreenshotAnalyzer.
        
        Args:
            device_serial (str, optional): Device serial number for ADB. Default is None.
            finger_touch_size_mm (int): Average finger touch size in millimeters. Default is 7mm.
            ppi (int): Pixels per inch of the target device. Default is 405 PPI.
            screen_resolution (tuple): Screen resolution as (width, height) in pixels.
                                      Default is (1080, 2400).
        """
        # Set up UI Automator connection (if available)
        self.device = None
        self.device_serial = device_serial
        self.device_actions = DeviceActions()
        
        if UI_AUTOMATOR_AVAILABLE:
            try:
                self.device = u2.connect(device_serial)
                self.device_serial = device_serial if device_serial else self.device.serial
                print(f"Connected to device: {self.device.info.get('productName', 'Unknown')}")
            except Exception as e:
                print(f"Warning: Failed to connect to device: {str(e)}")
        
        # Set up grid overlay
        self.grid_overlay = GridOverlay()
        
        # Set up Gemini API
        self.genai_client = None
        if GENAI_AVAILABLE:
            self._setup_genai()
        
    def _setup_genai(self):
        """Set up Google Generative AI client."""
        if not GENAI_AVAILABLE:
            return
            
        try:
            # Initialize the Gemini client with API key from environment
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                print("Warning: GEMINI_API_KEY environment variable not found.")
                self.genai_client = None
                return
                
            self.genai_client = genai.Client(api_key=api_key)
            print("Google Generative AI client initialized.")
                
        except Exception as e:
            print(f"Error setting up Google Generative AI: {str(e)}")
            self.genai_client = None
            
    def take_screenshot(self):
        """
        Take a screenshot using UIAutomator2. Always save with file in this formate : screenshot.png
        
        Args:
            output_path (str, optional): Path to save the screenshot.
                If not provided, a timestamp-based filename will be used.
                Always save with .png format
                don't store it in a directoy
                
        Returns:
            str: Path to the saved screenshot, or None if failed.
        """
        if not UI_AUTOMATOR_AVAILABLE or not self.device:
            print("UI Automator not available. Cannot take screenshot.")
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"screenshot_{timestamp}.png"
            
        try:
            # Take screenshot using UIAutomator2
            self.device_actions.take_screenshot(output_path)
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"Screenshot saved to {output_path}")
                return output_path
            else:
                print("Screenshot file is empty or not created")
                return None
                
        except Exception as e:
            print(f"Error taking screenshot: {str(e)}")
            return None
            
    def apply_grid_to_screenshot(self, screenshot_path, output_path=None):
        """
        Apply grid overlay to a screenshot
        
        Args:
            screenshot_path (str): Path to the input screenshot.
            output_path (str, optional): Path to save the output image.
                If not provided, will save with '_grid' suffix.
                
        Returns:
            str: Path to the saved output image with grid overlay.
        """
        return self.grid_overlay.apply_grid_to_image(screenshot_path, output_path)
        
    def extract_text_with_gemini(self, image_path):
        """
        Extract text from image using Gemini 2.0 Flash multimodal model.
        
        Args:
            image_path (str): Path to the image file.
            
        Returns:
            str: Extracted text from the image.
        """
        if not GENAI_AVAILABLE:
            print("Google Generative AI SDK not available (import failed).")
            return ""
            
        if not self.genai_client:
            print("Google Generative AI client not initialized.")
            return ""
            
        try:
            # Open image with PIL
            img = Image.open(image_path)
            
            # Generate content with Gemini 2.0 Flash
            response = self.genai_client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[
                    """
                Role:
                You are an expert screen reader specializing in translating mobile phone screenshots into highly detailed text descriptions for blind users. Your primary skill is accurately identifying and explaining all visible elements while associating them with the correct grid number to help users navigate the screen effectively.

                Task:
                Given a mobile phone screenshot that includes grid numbers, your job is to extract and describe every visible detail on the screen. Each element must be paired with its corresponding grid number so that blind users can precisely identify its location.

                What Are grid numbers?
                Its already present on the screenshot.
                Each grid number represents a specific area of the screen where users can interact.

                Requirements:
                Explain everything on the screen, including text, buttons, icons, images, and any minor details, no matter how small.
                After each explanation, tell the grid number that is right on the element you are referring (can be icon, text, button, image, etc) as close as possible and that is visible on the screenshot in those small grids that you are referring to.
                Ensure clarity and organization to maximize usability.
                Use a structured format to make it easy for blind users to understand and navigate the screen.
                Also clearly expalin the bottom navigation buttons, recent tabs, home button and back button. 

""",
                    img
                ]
            )
            
            # Get the extracted text
            extracted_text = response.text.strip()
            print("Pritning extarcted text", extracted_text)
            return extracted_text
                
        except Exception as e:
            print(f"Error calling Gemini API: {str(e)}")
            return ""
            
    def capture_analyze_with_grid(self):
        """
        Capture screenshot, apply grid overlay, and extract text using Gemini.
        
        Returns:
            dict: Result containing paths and extracted text.
        """
        result = {
            "screenshot_path": None,
            "grid_screenshot_path": None,
            "extracted_text": None
        }
        
        # Step 1: Take screenshot
        screenshot_path = self.take_screenshot()
        if not screenshot_path:
            return result
        result["screenshot_path"] = screenshot_path
        
        # Step 2: Apply grid overlay
        grid_path = self.apply_grid_to_screenshot(screenshot_path)
        result["grid_screenshot_path"] = grid_path
        
        # Step 3: Extract text with Gemini
        if GENAI_AVAILABLE and self.genai_client:
            extracted_text = self.extract_text_with_gemini(grid_path)
            result["extracted_text"] = extracted_text
            
        return result
        
    def get_grid_coordinates(self, grid_number):
        """
        Get screen coordinates for a specific grid number.
        
        Args:
            grid_number (int): The grid cell number.
            
        Returns:
            tuple: (x, y) coordinates corresponding to the grid number.
        """
        return self.grid_overlay.get_coordinates_for_grid(grid_number)
        
    def tap_on_grid(self, grid_number):
        """
        Tap on the coordinates corresponding to a grid number.
        
        Args:
            grid_number (int): The grid cell number to tap on.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if not UI_AUTOMATOR_AVAILABLE or not self.device:
            print("UI Automator not available. Cannot tap on screen.")
            return False
            
        try:
            x, y = self.get_grid_coordinates(grid_number)
            self.device.click(x, y)
            print(f"Tapped on grid #{grid_number} at coordinates: ({x}, {y})")
            return True
        except Exception as e:
            print(f"Error tapping on grid #{grid_number}: {str(e)}")
            return False
            
    def verify_screen_content(self, image_path, verification_items):
        """
        Verify if specific items/elements are present on the screen.
        
        Args:
            image_path (str): Path to the screenshot image to verify
            verification_items (list): List of items/elements to verify on the screen
                Each item should be a string describing what to look for
                
        Returns:
            dict: Dictionary with verification results
                {
                    "verified": bool - Overall verification result (True if all items found),
                    "items": [
                        {
                            "item": str - The item that was checked,
                            "found": bool - Whether the item was found,
                            "confidence": float - Confidence score (0-1),
                            "location": str - Grid location if found (or None),
                            "details": str - Additional details about the item
                        }
                    ],
                    "screenshot_analysis": str - Full text analysis of the screenshot
                }
        """
        if not GENAI_AVAILABLE:
            print("Google Generative AI SDK not available (import failed).")
            return {"verified": False, "items": [], "error": "Gemini API not available"}
            
        if not self.genai_client:
            print("Google Generative AI client not initialized.")
            return {"verified": False, "items": [], "error": "Gemini client not initialized"}
            
        try:
            # Open image with PIL
            img = Image.open(image_path)
            
            # Create a prompt that asks for verification of specific elements
            verification_prompt = f"""
            Role:
            You are a specialized mobile screen verification agent. Your task is to analyze a screenshot and verify if specific elements are present on the screen.
            
            Task:
            Given the following list of items to verify, carefully analyze the screenshot and determine if each item is present. For each item, provide:
            1. Whether the item is found (yes/no)
            2. A confidence score between 0 and 1
            4. Any additional details that might be helpful for verification
            
            Items to verify:
            {', '.join(verification_items)}
            
            Format your response as a structured verification report with one section per item.
            """
            
            # Generate content with Gemini 2.0 Flash
            response = self.genai_client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[verification_prompt, img]
            )
            
            # Get the analysis text
            analysis_text = response.text.strip()
            
            # First, get a standard screen description for context
            screen_description = self.extract_text_with_gemini(image_path)
            
            # Parse the verification results
            verification_results = {
                "verified": True,  # Will be set to False if any item is not found
                "items": [],
                "screenshot_analysis": screen_description
            }
            
            # Process each verification item
            for item in verification_items:
                # Very simple parsing - in a real implementation, this would be more sophisticated
                # and would properly parse the structured response from the model
                found = "not found" not in analysis_text.lower() and item.lower() in analysis_text.lower()
                
                # If any item is not found, overall verification is false
                if not found:
                    verification_results["verified"] = False
                
                # Extract relevant portion of the analysis for this item
                item_details = ""
                lines = analysis_text.split("\n")
                for i, line in enumerate(lines):
                    if item.lower() in line.lower():
                        # Take this line and a few after it as the item details
                        item_details = "\n".join(lines[i:i+5])
                        break
                        
                # Try to extract grid location from details
                location = None
                if "grid" in item_details.lower():
                    for word in item_details.split():
                        if word.isdigit() and "grid" in item_details.lower().split(word)[0][-10:]:
                            location = word
                            break
                
                # Add the verification result for this item
                verification_results["items"].append({
                    "item": item,
                    "found": found,
                    "confidence": 0.9 if found else 0.1,  # Simplified confidence score
                    "location": location,
                    "details": item_details if item_details else "No specific details found"
                })
            
            print(f"Verification completed for {len(verification_items)} items")
            return verification_results
                
        except Exception as e:
            print(f"Error verifying screen content: {str(e)}")
            return {
                "verified": False, 
                "items": [], 
                "error": str(e)
            }
            
    def verify_screen_elements(self, verification_items, take_new_screenshot=True):
        """
        Convenience method to take a screenshot and verify elements in one step.
        
        Args:
            verification_items (list): List of elements to verify
            take_new_screenshot (bool): Whether to take a new screenshot (True) or use the last one (False)
            
        Returns:
            dict: Verification results
        """
        # Step 1: Get a screenshot (either new or existing)
        if take_new_screenshot:
            screenshot_path = self.take_screenshot()
            if not screenshot_path:
                return {"verified": False, "items": [], "error": "Failed to take screenshot"}
        else:
            # Use the most recent screenshot file
            screenshot_files = [f for f in os.listdir('.') if f.startswith('screenshot_') and f.endswith('.png')]
            if not screenshot_files:
                return {"verified": False, "items": [], "error": "No existing screenshots found"}
            screenshot_path = sorted(screenshot_files)[-1]  # Get the most recent one
            
        # Step 2: Apply grid overlay
        grid_path = self.apply_grid_to_screenshot(screenshot_path)
        
        # Step 3: Verify content
        return self.verify_screen_content(grid_path, verification_items)

if __name__ == "__main__":
    # Example usage
    analyzer = ScreenshotAnalyzer()
    
    # Capture screenshot, apply grid, and extract text
    result = analyzer.capture_analyze_with_grid()
    
    # Print paths to generated files
    print(f"\nOriginal screenshot: {result['screenshot_path']}")
    print(f"Grid overlay: {result['grid_screenshot_path']}")
    
    # Print extracted text 
    if result['extracted_text']:
        print(f"\nExtracted text:\n{result['extracted_text']}")
