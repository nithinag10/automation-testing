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

# Import core modules
from core.device_actions import DeviceActions
from core.screenshot_analyzer import ScreenshotAnalyzer
from core.grid_overlay import GridOverlay
from core.logger import log_activity, log_human_interaction, log_task_completion

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
        error_msg = f"Error in get_screen_data: {str(e)}"
        print(f"Error: {error_msg}")
        return error_msg

@tool
def click_grid(grid_number: int) -> str:
    """
    Perform a click action at the center of the specified grid cell.
    
    Args:
        grid_number (int): The grid cell number (starting from 1) where the click should occur.
    
    Returns:
        str: Success message with grid number and corresponding screen coordinates,
             or error message if the click failed.
    """
    print(f"\n=== Clicking at grid {grid_number} ===")
    print(f"Screen bounds: 1080x2400")  # Known device resolution
    
    # Get grid overlay instance to map grid numbers to coordinates
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
    """
    Input text on the device.
    """
    print(f"\n=== Inputting Text: {text} ===")
    
    try:
        success = device.input_text(text)
        
        if success:
            return f"Successfully input text: '{text}'"
        else:
            return "Failed to input text"
            
    except Exception as e:
        error_msg = f"Error inputting text: {str(e)}"
        print(f"Exception: {error_msg}")
        return error_msg

@tool
def match_screen_with_description(expected_screen_description: str) -> str:
    """
    Check if the current screen matches the provided description.
    
    This tool captures the current screen and analyzes whether it matches the expected description.
    It compares what is actually displayed on the screen with what should be displayed according
    to the description.
    
    Args:
        expected_screen_description (str): A detailed description of what the screen should look like.
                                          Example: "WhatsApp home screen with chat list visible and search bar at the top"
    
    Returns:
        str: Analysis report detailing whether the screen matches the expected description
    """
    print(f"\n=== Matching Screen with Description ===")
    print(f"Expected screen description: {expected_screen_description}")
    
    # Take a screenshot first
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = f"validation_screenshot_{timestamp_str}.png"
    
    try:
        # Capture screenshot
        print(f"Taking screenshot for validation: {screenshot_path}")
        success = device.take_screenshot(screenshot_path)
        
        if not success or not os.path.exists(screenshot_path):
            error_msg = "Failed to take screenshot for validation"
            print(f"Error: {error_msg}")
            return json.dumps({"matches": False, "error": error_msg})
            
        # Extract text from screenshot
        print("Extracting text from screenshot...")
        extracted_text = screenshot_analyzer.extract_text_with_gemini(screenshot_path)
        
        if not extracted_text:
            error_msg = "Failed to extract text from validation screenshot"
            print(f"Error: {error_msg}")
            return json.dumps({"matches": False, "error": error_msg})
            
        print(f"Successfully extracted text, length: {len(extracted_text)} characters")
        
        # Use Gemini to compare the extracted text with the expected description
        print("Comparing screen content with expected description...")
        comparison_result = screenshot_analyzer.compare_screen_with_description(
            screenshot_path,
            expected_screen_description,
            extracted_text
        )
        
        # Format the result
        result = {
            "matches": comparison_result.get("matches", False),
            "confidence": comparison_result.get("confidence", 0.0),
            "explanation": comparison_result.get("explanation", "No explanation provided"),
            "screenshot_path": screenshot_path,
            "current_screen_text": extracted_text[:300] + "..." if len(extracted_text) > 300 else extracted_text
        }
        
        print(f"Match result: {result['matches']} (Confidence: {result['confidence']})")
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Error in match_screen_with_description: {str(e)}"
        print(f"Exception: {error_msg}")
        return json.dumps({"matches": False, "error": error_msg})

@tool
def press_system_key(key_name: str) -> str:
    """
    Press a system key on the device.
    
    Available keys: home, back, enter, volume_up, volume_down, power
    """
    print(f"\n=== Pressing System Key: {key_name} ===")
    
    # Map key names to key codes
    key_map = {
        "home": 3,
        "back": 4,
        "enter": 66,
        "volume_up": 24,
        "volume_down": 25,
        "power": 26
    }
    
    if key_name not in key_map:
        valid_keys = ", ".join(key_map.keys())
        error_msg = f"Invalid key name: {key_name}. Valid options: {valid_keys}"
        print(f"Error: {error_msg}")
        return error_msg
    
    key_code = key_map[key_name]
    
    try:
        success = device.press_key(key_code)
        
        if success:
            return f"Successfully pressed the {key_name} key"
        else:
            return f"Failed to press the {key_name} key"
            
    except Exception as e:
        error_msg = f"Error pressing key {key_name}: {str(e)}"
        print(f"Exception: {error_msg}")
        return error_msg

@tool
def ask_human_for_help(query: str) -> str:
    """
    Request human assistance and log the conversation. Use this when stuck or need clarification.
    
    Args:
        query: The specific question/request for the human
        
    Returns:
        str: Human's response
    """
    print(f"\n=== HUMAN ASSISTANCE NEEDED ===")
    print(f"Question: {query}")
    
    # Print a visible separator to make the question stand out
    print("\n" + "=" * 60)
    print("🔴 HUMAN ASSISTANCE NEEDED 🔴")
    print(f"Question: {query}")
    print("=" * 60 + "\n")
    
    # Get the human's response
    response = input("Your response: ")
    
    # Print another separator to indicate the end of the human interaction
    print("\n" + "=" * 60)
    print("🟢 HUMAN RESPONSE RECEIVED 🟢")
    print(f"Response: {response}")
    print("=" * 60 + "\n")
    
    # Log the interaction using the new core logger
    log_human_interaction(query, response)
    
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
    # Use the new centralized logging function that always appends
    return log_activity(screen_name, action_description)

