#!/usr/bin/env python3
"""
Logger Module

This module provides centralized logging functionality for the Android automation system.
It ensures all activities are properly logged and preserved throughout execution.
"""

import os
import json
import datetime
from typing import Dict, Any, Optional

class Logger:
    """
    Centralized logger for the Android automation system.
    
    This class handles all logging operations, ensuring that logs are properly
    formatted and stored in the correct location. It addresses the previous
    issue where logs were being overwritten by always using append mode.
    """
    
    def __init__(self, log_dir="activity_logs"):
        """
        Initialize the Logger.
        
        Args:
            log_dir (str): Directory where logs should be stored
        """
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, "agent_activity_log.jsonl")
        
    def log_activity(self, screen_name: str, action_description: str) -> str:
        """
        Log an agent activity.
        
        Args:
            screen_name (str): The current screen name
            action_description (str): Description of the action being performed
            
        Returns:
            str: Formatted activity message
        """
        # Prepare log entry
        timestamp = datetime.datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "screen": screen_name,
            "action": action_description
        }
        
        # Append to log file (always in append mode)
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        # Format message for user feedback
        accessibility_message = f"Screen: {screen_name} | Action: {action_description}"
        print(f"\n[ACTIVITY TRACKER] {accessibility_message}\n")
        
        return accessibility_message
        
    def log_human_interaction(self, request: str, response: str) -> None:
        """
        Log a human interaction.
        
        Args:
            request (str): The request made to the human
            response (str): The human's response
        """
        # Prepare log entry
        timestamp = datetime.datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "type": "human_interaction",
            "request": request,
            "response": response
        }
        
        # Append to log file (always in append mode)
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        print(f"\n[HUMAN INTERACTION] Request: {request}\nResponse: {response}\n")
        
    def log_task_completion(self, task_description: str, result: Optional[Dict[str, Any]] = None) -> None:
        """
        Log task completion.
        
        This method always uses append mode to ensure previous logs are not overwritten.
        
        Args:
            task_description (str): Description of the completed task
            result (dict, optional): Result data from the task
        """
        timestamp = datetime.datetime.now().isoformat()
        
        # Always use append mode to preserve existing logs
        with open(self.log_file, "a") as f:
            f.write(f"AUTOMATION TASK: {task_description}\n")
            f.write(f"COMPLETED AT: {timestamp}\n")
            f.write("=======================================================\n")
            
            # Log the result if provided
            if result:
                f.write("SUPERVISOR RESULT:\n")
                f.write(json.dumps(result, indent=2, default=lambda o: o.__dict__) + "\n")
                f.write("=======================================================\n\n")
        
        print(f"Automation task completed and logged to {self.log_file}")
        
    def query_logs(self, query: str = None) -> str:
        """
        Query the logs and return matching entries.
        
        Args:
            query (str, optional): Query to filter logs
            
        Returns:
            str: JSON string of matching log entries
        """
        # Check if log file exists
        if not os.path.exists(self.log_file):
            return "No activity logs found."
        
        # Read all logs
        activities = []
        with open(self.log_file, "r") as f:
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
            return "Activity log exists but contains no entries."
        
        # Format the result
        result = {
            "total_activities": len(activities),
            "workflow": activities
        }
        
        return json.dumps(result, indent=2)

# Create a global logger instance
logger = Logger()

# Convenience functions
def log_activity(screen_name: str, action_description: str) -> str:
    return logger.log_activity(screen_name, action_description)

def log_human_interaction(request: str, response: str) -> None:
    return logger.log_human_interaction(request, response)

def log_task_completion(task_description: str, result: Optional[Dict[str, Any]] = None) -> None:
    return logger.log_task_completion(task_description, result)

def query_logs(query: str = None) -> str:
    return logger.query_logs(query)
