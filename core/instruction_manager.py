"""
Instruction Manager for Android Automation

This module provides functionality to manage lengthy instruction sets
by breaking them down into individual steps and managing their execution flow.
"""

import os
import json
from typing import Dict, List, Any, Optional

# Import logger from core
from core.logger import log_activity

class InstructionManager:
    """Manages multi-step instructions for the automation supervisor."""
    
    def __init__(self):
        """Initialize the instruction manager."""
        self.instruction_store_path = "instruction_steps.json"
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure necessary directories exist."""
        # No need to create directories for a file in the current directory
        # Just ensure results directory exists for other operations
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
    
    def store_instruction_steps(self, instructions: str) -> str:
        """
        Parse a lengthy instruction set into individual steps and store them.
        
        Args:
            instructions (str): A multi-line string with numbered instruction steps
            
        Returns:
            str: Confirmation message with the number of steps stored
        """
        print("\n=== Storing Instruction Steps in Memory ===")
        
        try:
            # Simple parsing logic to extract numbered steps
            lines = instructions.strip().split('\n')
            steps = []
            current_step = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check if this is a new numbered step
                if line[0].isdigit() and '.' in line[:3]:
                    if current_step:
                        steps.append(current_step)
                    step_num = line.split('.')[0].strip()
                    step_text = line[len(step_num)+1:].strip()
                    current_step = {
                        "step_id": int(step_num),
                        "instruction": step_text
                    }
                elif current_step:
                    # Continue previous step with additional details
                    current_step["instruction"] += " " + line
            
            # Add the last step if there is one
            if current_step:
                steps.append(current_step)
                
            # Sort steps by step_id to ensure correct order
            steps.sort(key=lambda x: x["step_id"])
            
            # Store steps in a file for persistence
            instruction_data = {
                "steps": steps, 
                "total_steps": len(steps)
            }
            
            with open(self.instruction_store_path, "w") as f:
                json.dump(instruction_data, f, indent=2)
                
            log_activity("instruction_parser", f"Parsed and stored {len(steps)} instruction steps")
            
            return f"Successfully parsed and stored {len(steps)} instruction steps."
            
        except Exception as e:
            error_msg = f"Error storing instruction steps: {str(e)}"
            print(f"Error: {error_msg}")
            return error_msg
    
    def get_instruction_batch(self, instruction_id: Optional[int] = None, batch_size: int = 3) -> Dict[str, Any]:
        """
        Retrieve a batch of instruction steps starting from the specified instruction ID.
        If no instruction ID is provided, retrieve the first batch of instructions.
        
        Args:
            instruction_id (Optional[int]): The ID of the instruction to start from (default: None)
            batch_size (int): Number of instruction steps to retrieve (default: 3)
            
        Returns:
            Dict[str, Any]: A dictionary containing the instruction batch and metadata
        """
        print(f"\n=== Retrieving Instruction Batch ===")
        
        try:
            if not os.path.exists(self.instruction_store_path):
                return {"error": "No instruction steps have been stored. Use store_instruction_steps first."}
                
            # Load the instruction data
            with open(self.instruction_store_path, "r") as f:
                instruction_data = json.load(f)
                
            steps = instruction_data["steps"]
            total_steps = instruction_data["total_steps"]
            
            # Find the starting index based on instruction_id
            start_index = 0
            if instruction_id is not None:
                # Find the step with the matching ID
                for i, step in enumerate(steps):
                    if step["step_id"] == instruction_id:
                        start_index = i
                        break
            
            # Calculate the end index
            end_index = min(start_index + batch_size, total_steps)
            
            # Extract the batch of instructions
            instruction_batch = steps[start_index:end_index]
            
            # Format response
            response = {
                "batch": instruction_batch,
                "batch_size": len(instruction_batch),
                "start_id": steps[start_index]["step_id"] if start_index < total_steps else None,
                "end_id": steps[end_index-1]["step_id"] if end_index > 0 and end_index <= total_steps else None,
                "total_steps": total_steps,
                "has_more": end_index < total_steps
            }
            
            log_activity("instruction_execution", f"Retrieved instruction batch starting from ID {instruction_id if instruction_id is not None else 'first step'}")
            
            return response
            
        except Exception as e:
            error_msg = f"Error retrieving instruction batch: {str(e)}"
            print(f"Error: {error_msg}")
            return {"error": error_msg}
    
    def get_all_instructions(self) -> Dict[str, Any]:
        """
        Get all instruction steps.
        
        Returns:
            Dict: The complete instruction set
        """
        if not os.path.exists(self.instruction_store_path):
            return {"error": "No instruction steps have been stored."}
            
        try:
            with open(self.instruction_store_path, "r") as f:
                return json.load(f)
        except Exception as e:
            return {"error": f"Error retrieving instructions: {str(e)}"}

# Create a singleton instance
instruction_manager = InstructionManager()
