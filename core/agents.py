#!/usr/bin/env python3
"""
Agent Definitions Module

This module defines the agents used in the Android automation system.
"""

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

# Import tools
from tools.screen_tools import get_screen_data
from tools.device_tools import click_grid, perform_gesture, press_system_key
from tools.input_tools import input_text
from tools.validation_tools import match_screen_with_description
from tools.knowledge_tools import query_application_knowledge

# Import custom tools defined in run.py
from core.custom_tools import (
    ask_human_for_help,
    inform_activity,
    store_instruction_steps,
    get_instruction_batch,
    get_all_instructions,
    get_navigation_recovery_plan
)

def create_agents(llm):
    """
    Create the agents used in the Android automation system.
    
    Args:
        llm: The language model to use for the agents
        
    Returns:
        Tuple containing (action_agent, validation_agent, tool_sets)
    """
    # Define tool sets for different agents
    interaction_tools = [
        get_screen_data,
        click_grid,
        perform_gesture,
        press_system_key,
        input_text,
        inform_activity,
        query_application_knowledge,
        get_navigation_recovery_plan
    ]

    validation_tools = [
        perform_gesture,
        match_screen_with_description
    ]

    # Supervisor instruction management tools
    instruction_management_tools = [
        store_instruction_steps,
        get_instruction_batch,
        get_all_instructions,
        get_navigation_recovery_plan
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
   - Tap on elements, perform gestures (`scroll_up`, `swipe_left`, etc.), type text (first click and then enter text), or press system buttons.
   - If an element is not visible, use gestures to find it before interacting.
   - If an action fails, retry using an alternative approach. 
   - If you find any obstacles, like popups, unexpected notification or any unexpected screen handle it by yourself.
   - Use inform_activity tool to log your every small activity and actions.
   - Ask human help if there is any login required.
   - Plan your own action plan if required to handle unexpected flow. 
   - If actions are not working, ask supervisor for validation than proceeding to the next steps. 

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

    # Validation Agent: validates the results of actions
    validation_agent = create_react_agent(
        llm,
        tools=validation_tools,
        prompt="""
You are a Validation Agent specialized in verifying the success of tasks performed on Android devices.

Your primary objective is to analyze the screen after an action has been performed and provide a clear yes/no determination if the expected outcome has been achieved.

### Your workflow:
1. Analyze the expected result description
2. Capture and analyze the current screen using match_screen_with_description
3. Make a clear determination if the success criteria have been met
4. If validation fails, suggest potential reasons and recovery actions

### Key responsibilities:
- Provide clear, binary success/failure determinations
- Use detailed reasoning to explain why something succeeded or failed
- Consider both exact matches and approximate equivalents (e.g., slightly different phrasing but same meaning)
- If screen data is unclear, use gestures to explore more before declaring failure
- Consider app state transitions and loading times

Your validations are critical for error recovery and workflow progression.
""",
        name="validation_agent"
    )
    
    return (
        action_agent, 
        validation_agent, 
        {
            "interaction_tools": interaction_tools,
            "validation_tools": validation_tools,
            "instruction_management_tools": instruction_management_tools
        }
    )
