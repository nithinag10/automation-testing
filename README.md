# Android ADB REST API

A Flask-based REST API that wraps ADB (Android Debug Bridge) commands to interact with Android devices.

## Prerequisites

- Python 3.6+
- ADB installed and available in your PATH
- Android device with USB debugging enabled

## Installation

1. Clone this repository
2. Install the dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Start the server:

```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### Get Connected Devices

```
GET /api/devices
```

Returns a list of connected Android devices.

### Take Screenshot

```
GET /api/screenshot?device_id=DEVICE_ID
```

Takes a screenshot of the device and returns it as a PNG image.

Parameters:
- `device_id` (optional): Specific device ID if multiple devices are connected

### Tap Screen

```
POST /api/tap
```

Simulates a tap on the screen at specified coordinates.

Request body:
```json
{
    "x": 500,
    "y": 500,
    "device_id": "DEVICE_ID" (optional)
}
```

### Swipe Screen

```
POST /api/swipe
```

Simulates a swipe on the screen between specified coordinates.

Request body:
```json
{
    "x1": 100,
    "y1": 500,
    "x2": 600,
    "y2": 500,
    "duration": 300,
    "device_id": "DEVICE_ID" (optional)
}
```

### Press Key

```
POST /api/key
```

Simulates a key press on the device.

Request body:
```json
{
    "keycode": 4,
    "device_id": "DEVICE_ID" (optional)
}
```

Common keycodes:
- 3: HOME
- 4: BACK
- 26: POWER
- 24: VOLUME_UP
- 25: VOLUME_DOWN

### Input Text

```
POST /api/text
```

Inputs text on the device.

Request body:
```json
{
    "text": "Hello World",
    "device_id": "DEVICE_ID" (optional)
}
```

### Execute Shell Command

```
POST /api/shell
```

Executes a custom ADB shell command.

Request body:
```json
{
    "command": "ls -la",
    "device_id": "DEVICE_ID" (optional)
}
```

### Install APK

```
POST /api/install
```

Installs an APK on the device.

Form data:
- `apk`: APK file
- `device_id` (optional): Specific device ID if multiple devices are connected

## Health Check

```
GET /health
```

Returns a simple health check response.

## Example Usage (with curl)

### Get devices

```bash
curl http://localhost:5000/api/devices
```

### Take a screenshot

```bash
curl -o screenshot.png http://localhost:5000/api/screenshot
```

### Tap the screen

```bash
curl -X POST http://localhost:5000/api/tap \
  -H "Content-Type: application/json" \
  -d '{"x": 500, "y": 500}'
```

### Input text

```bash
curl -X POST http://localhost:5000/api/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello World"}'
```
