#!/usr/bin/env python3
"""
Habit Monitor CLI - Real-time webcam monitoring for bad habits using Roboflow workflows
"""

import click
import sys
import os
from colorama import init

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from lib import HabitMonitor
import config

@click.command()
def main():
    """
    Habit Monitor CLI - Monitor webcam for bad habits using Roboflow workflows
    
    All configuration is loaded from the .env file. Required variables:
    - ROBOFLOW_API_KEY: Your Roboflow API key
    - WORKSPACE_NAME: Your Roboflow workspace name  
    - WORKFLOW_ID: Your workflow ID for habit detection
    - CONFIDENCE_THRESHOLD: Confidence threshold (0.0-1.0)
    """
    from colorama import Fore
    
    # Validate required environment variables
    required_vars = {
        'ROBOFLOW_API_KEY': config.ROBOFLOW_API_KEY,
        'WORKSPACE_NAME': config.WORKSPACE_NAME,
        'WORKFLOW_ID': config.WORKFLOW_ID
    }
    
    for var_name, var_value in required_vars.items():
        if not var_value or var_value == "your-api-key-here":
            print(f"{Fore.RED}❌ {var_name} is not set or invalid in .env file")
            print(f"{Fore.RED}Please set it in your .env file: {var_name}=your-value")
            sys.exit(1)
    
    # Create configuration dictionary from config module
    config_dict = {
        key: getattr(config, key) 
        for key in dir(config) 
        if not key.startswith('_') and key.isupper()
    }
    
    # Create monitor instance with fixed values
    monitor = HabitMonitor(
        workspace_name=config.WORKSPACE_NAME,
        workflow_id=config.WORKFLOW_ID,
        confidence_threshold=config.CONFIDENCE_THRESHOLD,
        config=config_dict
    )
    
    # Always show configuration
    config_info = monitor.get_configuration()
    monitor.logger.info("Current configuration:")
    for key, value in config_info.items():
        monitor.logger.info(f"  {key}: {value}")
    
    # Always run validation
    monitor.logger.info("Running system validation...")
    results = monitor.validate_setup()
    
    # Log validation results
    monitor.logger.info("Validation results:")
    for check_name, result in results.items():
        status = "✅ PASSED" if result.get("success", False) else "❌ FAILED"
        message = result.get("message", "No details")
        monitor.logger.info(f"  {check_name}: {status} - {message}")
    
    # Only proceed if all validations pass
    if not all(result.get("success", False) for result in results.values()):
        monitor.logger.error("Setup validation failed. Please check the log file for details.")
        monitor.logger.error("Fix the issues and try again.")
        sys.exit(1)
    
    monitor.logger.info("✅ All validations passed!")
    
    try:
        # Start monitoring
        monitor.start_monitoring()
    except Exception as e:
        monitor.logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 