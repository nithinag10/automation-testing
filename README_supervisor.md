# Android ADB API with LangGraph Supervisor

This project implements an Android device automation system that allows you to automate tasks on Android devices using natural language instructions.

## Prerequisites

- Python 3.10+
- Android device with USB debugging enabled
- ADB (Android Debug Bridge) installed
- OpenAI API key

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/android-adb-api.git
   cd android-adb-api
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your_openai_api_key
   GEMINI_API_KEY=your_gemini_api_key  # Optional, for screenshot analysis
   LANGSMITH_API_KEY=your_langsmith_api_key  # Optional, for tracing
   ```

## Usage

1. **Connect your Android device**
   - Connect your device via USB
   - Enable USB debugging in developer options
   - Verify connection with `adb devices`

2. **Run the application**
   ```bash
   python main.py
   ```

3. **Using instruction files**
   You can create an instruction file with numbered steps:
   ```
   1. Open the Settings app
   2. Navigate to Display settings
   3. Toggle Dark mode
   4. Return to the home screen
   ```

   Then run:
   ```bash
   python main.py --instruction-file your_instructions.txt
   ```

4. **Command-line options**
   ```bash
   # Run with a specific model
   python main.py --model gpt-4o
   
   # Run with verbose logging
   python main.py --verbose
   
   # Run with a specific instruction
   python main.py --instruction "Open the calculator app and perform 2+2"
   ```

## Troubleshooting

- **No devices found**: Ensure USB debugging is enabled and the device is properly connected
- **API key errors**: Verify your API keys in the `.env` file
- **Execution errors**: Check the activity logs in the `activity_logs` directory

## Log Files

- Activity logs are stored in the `activity_logs` directory
- Screenshots are saved in the `screenshots` directory
- Execution results are stored in the `results` directory

## License

This project is licensed under the MIT License - see the LICENSE file for details.
