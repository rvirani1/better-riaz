"""
Configuration file for Habit Monitor CLI
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Roboflow Configuration
ROBOFLOW_API_KEY = os.environ["ROBOFLOW_API_KEY"]
WORKSPACE_NAME = os.environ["WORKSPACE_NAME"]
WORKFLOW_ID = os.environ["WORKFLOW_ID"]

# Detection Settings
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))  # Confidence threshold for habit detection (0.0 - 1.0)

# Camera Settings
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))           # Default camera index (0 for built-in webcam)
CAMERA_WIDTH = int(os.getenv("CAMERA_WIDTH", "640"))         # Camera resolution width
CAMERA_HEIGHT = int(os.getenv("CAMERA_HEIGHT", "480"))        # Camera resolution height
CAMERA_FPS = int(os.getenv("CAMERA_FPS", "15"))           # Camera frames per second

# Audio Settings
ENABLE_AUDIO_WARNINGS = os.getenv("ENABLE_AUDIO_WARNINGS", "True").lower() == "true"  # Enable/disable audio warnings
AUDIO_WARNING_COOLDOWN = float(os.getenv("AUDIO_WARNING_COOLDOWN", "5"))    # Seconds to wait between audio warnings

# Display Settings
REFRESH_RATE = float(os.getenv("REFRESH_RATE", "1.0"))        # Seconds between display updates
SHOW_WEBCAM_FEED = os.getenv("SHOW_WEBCAM_FEED", "False").lower() == "true"  # Show webcam window (set to True for debugging)

# Logging Settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")        # DEBUG, INFO, WARNING, ERROR
# Note: Logging always enabled with timestamped files in logs/ directory 