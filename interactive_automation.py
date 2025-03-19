#!/usr/bin/env python3
"""
Interactive Android Automation with React Agent
"""

# =============================================================================
# IMPORTS AND CONFIGURATION
# =============================================================================
import os
import json
import time
import datetime
import http.server
import socketserver
import threading
import webbrowser
import urllib.parse
from typing import Dict, Any, List, Optional
from pathlib import Path
from langchain.schema import HumanMessage
from langchain_core.tools import tool, Tool
from langchain_openai import ChatOpenAI

# Import core modules
from core.device_actions import DeviceActions
from core.screenshot_analyzer import ScreenshotAnalyzer
from core.grid_overlay import GridOverlay
from core.logger import log_activity, log_task_completion
LANGCHAIN_AVAILABLE = True

try:
    from langgraph.prebuilt import create_react_agent
    from langchain_core.tools import tool, Tool
    LANGGRAPH_AVAILABLE = True
    print("LangGraph is available.")
except ImportError:
    print("Warning: LangGraph not available. React agent capabilities will be limited.")
    LANGGRAPH_AVAILABLE = False

# Global reference to the interactive automation instance
# This will be set when the instance is created
_automation_instance = None

@tool
def analyze_screen() -> str:
    """Analyze the current screen to extract text and identify UI elements."""
    global _automation_instance
    if not _automation_instance:
        return "Error: Automation system not initialized"
    return _automation_instance._analyze_screen_impl()

