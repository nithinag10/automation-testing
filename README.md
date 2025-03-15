# Android Automation with Multi-Agent Architecture

A powerful Android automation framework that uses a three-layer agent architecture powered by LangGraph and LangChain to automate complex tasks on Android devices.

## Project Overview

This project implements an intelligent automation system for Android devices using a sophisticated multi-agent architecture:

1. **Planner Agent** - Reads instructions, breaks them into individual steps, and manages the execution flow
2. **Supervisor Agent** - Implements a StateGraph workflow to coordinate between action and validation agents
3. **Execution Agents**:
   - **Action Agent** - Performs UI interactions on the Android device
   - **Validation Agent** - Verifies the results of actions

The system handles complex multi-step instructions by parsing them into atomic tasks and executing them sequentially, with progress tracking and error handling capabilities.

## Key Features

- **Natural Language Task Execution**: Execute complex Android tasks described in natural language
- **Visual Understanding**: Uses Gemini Vision to analyze screenshots and understand UI elements
- **Grid-Based Interaction**: Applies a numbered grid overlay to screenshots for precise touch interactions
- **Intelligent Error Recovery**: Automatically detects and attempts to recover from errors during task execution
- **Activity Logging**: Comprehensive logging of all actions and screens for debugging and analysis
- **Knowledge Query System**: Query past automation runs to extract insights and solve similar problems

## Prerequisites

- Python 3.10+
- Android device with USB debugging enabled
- ADB (Android Debug Bridge) installed and configured
- OpenAI API key for LLM capabilities
- Google Gemini API key for vision analysis

## Installation

1. Clone this repository
2. Install the dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file with the following environment variables:

```
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
LANGSMITH_API_KEY=your_langsmith_api_key  # Optional for tracing
```

## Project Structure

- **run.py** - Main entry point and implementation of the multi-agent architecture
- **device_actions.py** - Handles direct interactions with the Android device via UIAutomator2
- **screenshot_analyzer.py** - Captures and analyzes screenshots using Gemini Vision
- **grid_overlay.py** - Applies a numbered grid to screenshots for precise touch interactions
- **activity_logs/** - Directory containing logs of all automation activities
- **results/** - Directory containing the results of supervisor workflows

## Core Components

### Device Actions

The `DeviceActions` class provides methods to interact with Android devices:

- Taking screenshots
- Clicking at specific coordinates
- Swiping and scrolling
- Typing text
- Pressing system keys

### Screenshot Analyzer

The `ScreenshotAnalyzer` class handles:

- Capturing screenshots from the device
- Applying grid overlays for touch precision
- Extracting text and UI elements using Gemini Vision

### Grid Overlay

The `GridOverlay` class:

- Divides the screen into a numbered grid based on finger touch size
- Provides mapping between grid numbers and screen coordinates
- Helps agents precisely identify UI elements by grid position

### Multi-Agent System

The system uses a three-layer agent architecture:

1. **Planner Agent**: Breaks down complex tasks into steps
2. **Supervisor Agent**: Orchestrates the workflow between agents
3. **Execution Agents**:
   - **Action Agent**: Performs the actual device interactions
   - **Validation Agent**: Verifies the results of actions

## Available Tools

The agents have access to the following tools:

- `get_screen_data()` - Captures and analyzes the current screen
- `click_grid(grid_number)` - Clicks at a specific grid position
- `perform_gesture(gesture_type)` - Performs swipe gestures
- `input_text(text)` - Types text on the device
- `press_system_key(key_name)` - Presses system keys like home, back, etc.
- `match_screen_with_description(expected_screen_description)` - Validates the current screen
- `ask_human_for_help(query)` - Requests human assistance when stuck
- `inform_activity(screen_name, action_description)` - Logs the current activity
- `query_application_knowledge(query)` - Searches past activities to answer questions

## Usage

1. Create an instruction file (`instruction.txt`) with the tasks you want to automate:

```
1. open whatsapp
2. open nikhil chat
3. send hello message to him
```

2. Run the automation:

```bash
python run.py
```

3. The system will:
   - Parse the instructions
   - Break them down into steps
   - Execute each step using the appropriate agents
   - Log all activities for future reference

## Logging and Debugging

All automation activities are logged in the `activity_logs/agent_activity_log.jsonl` file. Each log entry contains:

- Timestamp
- Current screen
- Action performed
- Human interactions (if any)

You can query past automation runs using the `query_application_knowledge` tool to extract insights and solve similar problems.

## Example Queries

You can use the `query_application_knowledge` tool to ask questions about past automation runs:

- "What issues occurred during the WhatsApp automation?"
- "How did the agent handle the payment flow in PhonePe?"
- "What screens were visited during the last task?"

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
