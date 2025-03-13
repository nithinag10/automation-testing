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

# Local modules and previously defined agents/tools.invoke
from langgraph.graph import StateGraph, END, START
from langchain_core.tools import tool, Tool
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from device_actions import DeviceActions
from screenshot_analyzer import ScreenshotAnalyzer
from grid_overlay import GridOverlay

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
def take_screenshot() -> str:
    """Take a screenshot of the Android device's current screen using ADB. Let the output path be a simple time stamp"""
    print("\n=== Taking Screenshot ===")

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

    print("Applying touch-size grid overlay (based on 405 PPI)")
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
    
    # Initialize GridOverlay with the device's specifications
    grid_overlay = GridOverlay()
    
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
def scroll_up() -> str:
    """Scroll up on the device screen."""
    if device.scroll_up():
        return "Successfully scrolled up"
    return "Failed to scroll up"

@tool
def swipe_left() -> str:
    """Swipe left on the device screen."""
    if device.swipe_left():
        return "Successfully swiped left"
    return "Failed to swipe left"

@tool
def swipe_right() -> str:
    """Swipe right on the device screen."""
    if device.swipe_right():
        return "Successfully swiped right"
    return "Failed to swipe right"

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
    click_grid,
    scroll_up,
    swipe_left,
    swipe_right,
    ask_human_for_help,
    ],
    prompt="""
You are an Action Agent specialized in executing tasks on Android devices. Your primary objective is to perform the given action no matter what, using all available interactions.

Your Capabilities:
You can tap, swipe (left, right, up, down), scroll, type, press buttons, and navigate back.
If an element is not visible, you scroll to find it before taking action.
You can handle multi-step interactions, such as opening menus, navigating back, or retrying failed actions.
If you encounter ambiguity or an issue, you can involve a human for clarification.
Your Ultimate Goal:
Execute the requested action with maximum efficiency and accuracy.
Ensure task completion even if it requires retries, adjustments, or alternative paths.
Constraints:
Do not stop unless the task is impossible after all options are exhausted.
Always prioritize efficiency and accuracy in interactions.
If your action didn't work, retry again differently. 
During click, always prefer clicking on icons.
""",
    name="action_agent"
)

# Validation Agent: verifies that actions were successful
validation_agent = create_react_agent(
    llm,
    tools=[
    take_screenshot,
    analyze_screenshot,
    scroll_up,
    swipe_left,
    swipe_right,
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
    result = compiled_supervisor.invoke(initial_input , {"recursion_limit": 50})
    print("\n=== Supervisor Result ===")
    print(json.dumps(result, indent=2, default=lambda o: o.__dict__))

if __name__ == "__main__":
    # Example: Automate opening the settings app and validating the settings screen.
    task = "Open Whatsapp, go to calls from the bottom right , call the second person on the list. If the calls successfully dials that it is success"
    run_supervisor(task)
