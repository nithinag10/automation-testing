#!/usr/bin/env python3
"""
Custom Tools Module

This module defines custom tools that aren't part of the standard device interaction tools.
"""

import os
import json
from typing import Optional, Dict, List, Any
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

# Import from core modules
from core.logger import log_activity, log_human_interaction
from core.instruction_manager import instruction_manager

# Initialize LLM for knowledge tools
llm = ChatOpenAI(model="gpt-4o", temperature=0)

@tool
def ask_human_for_help(query: str) -> str:
    """
    Request human assistance and log the conversation. Use this when stuck or need clarification.
    Ask human assistance if there is any login credentials needed for you to move forward.
    
    Args:
        query: The specific question/request for the human
        
    Returns:
        str: Human's response
    """
    print("\n=== Requesting Human Assistance ===")
    print(f"Question: {query}")
    
    # Get user input
    print("\nPlease provide your response (type your answer and press Enter):")
    response = input("> ")
    
    print(f"Human response received: {response}")
    
    # Log the interaction
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
    # Use the centralized logging function that always appends
    return log_activity(screen_name, action_description)

@tool
def store_instruction_steps(instructions: str) -> str:
    """
    Parse a lengthy instruction set into individual steps and store them.
    
    This tool breaks down a multi-step instruction into individual tasks and stores them
    in a structured format. It's designed to help manage complex automation workflows
    that would otherwise exceed the context window of the agent.
    
    Args:
        instructions (str): A multi-line string with numbered instruction steps
        
    Returns:
        str: Confirmation message with the number of steps stored
    """
    return instruction_manager.store_instruction_steps(instructions)

@tool
def get_instruction_batch(instruction_id: Optional[int] = None, batch_size: int = 4) -> str:
    """
    Retrieve a batch of instruction steps starting from the specified instruction ID.
    If no instruction ID is provided, retrieve the first batch of instructions.
    
    This tool retrieves 4 instruction steps at a time to prevent overwhelming 
    the agent's context window while maintaining meaningful task context.
    
    Args:
        instruction_id (Optional[int]): The ID of the instruction to start from (default: None)
        batch_size (int): Number of instruction steps to retrieve (default: 3)
        
    Returns:
        str: A formatted string containing the batch of instructions and metadata
    """
    result = instruction_manager.get_instruction_batch(instruction_id, batch_size)
    
    if "error" in result:
        return result["error"]
    
    # Format the output as a string
    output = f"Instruction Batch ({result['batch_size']} steps, {result['start_id']} to {result['end_id']}):\n\n"
    
    for i, step in enumerate(result["batch"]):
        output += f"{i+1}. Step {step['step_id']}: {step['instruction']}\n"
    
    output += f"\nTotal Steps: {result['total_steps']}"
    if result["has_more"]:
        output += f"\nMore instructions available. For next batch, use instruction_id={result['end_id'] + 1}"
    
    return output

@tool
def get_all_instructions() -> str:
    """
    Get the complete set of instruction steps.
    
    This tool returns all instructions and their details, providing a complete overview
    of the entire task. Use this when you need to see the big picture of what needs to 
    be accomplished.
    
    Returns:
        str: A formatted list of all instruction steps
    """
    result = instruction_manager.get_all_instructions()
    
    if "error" in result:
        return result["error"]
    
    steps = result["steps"]
    total_steps = result["total_steps"]
    
    output = f"All Instructions ({total_steps} steps):\n\n"
    
    for step in steps:
        output += f"Step {step['step_id']}: {step['instruction']}\n"
    
    return output

