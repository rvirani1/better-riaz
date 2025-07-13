"""
Utility functions for the habit monitor application
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from colorama import Fore, Style


def setup_logging(log_level="INFO", session_timestamp=None):
    """Setup logging configuration with timestamped log files"""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    # Generate timestamped log file name
    if session_timestamp is None:
        session_timestamp = datetime.now()
    
    timestamp_str = session_timestamp.strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"habit_monitor_{timestamp_str}.log")
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # File handler (always enabled with timestamped filename)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Log the setup info
    logger.info(f"Logging initialized - Log file: {log_file}")
    
    return logger, log_file


def format_duration(duration):
    """Format timedelta to readable string"""
    if isinstance(duration, timedelta):
        return str(duration).split('.')[0]
    return str(duration)


def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')


def print_header(title, width=60):
    """Print a formatted header"""
    print(f"{Fore.CYAN}{'='*width}")
    print(f"{Fore.CYAN}{title.center(width)}")
    print(f"{Fore.CYAN}{'='*width}")


def print_status(message, status_type="info"):
    """Print a status message with color coding"""
    colors = {
        "info": Fore.CYAN,
        "success": Fore.GREEN,
        "warning": Fore.YELLOW,
        "error": Fore.RED
    }
    color = colors.get(status_type, Fore.WHITE)
    print(f"{color}{message}")


def validate_confidence(confidence):
    """Validate confidence threshold value"""
    if not isinstance(confidence, (int, float)):
        raise ValueError("Confidence must be a number")
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("Confidence must be between 0.0 and 1.0")
    return float(confidence)


def get_env_var(name, default=None, required=False):
    """Get environment variable with validation"""
    value = os.getenv(name, default)
    if required and not value:
        raise ValueError(f"Environment variable {name} is required")
    return value


def safe_divide(numerator, denominator):
    """Safely divide two numbers, returning 0 if denominator is 0"""
    if denominator == 0:
        return 0
    return numerator / denominator


def format_percentage(value, total):
    """Format a percentage with proper handling of edge cases"""
    if total == 0:
        return "0.0%"
    percentage = (value / total) * 100
    return f"{percentage:.1f}%" 