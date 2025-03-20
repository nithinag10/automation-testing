#!/usr/bin/env python3
"""
Workflow Module

This module defines the supervisor workflow used to coordinate the agents.
"""

import os
import json
from typing import Dict, Any, List, Optional
import datetime

from langgraph.graph import StateGraph, END, START
from langgraph_supervisor import create_supervisor
from langchain_core.messages import HumanMessage

from core.logger import log_task_completion

def create_supervisor_workflow(action_agent, validation_agent, tools, llm, name="supervisor_agent"):
    """
    Create the supervisor workflow that coordinates the action and validation agents.
    
    Args:
        action_agent: The action agent instance
        validation_agent: The validation agent instance
        tools: List of additional tools to provide to the supervisor
        llm: The language model to use
        name: The name of the supervisor workflow
        
    Returns:
        The compiled supervisor workflow
    """
    # Create the supervisor workflow
    supervisor_workflow = create_supervisor(
        agents=[action_agent, validation_agent],
        tools=tools,
        model=llm,
        prompt="""
You are the Supervisor Agent for an Android Automation system. Your role is to coordinate and oversee the execution of automation tasks by delegating to specialized agents:

1. Action Agent - Capable of performing UI interactions (clicks, text input, swipes)
2. Validation Agent - Verifies if actions were successful based on screen results

Instructions:
- First, understand the task thoroughly and break it into logical steps.
- For each step, delegate to the Action Agent for execution, then the Validation Agent to confirm success.
- The validation agent will inform you if the expected outcome was achieved.
- If validation fails, retry the action with adjusted parameters or an alternative approach.
- Maintain context across the entire workflow, remembering previous screens and actions.
- You can retrieve detailed instructions in batches using instruction management tools.
- If the agents get stuck or encounter unexpected screens, use the navigation recovery tool.
- When human assistance is required, use the ask_human_for_help tool directly.

Remember:
- You have access to instruction management tools to handle complex multi-step tasks.
- Always keep track of the current instruction step being executed.
- If a screen doesn't match expectations, use the get_navigation_recovery_plan tool.
- Apply knowledge from past activities using the query_application_knowledge tool.
- Use human assistance sparingly and only when automated recovery fails.
"""
    )
    
    return supervisor_workflow.compile()

def stream_workflow_execution(compiled_supervisor, task_description, log_directory="activity_logs"):
    """
    Execute the supervisor workflow with a traditional approach.
    
    Args:
        compiled_supervisor: The compiled supervisor workflow
        task_description: The automation task to perform
        log_directory: Directory for storing logs
        
    Returns:
        The final state of the workflow
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

    # Create logs directory if it doesn't exist
    os.makedirs(log_directory, exist_ok=True)
    
    # Timestamp for this session
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Log file for this session - use append mode instead of write mode to fix logging issue
    log_file = os.path.join(log_directory, f"activity_log_{timestamp}.txt")
    
    # Open log file in append mode (not overwrite mode)
    with open(log_file, "a") as f:
        f.write(f"=== Task Description ===\n{task_description}\n\n")

    # Run the supervisor workflow
    print("\n=== Running Supervisor Workflow ===")
    
    try:
        # Invoke the workflow directly without streaming
        final_output = compiled_supervisor.invoke(initial_input, config)
        
        # Log the task completion
        log_task_completion(task_description, final_output, log_directory)
        
        print("\n=== Supervisor Execution Complete ===")
        
        # Store the supervisor result in a JSON file
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        result_file = os.path.join(results_dir, f"supervisor_result_{timestamp}.json")
        
        with open(result_file, "w") as f:
            json.dump(final_output, f, indent=2, default=lambda o: o.__dict__)
            
        return final_output
    except Exception as e:
        print(f"Error during workflow execution: {e}")
        raise
