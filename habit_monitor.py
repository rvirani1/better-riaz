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
@click.option('--workspace', default=config.WORKSPACE_NAME, 
              help='Roboflow workspace name')
@click.option('--workflow-id', default=config.WORKFLOW_ID, 
              help='Workflow ID for habit detection')
@click.option('--confidence', default=config.CONFIDENCE_THRESHOLD, type=float, 
              help='Confidence threshold for habit detection')
@click.option('--camera', default=config.CAMERA_INDEX, type=int, 
              help='Camera index to use')
@click.option('--skip-validation', is_flag=True, 
              help='Skip setup validation (not recommended)')
@click.option('--show-config', is_flag=True, 
              help='Show current configuration')
def main(workspace, workflow_id, confidence, camera, skip_validation, show_config):
    """
    Habit Monitor CLI - Monitor webcam for bad habits using Roboflow workflows
    """
    from colorama import Fore
    
    # Create configuration dictionary from config module
    config_dict = {
        key: getattr(config, key) 
        for key in dir(config) 
        if not key.startswith('_') and key.isupper()
    }
    
    # Create monitor instance
    monitor = HabitMonitor(
        workspace_name=workspace,
        workflow_id=workflow_id,
        confidence_threshold=confidence,
        camera_index=camera,
        config=config_dict
    )
    
    # Show configuration if requested (only if display enabled)
    if show_config:
        if hasattr(monitor, 'display_enabled') and monitor.display_enabled:
            monitor.display_manager.show_configuration(monitor.get_configuration())
        else:
            # Log configuration to file instead
            config_info = monitor.get_configuration()
            monitor.logger.info("Current configuration:")
            for key, value in config_info.items():
                monitor.logger.info(f"  {key}: {value}")
        return
    
    # Run validation by default (unless skipped)
    if not skip_validation:
        monitor.logger.info("Running system validation...")
        results = monitor.validate_setup()
        
        # Log validation results to file instead of displaying
        monitor.logger.info("Validation results:")
        for check_name, result in results.items():
            status = "✅ PASSED" if result.get("success", False) else "❌ FAILED"
            message = result.get("message", "No details")
            monitor.logger.info(f"  {check_name}: {status} - {message}")
        
        # Only proceed if all validations pass
        if not all(result.get("success", False) for result in results.values()):
            monitor.logger.error("Setup validation failed. Please check the log file for details.")
            monitor.logger.error("You can skip validation with --skip-validation (not recommended)")
            sys.exit(1)
        
        monitor.logger.info("✅ All validations passed!")
    
    # Check if API key is set
    if not os.getenv("ROBOFLOW_API_KEY"):
        monitor.logger.warning("ROBOFLOW_API_KEY environment variable not set")
        monitor.logger.warning("Please set it with: export ROBOFLOW_API_KEY=your-api-key")
    
    try:
        # Start monitoring
        monitor.start_monitoring()
    except Exception as e:
        monitor.logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 