#!/usr/bin/env python3
"""
Multi-Agent LangGraph Supervisor for Android Automation
"""

import os
import json
from datetime import datetime
from typing import Literal, List
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

# Local modules and previously defined agents/tools
from langgraph.graph import StateGraph, END, START
from langchain_core.tools import tool, Tool
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from device_actions import DeviceActions
from screenshot_analyzer import ScreenshotAnalyzer

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure models
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Initialize device and screenshot analyzer (assumes these classes are implemented)
device = DeviceActions()
screenshot_analyzer = ScreenshotAnalyzer()

# Initialize LLM (using GPT-4o)
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Define tools for the agents
@tool
def take_screenshot(output_path: str = None) -> str:
    """Take a screenshot of the Android device's current screen using ADB."""
    print("\n=== Taking Screenshot ===")

    if output_path is None:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"screenshot_{timestamp}.png"
    print(f"Screenshot output path: {output_path}")

    try:
        print("Using device.screenshot() method for reliable screenshot capture")
        # Use the device's screenshot method directly
        success = device.take_screenshot(output_path)
        
        if not success:
            error_msg = "Screenshot failed using device.screenshot() method"
            print(f"Error: {error_msg}")
            return error_msg

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            file_size = os.path.getsize(output_path)
            print(f"Screenshot saved successfully. File size: {file_size} bytes")
            return f"Screenshot saved to {output_path}"
        else:
            error_msg = "Screenshot file is empty or not created"
            print(f"Error: {error_msg}")
            return error_msg
    except Exception as e:
        error_msg = f"Error taking screenshot: {str(e)}"
        print(f"Exception: {error_msg}")
        return error_msg

@tool
def analyze_screenshot(screenshot_path: str) -> str:
    """Analyze a screenshot to extract text and UI elements."""
    print("\n=== Analyzing Screenshot ===")
    print(f"Screenshot path: {screenshot_path}")

    if not os.path.exists(screenshot_path):
        error_msg = f"Screenshot file not found: {screenshot_path}"
        print(f"Error: {error_msg}")
        return error_msg

    print("Applying 7mm touch-size grid overlay (based on 405 PPI)")
    grid_screenshot = screenshot_analyzer.apply_grid_to_screenshot(screenshot_path)
    print(f"Grid overlay applied: {grid_screenshot}")

    print("Extracting text using Gemini Vision...")
    extracted_text = screenshot_analyzer.extract_text_with_gemini(grid_screenshot)

    if not extracted_text:
        error_msg = "Failed to extract text from screenshot."
        print(f"Error: {error_msg}")
        return error_msg

    print(f"Successfully extracted text, length: {len(extracted_text)} characters")
    return extracted_text

@tool
def click_at_coordinates(x: int, y: int) -> str:
    """Click at the specified coordinates (x, y) on the screen."""
    print(f"\n=== Clicking at ({x}, {y}) ===")
    print(f"Screen bounds: 1080x2400")  # Known device resolution
    
    # Validate coordinates
    if not (0 <= x <= 1080 and 0 <= y <= 2400):
        error_msg = f"Coordinates ({x}, {y}) out of bounds for 1080x2400 screen"
        print(f"Error: {error_msg}")
        return error_msg
        
    print("Executing device.click() method...")
    # Use the device's click method directly
    success = device.click(x, y)
    
    if success:
        print("Click action successful")
        return f"Clicked at coordinates ({x}, {y})."
    else:
        error_msg = f"Failed to click at coordinates ({x}, {y})."
        print(f"Error: {error_msg}")
        return error_msg

@tool
def swipe_on_screen(start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5) -> str:
    """Swipe from start coordinates to end coordinates on the screen."""
    print(f"\n=== Swiping from ({start_x}, {start_y}) to ({end_x}, {end_y}) ===")
    print(f"Screen bounds: 1080x2400")  # Known device resolution
    print(f"Swipe duration: {duration}s")
    
    # Validate coordinates
    if not (0 <= start_x <= 1080 and 0 <= start_y <= 2400 and 
            0 <= end_x <= 1080 and 0 <= end_y <= 2400):
        error_msg = f"Coordinates out of bounds for 1080x2400 screen"
        print(f"Error: {error_msg}")
        return error_msg
        
    print("Executing swipe command...")
    success = device.swipe(start_x, start_y, end_x, end_y, duration=duration)
    
    if success:
        print("Swipe action successful")
        return f"Swiped from ({start_x}, {start_y}) to ({end_x}, {end_y})."
    else:
        error_msg = f"Failed to swipe from ({start_x}, {start_y}) to ({end_x}, {end_y})."
        print(f"Error: {error_msg}")
        return error_msg