@tool
def query_application_knowledge(query: str) -> str:
    """
    Search through past activity logs to answer questions about the application's behavior and history.
    
    This tool analyzes past interactions, screens visited, and actions performed by the agent,
    then uses an LLM to interpret this knowledge and provide a targeted answer to your query.
    
    Args:
        query (str): The specific question about past application behavior or workflow
        
    Returns:
        str: A concise, relevant answer based on past application activities
    """
    print(f"Searching application knowledge for: {query}")
    log_file = os.path.join("activity_logs", "agent_activity_log.jsonl")
    
    # Check if log file exists
    if not os.path.exists(log_file):
        return "No activity logs found to answer your query."
    
    # Read all logs
    activities = []
    with open(log_file, "r") as f:
        for line in f:
            if line.strip():  # Skip empty lines
                try:
                    # Try to parse as JSON
                    log_entry = json.loads(line)
                    activities.append(log_entry)
                except json.JSONDecodeError:
                    # If not JSON, add as plain text entry
                    if not line.startswith("====="):  # Skip separator lines
                        activities.append({"text": line.strip()})
    
    if not activities:
        return "Activity log exists but contains no entries to analyze for your query."
    
    # Format the knowledge context from activities
    knowledge_context = ""
    for entry in activities:
        if isinstance(entry, dict):
            if "timestamp" in entry and "screen" in entry and "action" in entry:
                knowledge_context += f"At {entry['timestamp']}, on screen '{entry['screen']}', action: {entry['action']}\n"
            elif "type" in entry and entry["type"] == "human_interaction":
                knowledge_context += f"Human interaction - Question: {entry.get('request', 'N/A')}, Response: {entry.get('response', 'N/A')}\n"
            elif "text" in entry:
                knowledge_context += f"{entry['text']}\n"
    
    # Generate the answer using LLM
    messages = [
        {"role": "system", "content": "You are an assistant that analyzes Android automation logs to answer specific questions. Use only the information provided in the logs to answer the question. If the logs don't contain relevant information, say that you cannot find the answer in the available logs."},
        {"role": "user", "content": f"Based on the following logs of Android app automation activities, please answer this question: {query}\n\nACTIVITY LOGS:\n{knowledge_context}"}
    ]
    
    try:
        # Use the same LLM that's configured for the main system
        response = llm.invoke(messages)
        answer = response.content
        # print the response from the llm
        print(f"query_application_knowledge Response: {answer}")
        return answer
    except Exception as e:
        print(f"Error using LLM to analyze knowledge: {str(e)}")
        return f"Error analyzing application knowledge: {str(e)}"


# =============================================================================
# AGENT DEFINITIONS
# =============================================================================

# Define tool sets for different agents
interaction_tools = [
    get_screen_data,
    click_grid,
    perform_gesture,
    press_system_key,
    input_text,
    inform_activity,
    query_application_knowledge
]

validation_tools = [
    perform_gesture,
    match_screen_with_description
]

# Action Agent: performs UI interactions
action_agent = create_react_agent(
    llm,
    tools=interaction_tools,
    prompt="""
You are an Action Agent specialized in executing tasks on Android devices using a **ReAct (Reasoning + Acting)** approach. Your primary objective is to analyze the situation, reason about the best course of action, and then execute the necessary steps efficiently.

### **ReAct-Based Workflow**  
For every task, follow this structured approach:  
1. **Observe** – Capture the screen state using `get_screen_data` and analyze full screen completely include all elements.
2. **Reason** – Based on the screen data:
   - Determine the best way to perform the task.
   - Also determine the second best way to perform the task thinking the first way is not possible.
   - let a = confidence_score(your_best_way)
   - let b = confidence_score(your_second_best_way)
   - if a and b values are too close. Use application_workflow knowledge for better reasoning. 
   - if a and b are too low, again use application_workflow knowledge for better reasoning. 
   - if still a and b are too low, ask supervisor for help

3. **Act** – Execute interactions step by step:
   - Tap on elements, perform gestures (`scroll_up`, `swipe_left`, etc.), type text, or press system buttons.
   - If an element is not visible, use gestures to find it before interacting.
   - If an action fails, retry using an alternative approach.  

4. **Verify** – After each action, confirm if the expected result was achieved.
   - If unsuccessful, adjust the approach and try again.
   - If the task is impossible after exhausting all options, report failure.  

### **Constraints**  
- **Never stop** unless all possible interactions have been tried and failed.  
- **Prioritize efficiency and accuracy** in every step.  
- **Prefer clicking on icons** over text elements whenever possible.

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
If the expected state is not observed, report what's actually visible and whether that meets the requirements.
You can also use match_screen_with_description to verify if the current screen matches what is expected.

Be thorough and precise with your observations, reporting exactly what you see.
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
        "Before executing, analyze the user's automation request and create a structured execution plan. Break down the request into clear, step-by-step instructions, specifying actions and expected validation points."
        "Once all steps are verified, respond with FINISH and a summary of the actions taken."
        "Ask for human help if you need feel you are stuck or confused what to do."
    )
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
    
    # Log task completion using the core logger module instead of direct file operations
    # THIS FIXES THE LOGGING ISSUE
    log_task_completion(task_description, result)
    
    return result


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main entry point for the Android automation system."""
    # Check for instruction file
    instruction_file = "instruction.txt"
    if not os.path.exists(instruction_file):
        print(f"Instruction file '{instruction_file}' not found!")
        return 1
    
    # Read instructions
    with open(instruction_file, "r") as f:
        instructions = f.read().strip()
    
    if not instructions:
        print("Instruction file is empty!")
        return 1
    
    print(f"Instructions: {instructions}")
    
    # Run the supervisor
    run_supervisor(instructions)
    
    return 0

if __name__ == "__main__":
    main()
