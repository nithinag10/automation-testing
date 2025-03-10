#!/bin/bash
device_id=$1
adb -s $device_id exec-out screencap -p > screenshot.png
