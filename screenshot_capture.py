#!/usr/bin/env python3
import subprocess
import os
from datetime import datetime

# Create screenshot filename with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
screenshot_path = f"/tmp/screenshot_{timestamp}.png"

# Take screenshot using macOS screencapture command
subprocess.run(["screencapture", "-x", screenshot_path], check=True)

print(screenshot_path)
