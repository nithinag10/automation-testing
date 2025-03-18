# Android Automation Framework

A modular framework for automating Android device interactions using a multi-agent architecture.

## Overview

This framework provides a robust system for automating interactions with Android devices. It uses a multi-agent architecture to handle complex automation tasks, with specialized agents for different aspects of the automation process.

## Architecture

This project implements a three-layer agent architecture:

1. **Planner Agent** - Reads instructions, breaks them into individual steps, and manages the execution flow
2. **Supervisor Agent** - Implements a StateGraph workflow to coordinate between action and validation agents
3. **Execution Agents**:
   - **Action Agent** - Performs UI interactions on the Android device
   - **Validation Agent** - Verifies the results of actions

The system handles complex multi-step instructions by parsing them into atomic tasks and executing them sequentially, with progress tracking and error handling capabilities.

## Memory System

The project includes a robust memory system that enables agents to:

1. **Store and Parse Instructions** - Break down complex instructions into manageable steps
2. **Track Progress** - Monitor the execution of multi-step tasks
3. **Store Procedural Knowledge** - Remember how to perform specific tasks for future reference
4. **Recall Relevant Information** - Search and retrieve stored knowledge when needed

### Memory Types

- **Instruction Memory**: Stores complex instructions and tracks progress through individual steps
- **Procedural Memory**: Stores knowledge about how to perform specific tasks (e.g., how to log in to an app)

## Project Structure

```
android-adb-api/
├── core/                  # Core functionality modules
│   ├── device_actions.py  # Device interaction methods
│   ├── screenshot_analyzer.py # Screen capture and analysis
│   ├── grid_overlay.py    # Grid overlay for touch coordinates
│   ├── logger.py          # Centralized logging system
│   └── memory_store.py    # Memory management system
├── tools/                 # Tool modules for specific functions
│   ├── device_tools.py    # Device interaction tools
│   ├── screen_tools.py    # Screen capture and analysis tools
│   ├── input_tools.py     # Text input tools
│   ├── validation_tools.py # Validation tools
│   └── knowledge_tools.py # Knowledge query tools
├── utils/                 # Utility modules
│   ├── config.py          # Configuration management
│   └── helpers.py         # Helper functions
├── activity_logs/         # Agent activity logs
├── memory_store/          # Stored memories and instructions
├── results/               # Execution results
├── run.py                 # Main entry point with agent definitions
├── instruction.txt        # Instructions for automation
├── requirements.txt       # Project dependencies
└── README.md              # Project documentation
```

## Core Components

### Device Interaction

The framework provides a comprehensive set of tools for interacting with Android devices:

- **Click Actions**: Precise touch interactions using a grid-based system
- **Gestures**: Swipe and scroll actions
- **Text Input**: Enter text into fields
- **System Keys**: Press hardware and software keys

### Screen Analysis

The framework includes advanced screen analysis capabilities:

- **Screenshot Capture**: Take screenshots of the device
- **Grid Overlay**: Apply a numbered grid to screenshots for precise touch actions
- **Text Extraction**: Extract text from screenshots using Gemini Vision
- **Screen Validation**: Compare screens with expected descriptions

### Logging System

A robust logging system ensures all activities are properly tracked:

- **Activity Logging**: Log all agent activities
- **Human Interaction**: Record conversations with human operators
- **Task Completion**: Log the completion of automation tasks
- **Knowledge Querying**: Search through past logs to answer questions

## Setup and Installation

1. Clone the repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   GEMINI_API_KEY=your_gemini_api_key
   LANGSMITH_API_KEY=your_langsmith_api_key
   ```

## Usage

1. Connect your Android device via USB and enable USB debugging
2. Create an `instruction.txt` file with the automation task
3. Run the main script:
   ```
   python run.py
   ```

### Example Instructions

```
Open the Settings app, navigate to Display settings, and enable Dark mode.
```

```
Open WhatsApp, find the contact named "John", and send a message saying "Hello, how are you?".
```

## Logs and Results

- Activity logs are stored in the `activity_logs` directory
- Results of automation tasks are stored in the `results` directory

## Advanced Features

### Human Assistance

The framework can request human assistance when it encounters situations it cannot handle:

```python
response = ask_human_for_help("I'm not sure which button to press. Can you help?")
```

### Knowledge Querying

The framework can query past activities to answer questions about the application's behavior:

```python
answer = query_application_knowledge("What screens did the agent navigate through during the last task?")
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
