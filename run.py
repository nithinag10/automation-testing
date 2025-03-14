#!/usr/bin/env python3
"""
Multi-Agent LangGraph Supervisor for Android Automation
"""

# =============================================================================
# IMPORTS AND CONFIGURATION
# =============================================================================
import os
import json
import datetime
from typing import Literal, List
from uuid import uuid4

# LangChain and LangGraph imports
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langchain_core.tools import tool, Tool
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor


# Local modules
from device_actions import DeviceActions
from screenshot_analyzer import ScreenshotAnalyzer
from grid_overlay import GridOverlay

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure OpenAI API
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Configure LangSmith tracing
unique_id = uuid4().hex[0:8]
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = f"Tracing Walkthrough - {unique_id}"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = os.environ.get("LANGSMITH_API_KEY")

# Initialize device and screenshot analyzer
device = DeviceActions()
screenshot_analyzer = ScreenshotAnalyzer()

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# =============================================================================
# TOOL DEFINITIONS
# =============================================================================

@tool
def get_screen_data() -> str:
    """
    Provides the details of the current screen. 
    
    Returns:
        str: The extracted text and UI elements from the current screen,
             or error message if the operation failed.
    """
    print("\n=== Capturing and Analyzing Screen ===")
    
    # Take screenshot
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"screenshot_{timestamp}.png"
    print(f"Screenshot output path: {output_path}")
    
    try:
        # Capture screenshot
        print("Using device.screenshot() method for screenshot capture")
        success = device.take_screenshot(output_path)
        
        if not success or not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            error_msg = "Screenshot failed or file is empty"
            print(f"Error: {error_msg}")
            return error_msg

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            file_size = os.path.getsize(output_path)
            print(f"Screenshot saved successfully. File size: {file_size} bytes")
        
        # Analyze screenshot
        print("Applying touch-size grid overlay (based on 405 PPI)")
        grid_screenshot = screenshot_analyzer.apply_grid_to_screenshot(output_path)
        print(f"Grid overlay applied: {grid_screenshot}")
        
        print("Extracting text using Gemini Vision...")
        extracted_text = screenshot_analyzer.extract_text_with_gemini(grid_screenshot)
        
        if not extracted_text:
            error_msg = "Failed to extract text from screenshot."
            print(f"Error: {error_msg}")
            return error_msg
        
        print(f"Successfully extracted text, length: {len(extracted_text)} characters")
        return extracted_text
        
    except Exception as e:
        error_msg = f"Error in screen data capture and analysis: {str(e)}"
        print(f"Exception: {error_msg}")
        return error_msg


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
        return f"Successfully input text: '{text}'"
    else:
        error_msg = f"Failed to input text: '{text}'"
        print(f"Error: {error_msg}")
        return error_msg


