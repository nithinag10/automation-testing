#!/usr/bin/env python3
"""
Configuration Module

This module handles loading configuration from environment variables and files.
"""

import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration manager for the Android automation system."""
    
    def __init__(self):
        """Initialize configuration with defaults and environment variables."""
        # Load API keys from environment
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
        
        # Set up paths and directories
        self.activity_log_dir = "activity_logs"
        self.results_dir = "results"
        self.instruction_file = "instruction.txt"
        
        # Ensure required directories exist
        os.makedirs(self.activity_log_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Default device settings
        self.device_id = os.getenv("DEVICE_ID", None)  # Use specific device ID or None for first available
        
        # Agent settings
        self.agent_settings = {
            "planner": {
                "model": os.getenv("PLANNER_MODEL", "gpt-3.5-turbo"),
                "temperature": 0.2
            },
            "supervisor": {
                "model": os.getenv("SUPERVISOR_MODEL", "gpt-3.5-turbo"),
                "temperature": 0.1
            },
            "action": {
                "model": os.getenv("ACTION_MODEL", "gpt-3.5-turbo"),
                "temperature": 0.2
            },
            "validation": {
                "model": os.getenv("VALIDATION_MODEL", "gpt-3.5-turbo"),
                "temperature": 0.1
            }
        }
        
        # Vision model settings
        self.vision_settings = {
            "model": os.getenv("VISION_MODEL", "gemini-pro-vision"),
            "max_tokens": 1024
        }
        
        # Grid overlay settings
        self.grid_settings = {
            "grid_size": 40,  # Size in pixels (average adult finger touch size)
            "grid_color": "red",
            "grid_line_width": 2,
            "grid_number_font_size": 20
        }
    
    def validate(self) -> bool:
        """
        Validate that all required configuration is present.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        if not self.openai_api_key:
            print("ERROR: OPENAI_API_KEY environment variable is not set")
            return False
            
        if not self.gemini_api_key:
            print("ERROR: GEMINI_API_KEY environment variable is not set")
            return False
            
        # Check if instruction file exists
        if not os.path.exists(self.instruction_file):
            print(f"WARNING: Instruction file {self.instruction_file} not found")
            # Still valid, just a warning
            
        return True
    
    def get_agent_settings(self, agent_name: str) -> Dict[str, Any]:
        """
        Get settings for a specific agent.
        
        Args:
            agent_name (str): Name of the agent (planner, supervisor, action, validation)
            
        Returns:
            dict: Agent settings
        """
        if agent_name not in self.agent_settings:
            raise ValueError(f"Unknown agent: {agent_name}")
            
        return self.agent_settings[agent_name]
    
    def get_vision_settings(self) -> Dict[str, Any]:
        """
        Get settings for vision models.
        
        Returns:
            dict: Vision model settings
        """
        return self.vision_settings
    
    def get_grid_settings(self) -> Dict[str, Any]:
        """
        Get settings for grid overlay.
        
        Returns:
            dict: Grid overlay settings
        """
        return self.grid_settings
    
    def __str__(self) -> str:
        """Return string representation of the configuration (with sensitive data redacted)."""
        # Create a copy with API keys redacted
        redacted_config = {
            "API Keys": {
                "OpenAI": "****" if self.openai_api_key else "Not set",
                "Gemini": "****" if self.gemini_api_key else "Not set",
                "LangSmith": "****" if self.langsmith_api_key else "Not set"
            },
            "Directories": {
                "Activity Logs": self.activity_log_dir,
                "Results": self.results_dir
            },
            "Instruction File": self.instruction_file,
            "Device ID": self.device_id or "Using first available device",
            "Agent Settings": self.agent_settings,
            "Vision Settings": self.vision_settings,
            "Grid Settings": self.grid_settings
        }
        
        return json.dumps(redacted_config, indent=2)

# Create a global config instance
config = Config()

# Convenience function to get the configuration
def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Returns:
        Config: Global configuration instance
    """
    return config
