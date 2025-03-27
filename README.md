# Android Automation Framework

A modular framework for automating Android device interactions using a multi-agent architecture.

## Setup and Installation

1. **Prerequisites**
   - Python 3.11+
   - Android device with USB debugging enabled
   - ADB (Android Debug Bridge) installed

2. **Installation Steps**
   ```bash
   # Clone the repository
   git clone https://github.com/nithinag10/android-adb-api.git
   cd android-adb-api
   
   # Create a Python virtual environment
   python -m venv venv
   
   # Activate the virtual environment
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Environment Setup**
   Create a `.env` file in the project root with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   GEMINI_API_KEY=your_gemini_api_key
   LANGSMITH_API_KEY=your_langsmith_api_key
   ```

## Demo Video
**[Watch the Demo Video](https://drive.google.com/file/d/1L4L13qGXp4e0tNNeFqY8tRW_BdY0wjdD/view?usp=sharing)**

### Demo Preview
![Demo Preview](https://drive.google.com/thumbnail?id=1L4L13qGXp4e0tNNeFqY8tRW_BdY0wjdD)

## Usage

1. **Connect your Android device**
   - Connect your device via USB
   - Enable USB debugging in developer options
   - Verify connection with `adb devices`

2. **Create instruction file**
   Create an `instruction.txt` file with your automation task:
   ```
   1. Open the Settings app
   2. Navigate to Display settings
   3. Enable Dark mode
   ```

3. **Run the automation**
   ```bash
   # Run with default settings
   python run.py
   
   # Run with custom instruction file
   python run.py --instruction-file custom_instructions.txt
   
   # Run with specific OpenAI model
   python run.py --model gpt-4o
   ```

4. **Monitor execution**
   - The system will execute your instructions step by step
   - Activity logs are stored in the `activity_logs` directory
   - Results are stored in the `results` directory

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

## Example Instructions

**Simple Login:**
```
1. Open the app
2. Click on the login button
3. Enter username "testuser" in the username field
4. Enter password "password123" in the password field
5. Click the submit button
```

**App Navigation:**
```
1. Open WhatsApp
2. Find the contact named "John"
3. Send a message saying "Hello, how are you?"
```

## Troubleshooting

- **No devices found**: Ensure USB debugging is enabled and the device is connected
- **API key errors**: Verify your API keys in the `.env` file
- **Execution errors**: Check the activity logs for detailed error information

## License

This project is licensed under the MIT License - see the LICENSE file for details.