@tool
def verify_screen_elements(items_to_verify: List[str]) -> str:
    """
    Verify if specific elements or content are present on the current screen.
    
    Args:
        items_to_verify (List[str]): List of elements/content to verify, e.g. ["Facebook logo", "News Feed", "Like button"]
    
    Returns:
        str: Verification results formatted as a readable report
    """
    print(f"\n=== Verifying Screen Elements ===")
    print(f"Items to verify: {items_to_verify}")
    
    if not items_to_verify:
        error_msg = "No verification items provided"
        print(f"Error: {error_msg}")
        return error_msg
    
    try:
        # Take a new screenshot first
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"screenshot_{timestamp}.png"
        success = device.take_screenshot(output_path)
        
        if not success:
            error_msg = "Failed to take screenshot for verification"
            print(f"Error: {error_msg}")
            return error_msg
        
        # Apply grid overlay
        grid_path = screenshot_analyzer.apply_grid_to_screenshot(output_path)
        
        # Verify the elements
        verification_results = screenshot_analyzer.verify_screen_content(grid_path, items_to_verify)
        
        # Format the results as a readable report
        report = ["=== Screen Verification Report ==="]
        report.append(f"Total items checked: {len(items_to_verify)}")
        
        # Add overall verification result
        if verification_results.get("verified", False):
            report.append("✅ OVERALL RESULT: All items were found on the screen")
        else:
            report.append("❌ OVERALL RESULT: Some items were not found on the screen")
        
        # Add detailed results for each item
        report.append("\n=== Detailed Results ===")
        for item_result in verification_results.get("items", []):
            item_name = item_result.get("item", "Unknown item")
            found = item_result.get("found", False)
            location = item_result.get("location", "Unknown")
            confidence = item_result.get("confidence", 0)
            
            status = "✅ FOUND" if found else "❌ NOT FOUND"
            report.append(f"\n{status}: {item_name}")
            report.append(f"  Confidence: {confidence:.2f}")
            
            if found and location:
                report.append(f"  Location: Grid {location}")
            
            details = item_result.get("details", "").strip()
            if details:
                report.append(f"  Details: {details}")
        
        # Return the formatted report
        formatted_report = "\n".join(report)
        print("Verification completed")
        return formatted_report
        
    except Exception as e:
        error_msg = f"Error during screen verification: {str(e)}"
        print(f"Exception: {error_msg}")
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
def ask_human_for_help(query: str) -> str:
    """Request human assistance and log the conversation. Use this when stuck or need clarification.
    
    Args:
        query: The specific question/request for the human
        
    Returns:
        str: Human's response
    """
    # Get human input
    response = input(f"AGENT REQUEST: {query}\nYour response: ")
    
    # Log to activity log
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "human_interaction",
        "request": query,
        "response": response
    }
    
    try:
        log_dir = "activity_logs"
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, "agent_activity_log.jsonl"), "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Error logging human interaction: {e}")

    return response


@tool
def inform_activity(screen_name: str, action_description: str) -> str:
    """
    Track and log the agent's current activity for accessibility purposes.
    
    This function is designed to help users (especially those with visual impairments)
    understand what screen the agent is currently on and what action it's going to perform.
    
    Args:
        screen (str): The current screen you got from screen data
        action_description (str): Description of the action being performed
        
    Returns:
        str: Confirmation message that the activity was logged
    """
    # Create logs directory if it doesn't exist
    log_dir = "activity_logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Create or append to the activity log file
    log_file = os.path.join(log_dir, "agent_activity_log.jsonl")
    
    # Prepare log entry
    timestamp = datetime.datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "screen": screen_name,
        "action": action_description
    }
    
    # Append to log file
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    # Format message for user feedback (especially for accessibility)
    accessibility_message = f"Screen: {screen_name} | Action: {action_description}"
    
    print(f"\n[ACTIVITY TRACKER] {accessibility_message}\n")
    return accessibility_message


@tool
def application_workflow() -> str:
    """
    Retrieves all recorded activities from the application's activity logs and past human helps. 

    This tool pulls the complete history of screens visited and actions performed
    by the agent, providing a full workflow trace of the application's usage.
    
    Returns:
        str: JSON string containing all logged activities in chronological order
    """
    log_file = os.path.join("activity_logs", "agent_activity_log.jsonl")
    
    # Check if log file exists
    if not os.path.exists(log_file):
        return "No activity logs found."
    
    # Read all logs
    activities = []
    with open(log_file, "r") as f:
        for line in f:
            if line.strip():  # Skip empty lines
                try:
                    log_entry = json.loads(line)
                    activities.append(log_entry)
                except json.JSONDecodeError:
                    continue  # Skip malformed entries
    
    # Sort activities by timestamp if needed
    activities.sort(key=lambda x: x.get("timestamp", ""))
    
    if not activities:
        return "Activity log exists but contains no entries."
    
    # Format the result
    result = {
        "total_activities": len(activities),
        "workflow": activities
    }
    
    return json.dumps(result, indent=2)



# =============================================================================
# AGENT DEFINITIONS
# =============================================================================

# Define tool sets for different agents
interaction_tools = [
    get_screen_data,
    click_grid,
    perform_gesture,
    press_system_key,
    inform_activity,
    application_workflow,
    verify_screen_elements
]

validation_tools = [
    get_screen_data,
    perform_gesture,
    ask_human_for_help,
    verify_screen_elements
]

