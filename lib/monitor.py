"""
Simplified habit monitor using Roboflow's InferencePipeline
"""

import time
import signal
import sys
import pprint
import os
from datetime import datetime
from inference import InferencePipeline
from .audio import AudioManager
from .display import DisplayManager
from .stats import StatsTracker
from .utils import setup_logging, validate_confidence
from .models import is_chomping_detected, get_top_class, get_confidence 


class HabitMonitor:
    """Simplified habit monitoring using Roboflow InferencePipeline"""
    
    def __init__(self, workspace_name, workflow_id, confidence_threshold=0.7, config=None):
        
        # Store session start time for consistent timestamps
        self.session_start_time = datetime.now()
        
        # Validate parameters
        self.confidence_threshold = validate_confidence(confidence_threshold)
        self.workspace_name = workspace_name
        self.workflow_id = workflow_id
        
        # Configuration
        self.config = config or {}
        
        # Setup logging with timestamped files
        log_level = self.config.get("LOG_LEVEL", "INFO")
        self.logger, self.log_file = setup_logging(log_level, self.session_start_time)
        
        # Get API key
        self.api_key = os.getenv("ROBOFLOW_API_KEY")
        if not self.api_key:
            raise ValueError("ROBOFLOW_API_KEY environment variable is required")
        
        # Initialize components
        self.audio_manager = AudioManager(
            cooldown_seconds=self.config.get("AUDIO_WARNING_COOLDOWN", 5)
        )
        
        # Display manager for CLI dashboard
        self.display_manager = DisplayManager(
            refresh_rate=self.config.get("REFRESH_RATE", 1.0),
            show_header=True
        )
        
        self.stats_tracker = StatsTracker()
        
        # Pipeline and monitoring state
        self.pipeline = None
        self.is_monitoring = False
        self.last_detection_time = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("HabitMonitor initialized with InferencePipeline")
        self.logger.info(f"Session started at: {self.session_start_time}")
        self.logger.info(f"Workspace: {workspace_name}, Workflow: {workflow_id}")
        self.logger.info(f"Confidence threshold: {confidence_threshold}")
    
    def validate_setup(self):
        """Validate the monitoring setup"""
        results = {}
        
        # Check API key
        if self.api_key and self.api_key != "your-api-key-here":
            results["API Key"] = {"success": True, "message": "API key is set"}
        else:
            results["API Key"] = {"success": False, "message": "ROBOFLOW_API_KEY not set or invalid"}
        
        # Check audio system
        try:
            audio_test = self.audio_manager.test_audio()
            results["Audio System"] = {"success": audio_test, "message": "Audio system working" if audio_test else "Audio system failed"}
        except Exception as e:
            results["Audio System"] = {"success": False, "message": f"Audio test failed: {e}"}
        
        # Check camera (we'll try to initialize the pipeline briefly)
        try:
            test_pipeline = InferencePipeline.init_with_workflow(
                api_key=self.api_key,
                workspace_name=self.workspace_name,
                workflow_id=self.workflow_id,
                video_reference=0,
                on_prediction=lambda x, y: None  # Dummy callback
            )
            results["Camera & Workflow"] = {"success": True, "message": "Camera and workflow accessible"}
            # Don't start the test pipeline, just creating it validates access
            del test_pipeline
        except Exception as e:
            results["Camera & Workflow"] = {"success": False, "message": f"Camera/workflow test failed: {e}"}
        
        return results
    
    def start_monitoring(self):
        """Start the habit monitoring pipeline"""
        if self.is_monitoring:
            self.logger.warning("Monitoring is already running")
            return
        
        try:
            self.logger.info("Starting habit monitoring...")
            
            # Initialize the InferencePipeline
            self.pipeline = InferencePipeline.init_with_workflow(
                api_key=self.api_key,
                max_fps=self.config.get("CAMERA_FPS", 15),
                on_prediction=self._on_prediction,
                video_reference=0,
                workflow_id=self.workflow_id,
                workspace_name=self.workspace_name,
            )
            
            # Start statistics tracking
            self.stats_tracker.start_session()
            
            # Set stats tracker and start display (if enabled)
            self.display_manager.set_stats_tracker(self.stats_tracker)
            self.display_manager.start_display()
            
            # Start the pipeline
            self.is_monitoring = True
            self.logger.info("Habit monitoring started successfully")
            
            # Start pipeline and wait
            self.pipeline.start()
            self.pipeline.join()  # This blocks until pipeline ends
            
        except KeyboardInterrupt:
            self.logger.info("Monitoring interrupted by user")
        except Exception as e:
            self.logger.error(f"Error during monitoring: {e}")
            raise
        finally:
            self.stop_monitoring()
    
    def _on_prediction(self, result, _video_frame):
        """Handle predictions from the InferencePipeline"""
        try:
            # Extract prediction details and determine if habit was detected
            habit_detected, prediction_data = self._process_prediction(result)
            
            # Update display with latest detection info
            self.display_manager.update_detection_info(
                prediction_data['top_class'], 
                prediction_data['confidence']
            )
            
            # Always update stats (detected or not)
            self.stats_tracker.update_habit_detection(
                detected=habit_detected,
                habit_class=prediction_data['top_class']
            )
            
            if habit_detected:
                current_time = time.time()
                
                # Play audio warning (respects cooldown)
                self.audio_manager.play_warning(prediction_data['top_class'])
                
                # Log the detection
                self.logger.info(f"Chomping detected: {prediction_data['top_class']} with confidence {prediction_data['confidence']:.3f}")
                
                self.last_detection_time = current_time
        
        except Exception as e:
            self.logger.error(f"Error processing prediction: {e}")
    
    def _process_prediction(self, result):
        """Process prediction result to determine if a habit was detected and extract data"""
        try:
            # Use simple utility functions to extract what we need
            habit_detected, confidence = is_chomping_detected(result, self.confidence_threshold)
            top_class = get_top_class(result)
            
            # Extract prediction data
            prediction_data = {
                'top_class': top_class,
                'confidence': confidence
            }
            
            # Log the detection result
            if habit_detected:
                self.logger.debug(f"Chomping detected: {top_class} with confidence {confidence:.3f}")
            else:
                self.logger.debug(f"No chomping: {top_class} with confidence {confidence:.3f}")
            
            return habit_detected, prediction_data
            
        except Exception as e:
            self.logger.error(f"Error processing prediction result: {e}")
            self.logger.error(f"Raw result: {pprint.pformat(result)}")
            # Don't terminate the application, just return no detection
            return False, {'top_class': 'unknown', 'confidence': 0.0}
    
    def stop_monitoring(self):
        """Stop the monitoring pipeline"""
        if not self.is_monitoring:
            return
        
        self.logger.info("Stopping habit monitoring...")
        self.is_monitoring = False
        
        # Stop pipeline
        if self.pipeline:
            try:
                self.pipeline.terminate()
            except Exception as e:
                self.logger.error(f"Error stopping pipeline: {e}")
        
        # Stop display (if enabled)
        self.display_manager.stop_display()
        
        # End session and save stats
        if self.stats_tracker:
            self.stats_tracker.end_session()
            
            # Show final summary (if display enabled)
            self.display_manager.show_shutdown_message(self.stats_tracker)
        
        session_duration = datetime.now() - self.session_start_time
        self.logger.info(f"Session ended. Duration: {session_duration}")
        self.logger.info(f"Log file saved: {self.log_file}")
        self.logger.info("Monitoring stopped")
    
    def _signal_handler(self, signum, _frame):
        """Handle interrupt signals"""
        self.logger.info(f"Received signal {signum}, stopping monitoring...")
        self.stop_monitoring()
        sys.exit(0)
    
    def get_configuration(self):
        """Get current configuration"""
        return {
            "workspace_name": self.workspace_name,
            "workflow_id": self.workflow_id,
            "confidence_threshold": self.confidence_threshold,
            "audio_cooldown": self.audio_manager.cooldown_seconds if self.audio_manager else 0,
            "display_refresh_rate": self.display_manager.refresh_rate if self.display_manager else 0,
            "log_file": self.log_file,
            "session_start": self.session_start_time.isoformat()
        }
    
    def __enter__(self):
        return self
    
    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        self.stop_monitoring() 