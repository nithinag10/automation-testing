# Android Automation Project - Modular Structure

This document outlines the modular structure of the Android Automation project, which has been organized to improve maintainability and clarity.

## Project Structure

```
android-adb-api/
├── core/                  # Core functionality modules
│   ├── device_actions.py  # Device interaction methods
│   ├── screenshot_analyzer.py # Screen capture and analysis
│   ├── grid_overlay.py    # Grid overlay for touch coordinates
│   └── logger.py          # Centralized logging system
├── tools/                 # Tool modules for specific functions
│   ├── device_tools.py    # Device interaction tools
│   ├── screen_tools.py    # Screen capture and analysis tools
│   ├── input_tools.py     # Text input tools
│   ├── validation_tools.py # Validation tools
│   └── knowledge_tools.py # Knowledge query tools
├── utils/                 # Utility modules
│   ├── config.py          # Configuration management
│   └── helpers.py         # Helper functions
├── run.py                 # Main entry point with agent definitions
├── instruction.txt        # Instructions for automation
├── requirements.txt       # Project dependencies
└── README.md              # Project documentation
```

## Module Descriptions

### Core Modules

1. **device_actions.py**
   - Provides the `DeviceActions` class for interacting with Android devices
   - Handles connections to devices and error management
   - Implements methods for clicking, swiping, and inputting text

2. **screenshot_analyzer.py**
   - Provides the `ScreenshotAnalyzer` class for capturing and analyzing screenshots
   - Integrates with Gemini Vision for text extraction
   - Implements methods for comparing screens with expected descriptions

3. **grid_overlay.py**
   - Provides the `GridOverlay` class for adding a numbered grid to screenshots
   - Maps grid numbers to screen coordinates for precise touch actions
   - Helps identify specific touch areas on the device screen

4. **logger.py**
   - Implements a centralized logging system
   - Ensures logs are preserved throughout execution
   - Provides functions for logging activities, human interactions, and task completions

### Tool Modules

1. **device_tools.py**
   - Implements tools for clicking, performing gestures, and pressing system keys
   - Provides a high-level interface for device interactions

2. **screen_tools.py**
   - Implements tools for capturing and analyzing device screens
   - Provides methods for applying grid overlays and extracting text

3. **input_tools.py**
   - Implements tools for entering text on the device
   - Handles text input for various fields

4. **validation_tools.py**
   - Implements tools for verifying action results
   - Checks if screens match expected states

5. **knowledge_tools.py**
   - Implements tools for querying past automation knowledge
   - Utilizes LLM for analysis and response generation

### Utility Modules

1. **config.py**
   - Manages configuration settings
   - Loads environment variables and provides access to configuration values

2. **helpers.py**
   - Provides utility functions for timestamps, file operations, and formatting
   - Implements helper methods used across the application

## Main Run Script

The `run.py` file serves as the main entry point for the Android automation system. It:

1. Defines the agent architecture:
   - Action Agent: Performs UI interactions on the Android device
   - Validation Agent: Verifies the results of actions
   - Supervisor Agent: Coordinates between action and validation agents

2. Implements the workflow using LangGraph's StateGraph
   - Manages transitions between planning, executing, validating, and handling errors
   - Provides conditional routing based on validation results

3. Defines tool functions that agents can use
   - Screen data retrieval
   - Grid-based clicking
   - Gesture performance
   - Text input
   - System key presses
   - Human assistance
   - Activity logging
   - Knowledge querying

## Logging System

The logging system has been improved to ensure all logs are preserved throughout execution:

1. The `inform_activity` function uses the centralized logger to append to the log file
2. The `run_supervisor` function uses the logger to record task completion without overwriting previous logs
3. All logs are stored in the `activity_logs` directory in JSONL format

## Usage

To run the Android automation system:

1. Create an `instruction.txt` file with the automation task
2. Run the main script: `python run.py`
3. The system will execute the task and log the results

For more details, refer to the README.md file.
