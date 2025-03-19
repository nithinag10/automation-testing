#!/usr/bin/env python3
"""
Device Actions Module

This module provides functionality to perform actions on Android devices
using the UIAutomator2 library. It supports actions like clicking on
specific coordinates, swiping, typing text, and more.

"""

import os
import time
from datetime import datetime

# Try to import UI Automator for device control
try:
    import uiautomator2 as u2
    UI_AUTOMATOR_AVAILABLE = True
except ImportError:
    print("Warning: uiautomator2 not available. Device interactions will be disabled.")
    UI_AUTOMATOR_AVAILABLE = False

class DeviceActions:
    """
    A class that provides methods to perform actions on Android devices.
    
    This class uses UIAutomator2 to interact with Android devices, allowing
    for actions like clicking, swiping, typing, and more based on screen
    coordinates.
    """
    
    def __init__(self, device_serial=None):
        """
        Initialize the DeviceActions class.
        
        Args:
            device_serial (str, optional): Serial number of the Android device.
                If not provided, connects to the first available device.
        """
        self.device_serial = device_serial
        self.device = None
        self._connect_to_device()
        
    def _connect_to_device(self):
        """
        Connect to an Android device using UIAutomator2.
        
        If device_serial is provided, connects to that specific device.
        Otherwise, connects to the first available device.
        """
        if not UI_AUTOMATOR_AVAILABLE:
            print("UIAutomator2 not available. Device interactions will be disabled.")
            return
            
        try:
            if self.device_serial:
                # Connect to specific device
                self.device = u2.connect(self.device_serial)
                print(f"Connected to device: {self.device_serial}")
            else:
                # Connect to first available device
                import subprocess
                # Get list of connected devices
                result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
                lines = result.stdout.strip().split('\n')[1:]  # Skip the first line (header)
                
                # Find first connected device
                for line in lines:
                    if line.strip():
                        device_serial = line.split()[0]
                        self.device_serial = device_serial
                        self.device = u2.connect(device_serial)
                        print(f"Connected to first available device: {device_serial}")
                        break
                
                if not self.device:
                    print("No devices found. Please connect a device.")
                    
        except Exception as e:
            print(f"Error connecting to device: {str(e)}")
            self.device = None
            
    def click(self, x, y):
        """
        Click on the specified coordinates using ADB shell input tap command.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
    
        Returns:
            bool: True if click was successful, False otherwise
        """
        if self.device is None:
            print("No device connected")
            return False
        
        try:
            # Use ADB shell input tap command
            self.device.shell(f'input tap {x} {y}')
            print(f"Clicked at coordinates: ({x}, {y})")
            return True
        except Exception as e:
            print(f"Error clicking at coordinates: {str(e)}")
            return False
            
    def swipe(self, start_x, start_y, end_x, end_y):
        """
        Swipe from start coordinates to end coordinates.
        
        Args:
            start_x (int): Starting X-coordinate.
            start_y (int): Starting Y-coordinate.
            end_x (int): Ending X-coordinate.
            end_y (int): Ending Y-coordinate.
            duration (float, optional): Duration of the swipe in seconds. Default is 0.5.
                
        Returns:
            bool: True if the swipe was successful, False otherwise.
        """
        if not UI_AUTOMATOR_AVAILABLE or not self.device:
            print("UIAutomator2 not available or no device connected. Cannot perform swipe.")
            return False
            
        try:
            self.device.swipe(start_x, start_y, end_x, end_y, duration=duration)
            print(f"Swiped from ({start_x}, {start_y}) to ({end_x}, {end_y})")
            return True
        except Exception as e:
            print(f"Error swiping: {str(e)}")
            return False
            

    def input_text(self, text):
        """
        Input text on the device using ADB.

        Args:
            text (str): The text to input.

        Returns:
            bool: True if the command executed successfully, False otherwise.
        """
        try:
            # Escape special characters in the text for ADB compatibility
            escaped_text = text.replace(" ", "%s")
            command = f'adb shell input text "{escaped_text}"'
            
            # Execute the ADB command
            result = os.system(command)
            
            if result == 0:
                print(f"Successfully inputted text: {text}")
                return True
            else:
                print(f"Failed to input text: {text}")
                return False
        except Exception as e:
            print(f"Error while inputting text via ADB: {str(e)}")
            return False
            
    def press_key(self, key_code):
        """
        Press a key on the device using Android key codes.
        
        Args:
            key_code (int): Android key code to press.
                Common key codes:
                - 3: HOME
                - 4: BACK
                - 24: VOLUME_UP
                - 25: VOLUME_DOWN
                - 26: POWER
                - 66: ENTER
                
        Returns:
            bool: True if the key press was successful, False otherwise.
        """
        if not UI_AUTOMATOR_AVAILABLE or not self.device:
            print("UIAutomator2 not available or no device connected. Cannot press key.")
            return False
            
        try:
            self.device.press(key_code)
            print(f"Pressed key code: {key_code}")
            return True
        except Exception as e:
            print(f"Error pressing key: {str(e)}")
            return False
            
    def wait(self, seconds):
        """
        Wait for the specified number of seconds.
        
        Args:
            seconds (float): Number of seconds to wait.
        """
        time.sleep(seconds)
        print(f"Waited for {seconds} seconds")
        
    def take_screenshot(self, output_path: str) -> bool:
        """
        Take a screenshot using uiautomator2 and save it to the specified path.
        
        Args:
            output_path (str): Path where the screenshot should be saved
    
        Returns:
            bool: True if screenshot was successful, False otherwise
        """
        if not UI_AUTOMATOR_AVAILABLE or not self.device:
            print("UIAutomator2 not available or no device connected.")
            # Fallback: Create a dummy screenshot for testing
            try:
                from PIL import Image, ImageDraw, ImageFont
                # Create a blank image with text indicating no device
                img = Image.new('RGB', (1080, 2400), color=(50, 50, 50))
                draw = ImageDraw.Draw(img)
                draw.text((540, 1200), "No Device Connected", fill=(255, 255, 255), anchor="mm")
                draw.text((540, 1300), "Mock Screenshot", fill=(255, 255, 255), anchor="mm")
                img.save(output_path)
                print(f"Created mock screenshot at {output_path}")
                return os.path.exists(output_path)
            except Exception as e:
                print(f"Error creating mock screenshot: {str(e)}")
                return False
        
        try:
            # Use uiautomator2's screenshot method
            self.device.screenshot(output_path)
            return os.path.exists(output_path) and os.path.getsize(output_path) > 0
        except Exception as e:
            print(f"Error taking screenshot: {str(e)}")
            return False
            
    def long_click(self, x, y, duration=1.0):
        """
        Perform a long click at the specified coordinates.
        
        Args:
            x (int): X-coordinate to long click.
            y (int): Y-coordinate to long click.
            duration (float, optional): Duration of the long click in seconds. Default is 1.0.
                
        Returns:
            bool: True if the long click was successful, False otherwise.
        """
        if not UI_AUTOMATOR_AVAILABLE or not self.device:
            print("UIAutomator2 not available or no device connected. Cannot perform long click.")
            return False
            
        try:
            self.device.long_click(x, y, duration=duration)
            print(f"Long clicked at coordinates: ({x}, {y}) for {duration} seconds")
            return True
        except Exception as e:
            print(f"Error long clicking at coordinates ({x}, {y}): {str(e)}")
            return False
            
    def scroll_up(self):
        """
        Scroll up on the device screen using ADB shell swipe command.
        This performs a gentle scroll that only moves enough to reveal new content.
        
        Returns:
            bool: True if scroll was successful, False otherwise
        """
        if self.device is None:
            print("No device connected")
            return False
            
        try:
            # Perform a gentler scroll up (from bottom to middle-top)
            # Use a shorter distance to avoid scrolling too far
            # Original was: self.device.shell('input swipe 540 2000 540 500 200')
            self.device.shell('input swipe 540 1500 540 1000 200')
            print("Scrolled up gently")
            return True
        except Exception as e:
            print(f"Error scrolling up: {str(e)}")
            return False

    def scroll_down(self):
        """
        Scroll down on the device screen using ADB shell swipe command.
        This performs a gentle scroll that only moves enough to reveal new content.
        
        Returns:
            bool: True if scroll was successful, False otherwise
        """
        if self.device is None:
            print("No device connected")
            return False
            
        try:
            # Perform a gentle scroll down (from middle-top to middle-bottom)
            # Use a shorter distance to avoid scrolling too far
            self.device.shell('input swipe 540 1000 540 1500 200')
            print("Scrolled down gently")
            return True
        except Exception as e:
            print(f"Error scrolling down: {str(e)}")
            return False

    def swipe_left(self):
        """
        Swipe left on the device screen using ADB shell swipe command.
        
        Returns:
            bool: True if swipe was successful, False otherwise
        """
        if self.device is None:
            print("No device connected")
            return False
            
        try:
            # Swipe from right to left
            self.device.shell('input swipe 900 1200 100 1200 200')
            print("Swiped left")
            return True
        except Exception as e:
            print(f"Error swiping left: {str(e)}")
            return False

    def swipe_right(self):
        """
        Swipe right on the device screen using ADB shell swipe command.
        
        Returns:
            bool: True if swipe was successful, False otherwise
        """
        if self.device is None:
            print("No device connected")
            return False
            
        try:
            # Swipe from left to right
            self.device.shell('input swipe 100 1200 900 1200 200')
            print("Swiped right")
            return True
        except Exception as e:
            print(f"Error swiping right: {str(e)}")
            return False


if __name__ == "__main__":
    # Example usage
    device = DeviceActions()
    
    # Take a screenshot
    screenshot_path = "screenshot.png"
    device.take_screenshot(screenshot_path)
    
    if os.path.exists(screenshot_path) and os.path.getsize(screenshot_path) > 0:
        # Example: Click at coordinates (500, 500)
        device.click(500, 500)
        
        # Wait for 1 second
        device.wait(1)
        
        # Example: Swipe down
        info = device.device.info
        width = info.get('displayWidth', 0)
        height = info.get('displayHeight', 0)
        device.swipe(width//2, height//4, width//2, height*3//4)
