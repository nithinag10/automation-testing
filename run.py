#!/usr/bin/env python3
"""
Multi-Agent LangGraph Supervisor for Android Automation
"""

# =============================================================================
# IMPORTS AND CONFIGURATION
# =============================================================================
from ast import Store
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


@tool
def inform_activity(screen_name: str, action_description: str) -> str:
    """
    Track and log the agent's current activity for accessibility purposes.
    
    This function is designed to help users (especially those with visual impairments)
    understand what screen the agent is currently on and what action it's going to perform.
    
    Args:
        screen_name (str): The name or description of the current screen
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

# =============================================================================
# AGENT DEFINITIONS
# =============================================================================

# Define tool sets for different agents
action_tools = [
    get_screen_data,
    click_grid,
    perform_gesture,
    inform_activity,
    ask_human_for_help,
]

validation_tools = [
    get_screen_data,
    perform_gesture,
    ask_human_for_help,
]



memory = InMemorySaver()

# Action Agent: performs UI interactions
action_agent = create_react_agent(
    llm,
    tools=action_tools,
    prompt="""
You are an Action Agent specialized in executing tasks on Android devices. Your primary objective is to perform the given action no matter what, using all available interactions.

Your Capabilities:
You can analyze screens, tap on elements, perform gestures (scroll up, swipe left/right), type text, press system buttons, and navigate back.
Use get_screen_data to capture and analyze the current screen in a single step.
Use perform_gesture with the gesture type (e.g., "scroll_up", "swipe_left", "swipe_right") to navigate.
If an element is not visible, use perform_gesture to find it before taking action.
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
    name="action_agent",
    checkpointer=memory
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
    model=llm,
    prompt=(
        "You are a supervisor managing Android automation tasks. "
        "You have two experts: an action agent that performs UI interactions and a validation agent that confirms the results. "
        "Direct the agents to complete the user's automation request. "
        "Once all steps are verified, respond with FINISH and a summary of the actions taken."
    ),
    output_mode="full_history",

)

def log_state(state):
    """Log the complete state for debugging purposes."""
    print("\n=== Current State ===")
    print(json.dumps(state, indent=2, default=lambda o: o.__dict__))  # Pretty-print state

compiled_supervisor = supervisor_workflow.compile(checkpointer=memory)


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

        # Add thread ID to configuration
    config = {
        "configurable": {
            "thread_id": "1"  # Or generate a unique ID, e.g., str(uuid4())
        },
        "recursion_limit": 50
    }

    # Invoke the supervisor workflow
    result = compiled_supervisor.invoke(initial_input, config)
    # Access and print ALL checkpoint data (using .list())
    print("\n=== All Stored Checkpoints ===")
    for checkpoint_tuple in memory.list(config): # Correct usage of .list()
        print(f"Checkpoint")
        print(checkpoint_tuple)
        print("-" * 40)

    print("\n=== Supervisor Result ===")
    print(json.dumps(result, indent=2, default=lambda o: o.__dict__))

    # Create logs directory if it doesn't exist
    log_dir = "activity_logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Create or append to the activity log file
    log_file = os.path.join(log_dir, "agent_activity_log.jsonl")
    
    with open(log_file, "w") as f:
        f.write(f"AUTOMATION TASK: {task_description}\n")
        f.write(f"COMPLETED AT: {datetime.datetime.now().isoformat()}\n")
        f.write("="*80 + "\n\n")
        
        # Lifecycle markers
        f.write("=== LIFE BEFORE AUTOMATION ===\n")
        f.write("Initial state captured in screenshots/actions history\n\n")
        
        f.write("=== ACTIVITY TIMELINE ===\n")
        # Write events here...
        
        f.write("\n=== LIFE AFTER AUTOMATION ===\n")
        f.write("Final state captured in screenshots/actions history\n")
        f.write("="*80 + "\n")
        f.write("=== END OF ACTIVITY LOG ===\n")

    # Save combined human-readable log
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    screen_data_history = []
    actions_history = []
    all_events = []
    for event in result["messages"]:
        if event["role"] == "agent":
            if event["content"]["type"] == "function":
                if event["content"]["name"] == "get_screen_data":
                    screen_data_history.append({"timestamp": event["timestamp"], "screen_data": event["content"]["output"]})
                elif event["content"]["name"] == "click_grid" or event["content"]["name"] == "perform_gesture" or event["content"]["name"] == "input_text" or event["content"]["name"] == "press_system_key":
                    actions_history.append({"timestamp": event["timestamp"], "action": event["content"]["name"], "output": event["content"]["output"]})
        all_events.append({"timestamp": event["timestamp"], "type": event["role"], "agent": event["agent"], "content": event["content"]})
    if screen_data_history or actions_history:
        log_file = os.path.join(logs_dir, f"task_log_{timestamp}.txt")
        with open(log_file, "w") as f:
            # Lifecycle Header
            f.write(f"=== AUTOMATION LIFE CYCLE ===\n")
            f.write(f"Task: {task_description}\n")
            f.write(f"Start: {datetime.datetime.now().isoformat()}\n\n")

            # Initial State
            f.write("=== LIFE BEFORE AUTOMATION ===\n")
            if screen_data_history:
                f.write(f"Initial Screen State:\n{screen_data_history[0]['screen_data'][:500]}...\n\n")
            f.write("No actions performed yet\n\n")

            # Activity Timeline
            f.write("=== ACTIVITY TIMELINE ===\n")
            for idx, event in enumerate(all_events, 1):
                f.write(f"EVENT {idx} - {event['type'].upper()} - {event['timestamp']}\n")
                f.write(f"Agent: {event['agent']}\n")
                f.write(f"{event['content']}\n")
                f.write("-"*50 + "\n\n")

            # Final State
            f.write("=== LIFE AFTER AUTOMATION ===\n")
            if screen_data_history:
                f.write(f"Final Screen State:\n{screen_data_history[-1]['screen_data'][:500]}...\n\n")
            f.write(f"Total Actions Performed: {len(actions_history)}\n")
            f.write(f"End: {datetime.datetime.now().isoformat()}\n")
            f.write("="*80 + "\n")
            f.write("=== END OF LOG ===\n")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    # Example: Automate opening the settings app and validating the settings screen.
    task = "Open Whatsapp, scroll screen to find lbs park lane group and open the chat messages."
    run_supervisor(task)
