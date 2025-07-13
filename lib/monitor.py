"""
Simplified habit monitor using Roboflow's InferencePipeline
"""

import time
import signal
import sys
import os
from datetime import datetime
from inference import InferencePipeline
from .audio import AudioManager
from .display import DisplayManager
from .stats import StatsTracker
from .utils import setup_logging, validate_confidence


class HabitMonitor:
    """Simplified habit monitoring using Roboflow InferencePipeline"""
    
    def __init__(self, workspace_name, workflow_id, confidence_threshold=0.7, 
                 camera_index=0, config=None):
        
        # Store session start time for consistent timestamps
        self.session_start_time = datetime.now()
        
        # Validate parameters
        self.confidence_threshold = validate_confidence(confidence_threshold)
        self.camera_index = camera_index
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
            enabled=self.config.get("ENABLE_AUDIO_WARNINGS", True),
            cooldown_seconds=self.config.get("AUDIO_WARNING_COOLDOWN", 5)
        )
        
        # Disable display manager for file-only logging
        self.display_manager = DisplayManager(
            refresh_rate=self.config.get("REFRESH_RATE", 1.0),
            show_header=True
        )
        self.display_enabled = False  # Disable stdout display
        
        self.stats_tracker = StatsTracker(
            stats_file=self.config.get("STATISTICS_FILE", "logs/habit_statistics.json")
        )
        
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
                video_reference=self.camera_index,
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
                video_reference=self.camera_index,
                workflow_id=self.workflow_id,
                workspace_name=self.workspace_name,
            )
            
            # Start statistics tracking
            self.stats_tracker.start_session()
            
            # Set stats tracker and start display (if enabled)
            if self.display_enabled:
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
            
            # Always update stats (detected or not)
            self.stats_tracker.update_habit_detection(
                detected=habit_detected,
                confidence=prediction_data['confidence'],
                habit_class=prediction_data['top_class']
            )
            
            if habit_detected:
                current_time = time.time()
                
                # Play audio warning (respects cooldown)
                self.audio_manager.play_warning()
                
                # Log the detection
                self.logger.info(f"Chomping detected: {prediction_data['top_class']} with confidence {prediction_data['confidence']:.3f}")
                
                self.last_detection_time = current_time
        
        except Exception as e:
            self.logger.error(f"Error processing prediction: {e}")
    
    def _process_prediction(self, result):
        """Process prediction result to determine if a habit was detected and extract data"""
        try:
            # Default prediction data
            prediction_data = {
                'top_class': 'unknown',
                'confidence': 0.0
            }
            
            # Handle the workflow result format - result is a dict
            if isinstance(result, dict) and result:
                # Extract classification predictions directly from the dict
                classification_preds = result.get('classification_predictions')
                if classification_preds:
                    prediction_data['top_class'] = classification_preds.get('top', 'unknown')
                    prediction_data['confidence'] = classification_preds.get('confidence', 0.0)
                    
                    # Check if the top class is "chomping" and confidence is above threshold
                    if prediction_data['top_class'] == "chomping" and prediction_data['confidence'] >= self.confidence_threshold:
                        self.logger.debug(f"Chomping detected: {prediction_data['top_class']} with confidence {prediction_data['confidence']:.3f}")
                        return True, prediction_data
                    else:
                        self.logger.debug(f"No chomping: {prediction_data['top_class']} with confidence {prediction_data['confidence']:.3f}")
            
            return False, prediction_data
            
        except Exception as e:
            self.logger.error(f"Error processing prediction result: {e}")
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
        if self.display_enabled:
            self.display_manager.stop_display()
        
        # End session and save stats
        if self.stats_tracker:
            self.stats_tracker.end_session()
            
            # Show final summary (if display enabled)
            if self.display_enabled:
                self.display_manager.show_shutdown_message(self.stats_tracker)
        
        session_duration = datetime.now() - self.session_start_time
        self.logger.info(f"Session ended. Duration: {session_duration}")
        self.logger.info(f"Log file saved: {self.log_file}")
        self.logger.info("Monitoring stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        self.logger.info(f"Received signal {signum}, stopping monitoring...")
        self.stop_monitoring()
        sys.exit(0)
    
    def get_status(self):
        """Get current monitoring status"""
        return {
            "is_monitoring": self.is_monitoring,
            "last_detection": self.last_detection_time,
            "session_stats": self.stats_tracker.get_session_summary() if self.stats_tracker else None,
            "log_file": self.log_file,
            "session_start": self.session_start_time
        }
    
    def get_configuration(self):
        """Get current configuration"""
        return {
            "workspace_name": self.workspace_name,
            "workflow_id": self.workflow_id,
            "confidence_threshold": self.confidence_threshold,
            "camera_index": self.camera_index,
            "audio_enabled": self.audio_manager.enabled if self.audio_manager else False,
            "audio_cooldown": self.audio_manager.cooldown_seconds if self.audio_manager else 0,
            "display_refresh_rate": self.display_manager.refresh_rate if self.display_manager else 0,
            "log_file": self.log_file,
            "session_start": self.session_start_time.isoformat()
        }
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_monitoring() 