# Action Agent: performs UI interactions
action_agent = create_react_agent(
    llm,
    tools=interaction_tools,
    prompt="""
You are an Action Agent specialized in executing tasks on Android devices. Your primary objective is to perform the given action no matter what, using all available interactions.

Your Capabilities:
You can analyze screens, tap on elements, perform gestures (scroll up, swipe left/right), type text, press system buttons, and navigate back.
Use get_screen_data to capture and analyze the current screen in a single step.
Use perform_gesture with the gesture type (e.g., "scroll_up", "swipe_left", "swipe_right") to navigate.
If an element is not visible, use perform_gesture to find it before taking action.
You can handle multi-step interactions, such as opening menus, navigating back, or retrying failed actions.
If you encounter ambiguity or an issue, use old application workflow to understand better. 
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
    tools=validation_tools,
    prompt="""
You are a Validation Agent for Android devices. Your job is to verify that UI actions have succeeded.
Always begin by using get_screen_data to inspect the current state and confirm whether the expected changes occurred.
""",
    name="validation_agent"
)

# =============================================================================
# SUPERVISOR SETUP
# =============================================================================

# Create the Supervisor Workflow
supervisor_workflow = create_supervisor(
    agents=[action_agent, validation_agent],
    tools=[ask_human_for_help],
    model=llm,
    prompt=(
        "You are a supervisor managing Android automation tasks. "
        "You have two experts: an action agent that performs UI interactions and a validation agent that confirms the results. "
        "Direct the agents to complete the user's automation request. "
        "Once all steps are verified, respond with FINISH and a summary of the actions taken."
        "Before executing, analyze the user's automation request and create a structured execution plan. Break down the request into clear, step-by-step instructions, specifying actions and expected validation points."
        "Ask for human help if something you are stuck at"
    ),
    output_mode="full_history",
)

def log_state(state):
    """Log the complete state for debugging purposes."""
    print("\n=== Current State ===")
    print(json.dumps(state, indent=2, default=lambda o: o.__dict__))  # Pretty-print state

compiled_supervisor = supervisor_workflow.compile()


# =============================================================================
# EXECUTION FUNCTIONS
# =============================================================================

def run_supervisor(task_description: str):
    """
    Run the supervisor workflow with a task description.
    
    Args:
        task_description (str): The automation task to perform
    """
    print("\n=== Starting Supervisor Workflow ===")
    print(f"Task description: {task_description}\n")
    
    # Prepare the initial message
    initial_input = {
        "messages": [
            {"role": "user", "content": task_description}
        ]
    }

    config = {
        "recursion_limit": 50
    }

    # Invoke the supervisor workflow
    result = compiled_supervisor.invoke(initial_input, config)

    print("\n=== Supervisor Result ===")
    print(json.dumps(result, indent=2, default=lambda o: o.__dict__))
    
    # Store the supervisor result in a JSON file
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = os.path.join(results_dir, f"supervisor_result_{timestamp}.json")
    
    with open(result_file, "w") as f:
        json.dump(result, f, indent=2, default=lambda o: o.__dict__)
    
    print(f"Supervisor result saved to {result_file}")

    # Create logs directory if it doesn't exist
    log_dir = "activity_logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Create or append to the activity log file with simplified output
    log_file = os.path.join(log_dir, "agent_activity_log.jsonl")
    
    with open(log_file, "w") as f:
        f.write(f"AUTOMATION TASK: {task_description}\n")
        f.write(f"COMPLETED AT: {datetime.datetime.now().isoformat()}\n")

    print(f"Automation task completed and logged to {log_file}")
    return result

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    # Read task from instruction.txt file
    try:
        with open("instruction.txt", "r") as f:
            task = f.read().strip()
            if not task:
                print("Warning: instruction.txt is empty. Using default task.")
                task = "Open Whatsapp, scroll screen to find lbs park lane group and open the chat messages."
    except FileNotFoundError:
        print("Warning: instruction.txt not found. Using default task.")
        task = "Open Whatsapp, scroll screen to find lbs park lane group and open the chat messages."
    
    print(f"Executing task: {task}")
    run_supervisor(task)