@tool
def get_navigation_recovery_plan(current_screen: str) -> str:
    """
    Analyze past navigation patterns to provide a recovery plan when the agent encounters an
    unknown or unexpected screen.
    
    This tool searches through activity logs to find navigation patterns and screen transitions,
    then provides step-by-step instructions to return to a known state or familiar screen.
    It also considers the current instruction context to provide more relevant recovery options.
    
    Args:
        current_screen (str): The name or description of the current unknown screen
        
    Returns:
        str: A detailed recovery plan with navigation steps to return to a known screen
    """
    print(f"Generating navigation recovery plan from screen: {current_screen}")
    log_file = os.path.join("activity_logs", "agent_activity_log.jsonl")
    
    # Check if log file exists
    if not os.path.exists(log_file):
        return "No activity logs found to generate a recovery plan."
    
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
                    # Skip non-JSON entries for this analysis
                    pass
    
    if not activities:
        return "Activity log exists but contains no structured entries to analyze for navigation patterns."
    
    # Extract navigation sequences (screen transitions)
    screen_transitions = []
    for i in range(len(activities)):
        entry = activities[i]
        if isinstance(entry, dict) and "screen" in entry and "action" in entry:
            # Track the screen, action, and next screen (if available)
            next_screen = None
            for j in range(i + 1, len(activities)):
                if isinstance(activities[j], dict) and "screen" in activities[j]:
                    next_screen = activities[j]["screen"]
                    break
            
            screen_transitions.append({
                "screen": entry["screen"],
                "action": entry["action"],
                "next_screen": next_screen
            })
    
    # Format the navigation history for the LLM
    navigation_history = ""
    for transition in screen_transitions:
        if transition["next_screen"]:
            navigation_history += f"From '{transition['screen']}', action: {transition['action']}, led to: '{transition['next_screen']}'\n"
        else:
            navigation_history += f"On '{transition['screen']}', action: {transition['action']}\n"
    
    # Common navigation patterns: identify home screens and common navigation actions
    common_screens = {}
    for transition in screen_transitions:
        screen = transition["screen"]
        if screen in common_screens:
            common_screens[screen] += 1
        else:
            common_screens[screen] = 1
    
    # Sort screens by frequency
    frequent_screens = sorted(common_screens.items(), key=lambda x: x[1], reverse=True)
    frequent_screens_str = "\n".join([f"'{screen}': visited {count} times" for screen, count in frequent_screens[:5]])
    
    # Get current instruction context
    instruction_context = ""
    try:
        # Get all instructions to understand the overall task
        all_instructions = get_all_instructions()
        
        # Try to determine which instruction step we might be on
        # Look for the most recent activity log entries with instruction references
        current_instruction_id = None
        current_step_number = None
        
        for entry in reversed(activities):
            if isinstance(entry, dict) and "instruction_id" in entry:
                current_instruction_id = entry.get("instruction_id")
                current_step_number = entry.get("step_number")
                break
        
        # Format instruction context
        if all_instructions:
            instruction_context += "Overall task instructions:\n"
            instruction_context += all_instructions
        
        # Add information about the current/last known instruction step
        if current_instruction_id is not None and current_step_number is not None:
            instruction_context += f"\nCurrent/last known instruction step: {current_step_number}\n"
            
            # Get the next few steps to help with recovery planning
            try:
                next_batch = get_instruction_batch(current_instruction_id)
                if next_batch:
                    instruction_context += "Upcoming instruction steps:\n"
                    instruction_context += next_batch
            except Exception as e:
                print(f"Error getting next instruction batch: {str(e)}")
    except Exception as e:
        print(f"Error retrieving instruction context: {str(e)}")
        instruction_context = "Unable to retrieve instruction context."
    
    # Generate the recovery plan using LLM
    messages = [
        {"role": "system", "content": 
         "You are an Android navigation expert specializing in app recovery. Your task is to help an automation agent " +
         "backtrack from an unknown screen to a known, familiar screen based on past navigation patterns and current task context. " +
         "Provide concise, clear steps focusing on using universal navigation actions like pressing the back button, " +
         "going to the home screen, or reopening the app. If you detect a pattern where certain screens consistently " +
         "follow specific actions, use this knowledge to guide the recovery. " +
         "Consider the current instruction steps to provide recovery options that help the agent continue its task."
        },
        {"role": "user", "content": 
         f"I'm currently on an unknown screen described as: '{current_screen}'\n\n" +
         f"Here's the navigation history from past app interactions:\n{navigation_history}\n\n" +
         f"Most frequently visited screens:\n{frequent_screens_str}\n\n" +
         f"Instruction context:\n{instruction_context}\n\n" +
         "Please provide a step-by-step recovery plan to get back to a familiar screen, " +
         "prioritizing reliable methods like pressing the back button, going to the home screen, " +
         "or reopening the app. Consider the current task instructions to suggest the most relevant " +
         "recovery path that will help continue the task. Include clear reasoning for each step."
        }
    ]
    
    try:
        # Use the same LLM that's configured for the main system
        response = llm.invoke(messages)
        recovery_plan = response.content
        print(f"Navigation Recovery Plan: {recovery_plan}")
        return recovery_plan
    except Exception as e:
        print(f"Error generating navigation recovery plan: {str(e)}")
        return f"Error generating navigation recovery plan: {str(e)}"