@tool
def input_text(text: str) -> str:
    """Input text on the device."""
    print(f"\n=== Inputting Text ===")
    print(f"Text to input: {text}")
    
    if not text:
        error_msg = "Empty text provided"
        print(f"Error: {error_msg}")
        return error_msg
        
    print("Executing input command...")
    success = device.input_text(text)
    
    if success:
        print("Text input successful")
        return f"Input text: {text}"
    else:
        error_msg = f"Failed to input text: {text}"
        print(f"Error: {error_msg}")
        return error_msg

@tool
def press_system_key(key_name: str) -> str:
    """Press a system key on the device.

    Available keys: home, back, enter, volume_up, volume_down, power
    """
    print(f"\n=== Pressing System Key: {key_name} ===")
    
    key_map = {
        "home": 3,
        "back": 4,
        "volume_up": 24,
        "volume_down": 25,
        "enter": 66,
    }

    key_code = key_map.get(key_name.lower())
    if not key_code:
        error_msg = f"Unknown key: {key_name}. Available keys: {list(key_map.keys())}"
        print(f"Error: {error_msg}")
        return error_msg

    print(f"Executing key press command (keycode: {key_code})...")
    success = device.press_key(key_code)
    
    if success:
        print("Key press successful")
        return f"Pressed system key: {key_name}"
    else:
        error_msg = f"Failed to press system key: {key_name}"
        print(f"Error: {error_msg}")
        return error_msg


@tool
def ask_human_for_help(question: str) -> str:
    """Ask the human for help or clarification."""
    print(f"\n[Agent is asking for your help]: {question}")
    user_input = input("Your response: ")
    return f"Human response: {user_input}"

# Action Agent: performs UI interactions
action_agent = create_react_agent(
    llm,
    tools=[
    take_screenshot,
    analyze_screenshot,
    click_at_coordinates,
    swipe_on_screen,
    ask_human_for_help,
    ],
    prompt="""
You are an Action Agent for Android devices. You perform UI interactions like clicking, swiping, and text input.
Always start by capturing the current screen state (screenshot) before performing an action.
If uncertain, ask for human help.
""",
    name="action_agent"
)

# Validation Agent: verifies that actions were successful
validation_agent = create_react_agent(
    llm,
    tools=[
    take_screenshot,
    analyze_screenshot,
    swipe_on_screen,
    ask_human_for_help,
    ],
    prompt="""
You are a Validation Agent for Android devices. Your job is to verify that UI actions have succeeded.
Always begin by taking a screenshot to inspect the current state and confirm whether the expected changes occurred.
""",
    name="validation_agent"
)

# --- Create the Supervisor Workflow ---
# Optionally, you can add memory support:
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore


supervisor_workflow = create_supervisor(
    agents=[action_agent, validation_agent],
    model=llm,
    prompt=(
        "You are a supervisor managing Android automation tasks. "
        "You have two experts: an action agent that performs UI interactions and a validation agent that confirms the results. "
        "Direct the agents to complete the user's automation request. "
        "Once all steps are verified, respond with FINISH and a summary of the actions taken."
    ),
    output_mode="last_message"  # You can choose "full_history" to include all agent messages.
)

# Compile the supervisor workflow with memory support
compiled_supervisor = supervisor_workflow.compile()

# --- Example Invocation ---
def run_supervisor(task_description: str):
    print("\n=== Starting Supervisor Workflow ===")
    print(f"Task description: {task_description}\n")
    
    # Prepare the initial message
    initial_input = {
        "messages": [
            {"role": "user", "content": task_description}
        ]
    }
    
    # Invoke the supervisor workflow
    result = compiled_supervisor.invoke(initial_input)
    print("\n=== Supervisor Result ===")
    print(json.dumps(result, indent=2, default=lambda o: o.__dict__))

if __name__ == "__main__":
    # Example: Automate opening the settings app and validating the settings screen.
    task = "Open facebook application and check you are getting feeds properly"
    run_supervisor(task)
