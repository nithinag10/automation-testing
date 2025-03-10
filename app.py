import os
import subprocess
import tempfile
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Helper function to execute ADB commands
def execute_adb_command(command):
    try:
        logger.info(f"Executing ADB command: {command}")
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return {"success": True, "output": result.stdout, "error": result.stderr}
    except subprocess.CalledProcessError as e:
        logger.error(f"ADB command failed: {e}")
        return {"success": False, "output": "", "error": e.stderr}

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Get list of connected Android devices"""
    result = execute_adb_command(['adb', 'devices'])
    return jsonify(result)

@app.route('/api/screenshot', methods=['GET'])
def take_screenshot():
    """Capture screenshot from connected Android device"""
    device_id = request.args.get('device_id')
    if not device_id:
        return jsonify({"success": False, "error": "device_id is required"})
    
    output_file = 'screenshot.png'
    
    try:
        # Remove existing screenshot if it exists
        if os.path.exists(output_file):
            os.remove(output_file)
        
        # Use the exact command but handle output in Python
        command = ['adb', '-s', device_id, 'exec-out', 'screencap', '-p']
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            return jsonify({"success": False, "error": stderr.decode()})
        
        # Write the binary data directly to file
        with open(output_file, 'wb') as f:
            f.write(stdout)
            
        # Check if file was created and has content
        if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
            return jsonify({"success": False, "error": "Failed to create screenshot or file is empty"})
            
        # Send the file
        return send_file(output_file, mimetype='image/png', 
                        as_attachment=True, download_name='screenshot.png')
    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        return jsonify({"success": False, "error": str(e)})
    finally:
        # Clean up the file after sending
        try:
            if os.path.exists(output_file):
                os.remove(output_file)
        except Exception as e:
            logger.error(f"Error cleaning up file: {e}")

@app.route('/api/tap', methods=['POST'])
def tap_screen():
    """Simulate tap on screen at specified coordinates"""
    data = request.json
    if not data or 'x' not in data or 'y' not in data:
        return jsonify({"success": False, "error": "Missing x, y coordinates"}), 400
    
    x, y = data['x'], data['y']
    device_id = data.get('device_id')
    
    # Build command with optional device ID
    command = ['adb']
    if device_id:
        command.extend(['-s', device_id])
    command.extend(['shell', 'input', 'tap', str(x), str(y)])
    
    result = execute_adb_command(command)
    return jsonify(result)

@app.route('/api/swipe', methods=['POST'])
def swipe_screen():
    """Simulate swipe on screen between specified coordinates"""
    data = request.json
    if not data or 'x1' not in data or 'y1' not in data or 'x2' not in data or 'y2' not in data:
        return jsonify({"success": False, "error": "Missing coordinates"}), 400
    
    x1, y1 = data['x1'], data['y1']
    x2, y2 = data['x2'], data['y2']
    duration = data.get('duration', 300)  # Default duration in ms
    device_id = data.get('device_id')
    
    # Build command with optional device ID
    command = ['adb']
    if device_id:
        command.extend(['-s', device_id])
    command.extend(['shell', 'input', 'swipe', str(x1), str(y1), str(x2), str(y2), str(duration)])
    
    result = execute_adb_command(command)
    return jsonify(result)

@app.route('/api/key', methods=['POST'])
def press_key():
    """Simulate key press on device"""
    data = request.json
    if not data or 'keycode' not in data:
        return jsonify({"success": False, "error": "Missing keycode"}), 400
    
    keycode = data['keycode']
    device_id = data.get('device_id')
    
    # Build command with optional device ID
    command = ['adb']
    if device_id:
        command.extend(['-s', device_id])
    command.extend(['shell', 'input', 'keyevent', str(keycode)])
    
    result = execute_adb_command(command)
    return jsonify(result)

@app.route('/api/text', methods=['POST'])
def input_text():
    """Input text on device"""
    data = request.json
    if not data or 'text' not in data:
        return jsonify({"success": False, "error": "Missing text"}), 400
    
    text = data['text']
    device_id = data.get('device_id')
    
    # Build command with optional device ID
    command = ['adb']
    if device_id:
        command.extend(['-s', device_id])
    command.extend(['shell', 'input', 'text', text])
    
    result = execute_adb_command(command)
    return jsonify(result)

@app.route('/api/shell', methods=['POST'])
def execute_shell():
    """Execute custom ADB shell command"""
    data = request.json
    if not data or 'command' not in data:
        return jsonify({"success": False, "error": "Missing command"}), 400
    
    shell_command = data['command']
    device_id = data.get('device_id')
    
    # Build command with optional device ID
    command = ['adb']
    if device_id:
        command.extend(['-s', device_id])
    command.extend(['shell', shell_command])
    
    result = execute_adb_command(command)
    return jsonify(result)

@app.route('/api/install', methods=['POST'])
def install_apk():
    """Install APK on device"""
    if 'apk' not in request.files:
        return jsonify({"success": False, "error": "No APK file provided"}), 400
    
    apk_file = request.files['apk']
    device_id = request.form.get('device_id')
    
    # Save APK to temp file
    temp_dir = tempfile.mkdtemp()
    apk_path = os.path.join(temp_dir, secure_filename(apk_file.filename))
    apk_file.save(apk_path)
    
    # Build command with optional device ID
    command = ['adb']
    if device_id:
        command.extend(['-s', device_id])
    command.extend(['install', apk_path])
    
    try:
        result = execute_adb_command(command)
        return jsonify(result)
    finally:
        # Clean up
        if os.path.exists(apk_path):
            os.unlink(apk_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)

@app.route('/api/read_screen', methods=['GET'])
def read_screen():
    """Read current screen content using UIAutomator"""
    device_id = request.args.get('device_id')
    
    # Build command with optional device ID
    dump_command = ['adb']
    cat_command = ['adb']
    
    if device_id:
        dump_command.extend(['-s', device_id])
        cat_command.extend(['-s', device_id])
    
    dump_command.extend(['shell', 'uiautomator', 'dump'])
    cat_command.extend(['shell', 'cat', '/sdcard/window_dump.xml'])
    
    # First dump the UI hierarchy
    dump_result = execute_adb_command(dump_command)
    if not dump_result['success']:
        return jsonify(dump_result)
    
    # Then read the dumped file
    cat_result = execute_adb_command(cat_command)
    return jsonify({
        "success": cat_result['success'],
        "content": cat_result['output'],
        "error": cat_result['error']
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