@tool
def click_grid(grid_number: str) -> str:
    """Click on a specific grid number on the screen."""
    global _automation_instance
    if not _automation_instance:
        return "Error: Automation system not initialized"
    return _automation_instance._click_grid_impl(grid_number)

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler to handle form submissions and display screenshots"""
    
    def __init__(self, *args, directory=None, automation_instance=None, **kwargs):
        """Initialize the HTTP request handler"""
        # Store the automation instance
        self.automation_instance = automation_instance
        
        # Store the directory for logging purposes
        self.base_directory = kwargs.get('directory', os.getcwd())
        super().__init__(*args, **kwargs)
        
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            # Debug logging - remove in production
            print(f"GET request for path: {self.path}")
            
            # Redirect root to the viewer page
            if self.path == "/":
                if self.automation_instance and hasattr(self.automation_instance, 'session_id'):
                    session_path = f"/session_{self.automation_instance.session_id}/viewer/index.html"
                    self.send_response(302)
                    self.send_header("Location", session_path)
                    self.end_headers()
                    print(f"Redirecting to: {session_path}")
                    return
                else:
                    # If no automation instance, just try to serve index.html
                    self.path = "/index.html"
            
            # Special handling for /viewer/index.html
            if self.path == "/viewer/index.html" and self.automation_instance:
                # Redirect to the correct session path
                session_path = f"/session_{self.automation_instance.session_id}/viewer/index.html"
                self.send_response(302)
                self.send_header("Location", session_path)
                self.end_headers()
                print(f"Redirecting /viewer/index.html to: {session_path}")
                return
            
            # Add CORS headers for local testing
            # Handle standard GET requests
            super().do_GET()
        except BrokenPipeError:
            # Client disconnected, this is normal behavior
            print(f"Client disconnected during GET response for: {self.path}")
            pass
        except ConnectionResetError:
            # Connection reset by client
            print(f"Connection reset by client during GET for: {self.path}")
            pass
        except Exception as e:
            # Try to send a 404 error if the file doesn't exist
            try:
                self.send_error(404, f"File not found: {self.path}")
            except:
                # If even sending the error fails, just log it
                print(f"Error serving file: {str(e)}")
                
    def do_POST(self):
        """Handle POST requests"""
        try:
            # Process action endpoint
            if self.path == "/process_action":
                # Get content length
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                # Parse form data if content type is form data
                if self.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
                    form_data = urllib.parse.parse_qs(post_data.decode('utf-8'))
                    
                    # Check if this is an instruction submission
                    if 'instruction' in form_data:
                        instruction = form_data['instruction'][0]
                        print(f"Received instruction: {instruction}")
                        
                        # Process the instruction if we have an automation instance
                        if self.automation_instance:
                            result = self.automation_instance.process_action(instruction)
                            
                            # Send JSON response
                            self.send_response(200)
                            self.send_header('Content-type', 'application/json')
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            self.wfile.write(json.dumps(result).encode('utf-8'))
                            return
                
                # For JSON requests (e.g., fetch API)
                elif self.headers.get('Content-Type') == 'application/json':
                    data = json.loads(post_data.decode('utf-8'))
                    
                    if 'instruction' in data:
                        instruction = data['instruction']
                        print(f"Received instruction (JSON): {instruction}")
                        
                        # Process the instruction if we have an automation instance
                        if self.automation_instance:
                            result = self.automation_instance.process_action(instruction)
                            
                            # Send JSON response
                            self.send_response(200)
                            self.send_header('Content-type', 'application/json')
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            self.wfile.write(json.dumps(result).encode('utf-8'))
                            return
                
                # If we get here, something went wrong
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                error_response = {'success': False, 'message': 'Invalid request format'}
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
            else:
                # Handle other POST requests
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                error_response = {'success': False, 'message': 'Endpoint not found'}
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
                
        except BrokenPipeError:
            # Client disconnected, this is normal behavior
            print(f"Client disconnected during POST response")
            pass
        except ConnectionResetError:
            # Connection reset by client
            print(f"Connection reset by client during POST")
            pass
        except Exception as e:
            # Handle errors and send an error response
            print(f"Error processing POST request: {str(e)}")
            try:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                error_response = {'success': False, 'message': f'Server error: {str(e)}'}
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
            except:
                # If sending the error fails, just log it
                print(f"Failed to send error response: {str(e)}")
                
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-Type")
        self.end_headers()
        
    def log_message(self, format, *args):
        """Override to customize logging"""
        # Print to stdout
        print(format % args)

class InteractiveAutomation:
    """Interactive Android automation with React agent"""
    
    def __init__(self):
        """Initialize the interactive automation"""
        self.device = DeviceActions()
        self.screenshot_analyzer = ScreenshotAnalyzer()
        self.current_step = 0
        self.execution_log = []
        self.http_server = None
        self.server_thread = None
        self.server_port = 8000
        
        # Current state tracking
        self.current_screenshot = None
        self.extracted_text = ""
        self.latest_action = ""
        self.instruction_log = []

        # Register this instance for the global tools
        global _automation_instance
        _automation_instance = self

        # Try to get API key from environment
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        
        # Initialize the LLM for natural language processing
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=openai_api_key)

        self._setup_react_agent()
        
        # Create directory for session screenshots if it doesn't exist
        self.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = f"session_{self.session_id}"
        os.makedirs(self.session_dir, exist_ok=True)
        
        # Create viewer directory for HTML files
        self.viewer_dir = os.path.join(self.session_dir, "viewer")
        os.makedirs(self.viewer_dir, exist_ok=True)
        
        # Create instruction log file
        self.instruction_log_file = os.path.join(self.session_dir, "instruction_log.txt")
        with open(self.instruction_log_file, "w") as f:
            f.write(f"=== Instruction Log for Session {self.session_id} ===\n\n")
        
        # Start HTTP server for screenshot viewing
        self._start_http_server()
        
        # Print session information
        print(f"\n{'='*50}")
        print(f"Starting new automation session: {self.session_id}")
        print(f"{'='*50}\n")
        print(f"Please navigate to: http://localhost:{self.server_port}/viewer/index.html")
    
    def _setup_react_agent(self):

        # Create the React agent
        try:
            self.react_agent = create_react_agent(
                model = self.llm,
                tools=[analyze_screen, click_grid],
                prompt="""
                You are an Action Agent specialized in executing tasks on Android devices using a **ReAct (Reasoning + Acting)** approach. 
                Your primary objective is to analyze the situation, reason about the best course of action, and then execute the necessary steps efficiently.
                
                You have two primary tools at your disposal:
                1. analyze_screen: Captures a screenshot and extracts all text information from it with grid numbers
                2. click_grid: Clicks on a specific grid location by its grid number (extract from analyze screen)
                
                When given an instruction:
                1. First, analyze the current screen to understand what's visible and where elements are located
                2. Identify which grid number corresponds to the element you need to interact with
                3. Click on the appropriate grid number
                4. After each action, analyze the screen again to see the updated state
                
                Remember:
                - Always follow natural Android UI patterns (scrolling if needed, navigating back, etc.)
                - Each grid is identified by a specific number visible on the screenshot
                - Provide clear reasoning for your actions
                """
            )
            return True
        except Exception as e:
            print(f"Error creating React agent: {str(e)}")
            return False
    
    def _analyze_screen_impl(self) -> str:
        """Implementation of the analyze_screen tool"""
        print("\n=== Analyzing Current Screen ===")
        
        try:
            # Take a screenshot if we don't have one
            if not self.current_screenshot:
                self.current_screenshot = self._take_screenshot()
                if not self.current_screenshot:
                    return "Error: Failed to take screenshot for analysis"
            
            # Apply grid overlay to the screenshot
            print("Applying grid overlay...")
            grid_screenshot = self.screenshot_analyzer.apply_grid_to_screenshot(self.current_screenshot)
            
            # Extract text from the screenshot using Gemini Vision
            print("Extracting text using Gemini Vision...")
            extracted_text = self.screenshot_analyzer.extract_text_with_gemini(grid_screenshot)
            
            # Store the extracted text for display in the UI
            self.extracted_text = extracted_text
            print(f"Successfully extracted text, length: {len(extracted_text)} characters")
            
            # Return a summary of the extracted text
            return self.extracted_text
            
        except Exception as e:
            error_msg = f"Error analyzing screen: {str(e)}"
            print(f"Error: {error_msg}")
            return error_msg
    
    def _click_grid_impl(self, grid_number: str) -> str:
        """Implementation of the click_grid tool"""
        try:
            grid_number = int(grid_number)
            grid_overlay = GridOverlay()
            
            x, y = grid_overlay.get_coordinates_for_grid(grid_number)
            success = self.device.click(x, y)
            
            if success:
                # Take a new screenshot after clicking
                self._take_screenshot()
                return f"Clicked at grid {grid_number} (coordinates: {x}, {y})"
            else:
                return f"Failed to click at grid {grid_number}"
        except ValueError as e:
            return f"Invalid grid number: {str(e)}"
        except Exception as e:
            return f"Error clicking grid {grid_number}: {str(e)}"
    
    def _start_http_server(self):
        """Start a custom HTTP server to serve screenshots and process commands"""
        try:
            # Create handler with the automation instance and session directory
            # Use the parent directory as the base for the HTTP server, not the current working directory
            handler = lambda *args, **kwargs: CustomHTTPRequestHandler(
                *args, directory=os.getcwd(), automation_instance=self, **kwargs
            )
            
            # Find an available port
            max_attempts = 10
            for attempt in range(max_attempts):
                try:
                    self.http_server = socketserver.TCPServer(("", self.server_port), handler)
                    break
                except OSError:
                    self.server_port += 1
            
            # Start HTTP server in a separate thread
            self.server_thread = threading.Thread(target=self.http_server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            print(f"HTTP server started on port {self.server_port}")
            
            # Create initial HTML file
            self._take_screenshot()
            if self.current_screenshot:
                viewer_url = self._create_viewer_html(self.current_screenshot)
                print(f"Web interface available at: {viewer_url}")
                # Also display alternative URL that might be more reliable
                direct_url = f"http://localhost:{self.server_port}"
                print(f"If the above URL doesn't work, try: {direct_url}")
            
        except Exception as e:
            print(f"Warning: Could not start HTTP server: {str(e)}")
            
    def _create_viewer_html(self, screenshot_path: str):
        """Create HTML page to display screenshot and extracted text"""
        if not screenshot_path:
            print("Warning: No screenshot path provided for HTML viewer")
            return ""
        
        # Get relative path for screenshot
        rel_path = os.path.relpath(screenshot_path, start=os.getcwd())
        
        # Create HTML content with manual refresh button and responsive design
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Android Automation</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 10px; text-align: center; max-width: 800px; margin: 0 auto; }}
                h1 {{ color: #333; font-size: 24px; margin: 10px 0; }}
                .screenshot {{ max-width: 70%; height: auto; border: 1px solid #ddd; margin: 10px 0; }}
                .info {{ margin: 10px 0; }}
                .step {{ font-weight: bold; }}
                .form-group {{ margin: 10px 0; text-align: left; }}
                label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
                input[type="text"] {{ width: 100%; padding: 8px; box-sizing: border-box; }}
                button {{ background-color: #4CAF50; color: white; padding: 10px 15px; border: none; cursor: pointer; margin-top: 10px; }}
                button:hover {{ background-color: #45a049; }}
                .refresh-button {{ background-color: #2196F3; margin-bottom: 15px; }}
                .status {{ padding: 8px; border-radius: 4px; margin: 10px 0; }}
                .pending {{ background-color: #fff3cd; color: #856404; }}
                .success {{ background-color: #d4edda; color: #155724; }}
                .error {{ background-color: #f8d7da; color: #721c24; }}
            </style>
        </head>
        <body>
            <h1>Android Automation with React Agent</h1>
            <div class="info">
                <p class="step">Step: {self.current_step + 1}</p>
            </div>
            <button class="refresh-button" onclick="window.location.reload()">Refresh Screen</button>
            <img class="screenshot" src="/{rel_path}" alt="Android Screen">
            <div class="form-group">
                <label for="instruction">Enter Natural Language Instruction:</label>
                <input type="text" id="instruction" name="instruction" placeholder="E.g., Click the menu button" required>
                <button type="button" id="execute-btn" onclick="submitInstruction()">Execute</button>
            </div>
            <div id="status" class="status" style="display: none;"></div>
            
            <script>
                // Function to submit the instruction using fetch API
                function submitInstruction() {{
                    const instructionInput = document.getElementById('instruction');
                    const statusDiv = document.getElementById('status');
                    const executeBtn = document.getElementById('execute-btn');
                    
                    // Get the instruction
                    const instruction = instructionInput.value.trim();
                    if (!instruction) {{
                        statusDiv.className = 'status error';
                        statusDiv.style.display = 'block';
                        statusDiv.innerHTML = 'Please enter an instruction';
                        return;
                    }}
                    
                    // Disable button and show pending status
                    executeBtn.disabled = true;
                    statusDiv.className = 'status pending';
                    statusDiv.style.display = 'block';
                    statusDiv.innerHTML = 'Processing instruction...';
                    
                    // Create form data
                    const formData = new URLSearchParams();
                    formData.append('instruction', instruction);
                    
                    // Send the instruction using fetch
                    fetch('/process_action', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/x-www-form-urlencoded',
                        }},
                        body: formData.toString()
                    }})
                    .then(response => {{
                        if (!response.ok) {{
                            throw new Error('Network response was not ok: ' + response.status);
                        }}
                        return response.json();
                    }})
                    .then(data => {{
                        console.log('Success:', data);
                        
                        // Update status based on response
                        if (data.success) {{
                            statusDiv.className = 'status success';
                        }} else {{
                            statusDiv.className = 'status error';
                        }}
                        statusDiv.innerHTML = data.message;
                        
                        // Re-enable button
                        executeBtn.disabled = false;
                        
                        // Clear the input field
                        instructionInput.value = '';
                        
                        // Automatically refresh after successful action (with a delay)
                        if (data.success) {{
                            setTimeout(() => window.location.reload(), 2000);
                        }}
                    }})
                    .catch(error => {{
                        console.error('Error:', error);
                        statusDiv.className = 'status error';
                        statusDiv.innerHTML = 'Error: ' + error.message;
                        executeBtn.disabled = false;
                    }});
                }}
            </script>
        </body>
        </html>
        """
        
        # Write HTML to viewer directory in session folder
        html_file = os.path.join(self.viewer_dir, "index.html")
        os.makedirs(os.path.dirname(html_file), exist_ok=True)  # Ensure directory exists
        with open(html_file, "w") as f:
            f.write(html_content)
        print(f"Created viewer HTML at: {html_file}")
        
        # Also create a copy at the root of the project for direct access
        root_html_file = os.path.join(os.getcwd(), "index.html")
        with open(root_html_file, "w") as f:
            f.write(html_content)
        print(f"Created root HTML at: {root_html_file}")
        
        # Return the URL to access the viewer
        session_url = f"http://localhost:{self.server_port}/session_{self.session_id}/viewer/index.html"
        root_url = f"http://localhost:{self.server_port}/"
        
        return session_url
    
    def _take_screenshot(self) -> Optional[str]:
        """
        Take a screenshot.
        
        Returns:
            str: Path to the screenshot, or None if failed
        """
        print("\n=== Capturing Screen ===")
        
        try:
            # Take a screenshot using DeviceActions
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"{self.session_dir}/screenshot_{timestamp}.png"
            success = self.device.take_screenshot(screenshot_path)
            
            if not success or not os.path.exists(screenshot_path) or os.path.getsize(screenshot_path) == 0:
                print("Screenshot failed or file is empty")
                return None
                
            # Extract text from the screenshot
            print("Extracting text using Gemini Vision...")
            self.extracted_text = self.screenshot_analyzer.extract_text_with_gemini(screenshot_path)
            
            if self.extracted_text:
                # Save the extracted text to a file
                text_path = f"{self.session_dir}/screen_text_{timestamp}.txt"
                with open(text_path, "w") as f:
                    f.write(self.extracted_text)
                print(f"Saved extracted text to: {text_path}")
            else:
                self.extracted_text = "Text extraction failed or no text detected."
            
            # Create HTML viewer and open in browser
            self.current_screenshot = screenshot_path
            viewer_url = self._create_viewer_html(screenshot_path)
            print(f"Screenshot viewer: {viewer_url}")
            
            try:
                if not hasattr(self, 'browser_opened'):
                    webbrowser.open(viewer_url)
                    self.browser_opened = True
                    print("Opened screenshot in browser")
            except Exception as e:
                print(f"Could not open browser: {str(e)}")
                print(f"Please manually open: {viewer_url}")
            
            return screenshot_path
            
        except Exception as e:
            print(f"Error taking screenshot: {str(e)}")
            return None
    
    def _log_instruction(self, instruction: str, action_taken: str):
        """Log the instruction and action taken"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] Instruction: {instruction}\nAction: {action_taken}\n\n"
        
        # Append to the instruction log file
        with open(self.instruction_log_file, "a") as f:
            f.write(log_entry)
        
        # Add to the instruction log list
        self.instruction_log.append({
            "timestamp": timestamp,
            "instruction": instruction,
            "action": action_taken
        })
        
        print(f"\nLogged instruction: {instruction}")
        print(f"Action taken: {action_taken}")
    
    def process_action(self, instruction):
        """Process a natural language instruction and execute the corresponding action"""
        # Log the instruction
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.instruction_log_file, "a") as f:
            f.write(f"[{timestamp}] INSTRUCTION: {instruction}\n")
        
        self.latest_action = f"Processing instruction: {instruction}"
        self.instruction_log.append({"timestamp": timestamp, "instruction": instruction, "status": "processing"})
        
        # Take a screenshot to analyze
        screenshot_path = self._take_screenshot()
        if not screenshot_path:
            error_msg = "Failed to take a screenshot. Please check device connection."
            self._log_action_result(instruction, error_msg, success=False)
            return {"success": False, "message": error_msg}
        
        # Set current screenshot first
        self.current_screenshot = screenshot_path

        try:
            # Prepare the initial message
            initial_input = {
                "messages": [
                    HumanMessage(content=f"""
                    Instruction: {instruction}
                    
                    I need you to execute this instruction on the Android device. First use analyze_screen to understand 
                    what's visible, then identify the relevant grid number, and use click_grid to interact with it.
                    """)
                ]
            }
            
            # Invoke the React agent
            print(f"Invoking React agent with instruction: {instruction}")
            result = self.react_agent.invoke(initial_input)
            
            # Process and log the agent's response
            response_text = ""
            if 'messages' in result and result['messages']:
                for message in result['messages']:
                    if hasattr(message, 'content'):
                        response_text += message.content + "\n"
                        print(f"Agent response: {message.content[:100]}...")
            else:
                response_text = str(result)
                print(f"Agent response (non-standard format): {response_text[:100]}...")
            
            # Log the success/failure
            success = True  # Assume success, the agent should report failures in its response
            self._log_action_result(instruction, response_text, success)
            
            # Take another screenshot after the action
            self._take_screenshot()
            
            # Create updated viewer HTML
            self._create_viewer_html(self.current_screenshot)
            
            return {"success": success, "message": response_text}
        except Exception as e:
            # Print stack trace for debugging
            import traceback
            traceback.print_exc()
            
            error_msg = f"Error while using React agent: {str(e)}"
            print(error_msg)
            self._log_action_result(instruction, error_msg, success=False)
            return {"success": False, "message": error_msg}

    def _log_action_result(self, instruction, result, success=True):
        """Log the result of an action"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "SUCCESS" if success else "FAILED"
        
        # Update latest action for UI display
        self.latest_action = f"[{status}] {result}"
        
        # Log to file
        with open(self.instruction_log_file, "a") as f:
            f.write(f"[{timestamp}] {status}: {result}\n")
            f.write("-" * 80 + "\n")
        
        # Also log to console
        print(f"[{timestamp}] {status}: {result}")
    
    def _log_step(self, screenshot_path: str, action: Dict[str, str], action_result: str) -> None:
        """
        Log a step in the execution log.
        
        Args:
            screenshot_path: Path to the screenshot
            action: Dictionary containing action details
            action_result: Result of the action
        """
        step_data = {
            "step": self.current_step + 1,
            "timestamp": datetime.datetime.now().isoformat(),
            "screenshot": screenshot_path,
            "action": action,
            "result": action_result,
        }
        
        self.execution_log.append(step_data)
        self.current_step += 1
        
        # Save the step data to a JSON file
        step_file = os.path.join(self.session_dir, f"step_{self.current_step}.json")
        with open(step_file, "w") as f:
            json.dump(step_data, f, indent=2)
    
    def _save_execution_log(self) -> None:
        """Save the execution log to a file"""
        log_file = os.path.join(self.session_dir, f"execution_log_{self.session_id}.json")
        with open(log_file, "w") as f:
            json.dump(self.execution_log, f, indent=2)
        print(f"Execution log saved to: {log_file}")
        
        # Also save the instruction log in JSON format
        instruction_log_json = os.path.join(self.session_dir, f"instruction_log_{self.session_id}.json")
        with open(instruction_log_json, "w") as f:
            json.dump(self.instruction_log, f, indent=2)
        print(f"Instruction log saved to: {instruction_log_json}")
            
    def run(self) -> None:
        """Run the interactive automation session."""
        try:
            # Take initial screenshot to start the session
            screenshot_path = self._take_screenshot()
            if not screenshot_path:
                print("Failed to take initial screenshot. Exiting.")
                return
                
            # Keep the script running to serve the HTTP requests
            print("\nInteractive automation is running. Press Ctrl+C to exit.")
            print(f"Access the web interface at: http://localhost:{self.server_port}/viewer/index.html")
            
            # Wait for keyboard interrupt
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\nAutomation session interrupted by user.")
            self._save_execution_log()
            if self.http_server:
                self.http_server.shutdown()
                
def main():
    """Main entry point for the interactive automation."""
    print("\n=== Android Interactive Automation with React Agent ===")
    print("This script provides a web interface for interacting with your Android device.")
    print("You can input natural language instructions and the agent will perform the actions.")
    print("Your instructions and actions will be logged for future reference.")
    
    try:
        # Create and run the interactive automation
        automation = InteractiveAutomation()
        automation.run()
    except Exception as e:
        print(f"\nError: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
