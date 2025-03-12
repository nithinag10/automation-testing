# Android ADB API with LangGraph Supervisor

This project implements an Android device automation system using LangGraph's Supervisor pattern. The system allows you to automate tasks on Android devices using natural language instructions.

## Features

- **LangGraph Supervisor Architecture**: Uses the `create_supervisor` function to manage specialized agents
- **Multi-Agent System**: Includes action and validation agents with specific responsibilities
- **Screenshot Analysis**: Captures and analyzes screenshots with a grid overlay for precise touch targets
- **Device Interaction**: Supports clicking, swiping, typing, and pressing system keys
- **Memory Management**: Includes short-term and long-term memory for the multi-agent system

## Requirements

- Python 3.10+
- Android device connected via ADB
- OpenAI API key

## Installation

1. Install the required packages:

```bash
pip install -r requirements.txt
```

2. Set up your environment variables by creating a `.env` file:

```
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key  # Optional, for screenshot analysis
```

## Usage

1. Connect your Android device via ADB
2. Run the supervisor application:

```bash
python supervisor_app.py
```

3. Enter your automation task when prompted

## Architecture

The system uses LangGraph's Supervisor pattern to manage two specialized agents:

1. **Action Agent**: Performs actions on the device (clicking, swiping, typing)
2. **Validation Agent**: Verifies that actions were successful

The supervisor decides which agent to use based on the current task and coordinates their work.

## Implementation Details

- **Screen Resolution**: 1080x2400 pixels (as specified in memory)
- **Pixel Density**: 405 PPI (as specified in memory)
- **Touch Target Size**: 7mm grid overlay for precise interactions
- **Screenshot Method**: Uses `adb exec-out screencap -p` for reliable screenshots (as specified in memory)

## Comparing with Previous Implementation

The new supervisor implementation offers several advantages over the previous approach:

1. **Simplified Architecture**: Uses the `create_supervisor` function for cleaner code
2. **Full Message History**: Maintains the complete conversation history between agents
3. **Memory Management**: Includes checkpointing and state storage
4. **Easier Extension**: Simpler to add new specialized agents

## Example Tasks

- "Open the Settings app and turn on Airplane mode"
- "Take a screenshot, analyze it, and tell me what apps are visible"
- "Open the browser and search for 'Android automation'"

## Customization

You can modify the `instruction.txt` file to provide specific guidance for your automation tasks.
