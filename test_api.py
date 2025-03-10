#!/usr/bin/env python3
"""
Test script for the Android ADB API
"""

import requests
import json
import os
import sys
import argparse
from time import sleep

BASE_URL = 'http://localhost:5000/api'

def test_health():
    """Test health check endpoint"""
    response = requests.get(f'{BASE_URL}/health')
    print("Health check:", response.json())
    return response.status_code == 200

def test_devices():
    """Test getting devices list"""
    response = requests.get(f'{BASE_URL}/devices')
    print("Connected devices:")
    print(json.dumps(response.json(), indent=2))
    return response.status_code == 200

def test_screenshot(save_path="screenshot.png"):
    """Test taking a screenshot"""
    response = requests.get(f'{BASE_URL}/screenshot')
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"Screenshot saved to {save_path}")
        return True
    else:
        print("Failed to take screenshot:", response.json())
        return False

def test_tap(x, y):
    """Test tapping at specific coordinates"""
    response = requests.post(
        f'{BASE_URL}/tap',
        json={"x": x, "y": y}
    )
    print(f"Tap at ({x}, {y}):", response.json())
    return response.status_code == 200

def test_swipe(x1, y1, x2, y2, duration=300):
    """Test swiping between coordinates"""
    response = requests.post(
        f'{BASE_URL}/swipe',
        json={"x1": x1, "y1": y1, "x2": x2, "y2": y2, "duration": duration}
    )
    print(f"Swipe from ({x1}, {y1}) to ({x2}, {y2}):", response.json())
    return response.status_code == 200

def test_key(keycode):
    """Test pressing a key"""
    response = requests.post(
        f'{BASE_URL}/key',
        json={"keycode": keycode}
    )
    print(f"Press key {keycode}:", response.json())
    return response.status_code == 200

def test_text(text):
    """Test inputting text"""
    response = requests.post(
        f'{BASE_URL}/text',
        json={"text": text}
    )
    print(f"Input text '{text}':", response.json())
    return response.status_code == 200

def test_shell(command):
    """Test executing a shell command"""
    response = requests.post(
        f'{BASE_URL}/shell',
        json={"command": command}
    )
    print(f"Shell command '{command}':", response.json())
    return response.status_code == 200

def run_tests(args):
    """Run all tests based on command line arguments"""
    successful_tests = 0
    total_tests = 0
    
    # Always run health check
    total_tests += 1
    if test_health():
        successful_tests += 1
    
    # Devices test
    total_tests += 1
    if test_devices():
        successful_tests += 1
    
    # Screenshot test
    if args.screenshot:
        total_tests += 1
        if test_screenshot(args.screenshot_path):
            successful_tests += 1
    
    # Tap test
    if args.tap:
        total_tests += 1
        if test_tap(args.tap_x, args.tap_y):
            successful_tests += 1
    
    # Swipe test
    if args.swipe:
        total_tests += 1
        if test_swipe(args.swipe_x1, args.swipe_y1, args.swipe_x2, args.swipe_y2, args.swipe_duration):
            successful_tests += 1
    
    # Key test
    if args.key is not None:
        total_tests += 1
        if test_key(args.key):
            successful_tests += 1
    
    # Text test
    if args.text:
        total_tests += 1
        if test_text(args.text):
            successful_tests += 1
    
    # Shell test
    if args.shell:
        total_tests += 1
        if test_shell(args.shell):
            successful_tests += 1
    
    print(f"\nTests completed: {successful_tests}/{total_tests} successful")

def main():
    parser = argparse.ArgumentParser(description='Test Android ADB API')
    parser.add_argument('--screenshot', action='store_true', help='Test screenshot functionality')
    parser.add_argument('--screenshot-path', default='screenshot.png', help='Path to save screenshot')
    
    parser.add_argument('--tap', action='store_true', help='Test tap functionality')
    parser.add_argument('--tap-x', type=int, default=500, help='X coordinate for tap')
    parser.add_argument('--tap-y', type=int, default=500, help='Y coordinate for tap')
    
    parser.add_argument('--swipe', action='store_true', help='Test swipe functionality')
    parser.add_argument('--swipe-x1', type=int, default=100, help='Start X coordinate for swipe')
    parser.add_argument('--swipe-y1', type=int, default=500, help='Start Y coordinate for swipe')
    parser.add_argument('--swipe-x2', type=int, default=600, help='End X coordinate for swipe')
    parser.add_argument('--swipe-y2', type=int, default=500, help='End Y coordinate for swipe')
    parser.add_argument('--swipe-duration', type=int, default=300, help='Duration of swipe in ms')
    
    parser.add_argument('--key', type=int, help='Test key press with keycode')
    parser.add_argument('--text', help='Test text input with specified text')
    parser.add_argument('--shell', help='Test shell command execution')
    
    args = parser.parse_args()
    
    # If no specific tests are specified, run all tests
    if not any([args.screenshot, args.tap, args.swipe, args.key is not None, args.text, args.shell]):
        args.screenshot = True
        args.tap = True
        args.swipe = True
        args.key = 4  # BACK key
        args.text = "Hello from test script"
        args.shell = "ls -la"
    
    run_tests(args)

if __name__ == "__main__":
    main()
