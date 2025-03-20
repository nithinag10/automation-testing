#!/usr/bin/env python3
"""
Android Automation System

Main entry point for the Android automation system with multi-agent architecture.
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Import core modules
from core.agents import create_agents
from core.workflow import create_supervisor_workflow, stream_workflow_execution
from core.custom_tools import ask_human_for_help

def main():
    """Main entry point for the Android automation system."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Android Automation System")
    parser.add_argument("--instruction-file", type=str, default="instruction.txt", 
                        help="Path to instruction file")
    parser.add_argument("--model", type=str, default="gpt-4o",
                        help="OpenAI model to use")
    parser.add_argument("--temperature", type=float, default=0,
                        help="Temperature for the LLM")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Check for OpenAI API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable is required")
        return 1
    
    # Check for instruction file
    instruction_file = args.instruction_file
    if not os.path.exists(instruction_file):
        print(f"Error: Instruction file '{instruction_file}' not found!")
        return 1
    
    # Read instructions
    with open(instruction_file, "r") as f:
        instructions = f.read().strip()
    
    if not instructions:
        print("Error: Instruction file is empty!")
        return 1
    
    print(f"Instructions: {instructions}")
    
    # Initialize LLM
    llm = ChatOpenAI(model=args.model, temperature=args.temperature)
    
    # Create agents
    action_agent, validation_agent, tool_sets = create_agents(llm)
    
    # Create supervisor workflow
    compiled_supervisor = create_supervisor_workflow(
        action_agent=action_agent,
        validation_agent=validation_agent,
        tools=[ask_human_for_help] + tool_sets["instruction_management_tools"],
        llm=llm
    )
    
    # Execute the workflow with streaming
    try:
        stream_workflow_execution(
            compiled_supervisor=compiled_supervisor,
            task_description=instructions
        )
        return 0
    except Exception as e:
        print(f"Error executing workflow: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
