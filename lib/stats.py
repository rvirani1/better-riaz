"""
Statistics tracker for habit monitoring analytics
"""

import json
import logging
from datetime import datetime, timedelta
from .utils import format_duration, safe_divide, format_percentage


class StatsTracker:
    """Tracks and analyzes habit detection statistics"""
    
    def __init__(self, stats_file="logs/habit_statistics.json"):
        self.stats_file = stats_file
        self.logger = logging.getLogger(__name__)
        
        # Session tracking
        self.session_start_time = None
        self.habit_start_time = None
        self.total_habit_time = timedelta(0)
        self.current_habit_duration = timedelta(0)
        self.is_habit_active = False
        
        # Statistics
        self.total_detections = 0
        self.habit_sessions = []
        self.detection_history = []
        
        # Load previous statistics if available
        self._load_statistics()
    
    def start_session(self):
        """Start a new monitoring session"""
        self.session_start_time = datetime.now()
        self.logger.info("Statistics session started")
    
    def end_session(self):
        """End the current monitoring session"""
        if self.is_habit_active:
            # End any active habit session
            self._end_habit_session()
        
        self._save_statistics()
        
        self.logger.info("Statistics session ended")
    
    def update_habit_detection(self, detected, confidence=0.0, habit_class="unknown"):
        """Update habit detection state and statistics"""
        current_time = datetime.now()
        
        # Record detection event
        self.detection_history.append({
            "timestamp": current_time,
            "detected": detected,
            "confidence": confidence,
            "class": habit_class
        })
        
        if detected and not self.is_habit_active:
            # Habit session started
            self._start_habit_session(current_time, habit_class)
            
        elif not detected and self.is_habit_active:
            # Habit session ended
            self._end_habit_session(current_time)
            
        elif detected and self.is_habit_active:
            # Habit session continues
            self._update_current_habit_duration(current_time)
    
    def _start_habit_session(self, timestamp, habit_class):
        """Start a new habit session"""
        self.habit_start_time = timestamp
        self.is_habit_active = True
        self.total_detections += 1
        
        self.logger.info(f"Habit session started: {habit_class}")
    
    def _end_habit_session(self, timestamp=None):
        """End the current habit session"""
        if not self.is_habit_active or not self.habit_start_time:
            return
        
        end_time = timestamp or datetime.now()
        session_duration = end_time - self.habit_start_time
        
        # Record the session
        self.habit_sessions.append({
            "start_time": self.habit_start_time,
            "end_time": end_time,
            "duration": session_duration
        })
        
        # Update totals
        self.total_habit_time += session_duration
        
        # Reset state
        self.is_habit_active = False
        self.current_habit_duration = timedelta(0)
        self.habit_start_time = None
        
        self.logger.info(f"Habit session ended: {format_duration(session_duration)}")
    
    def _update_current_habit_duration(self, timestamp):
        """Update the current habit session duration"""
        if self.habit_start_time:
            self.current_habit_duration = timestamp - self.habit_start_time
    
    def get_session_duration(self):
        """Get total session duration"""
        if not self.session_start_time:
            return timedelta(0)
        return datetime.now() - self.session_start_time
    
    def get_habit_percentage(self):
        """Get percentage of time spent on habits"""
        session_duration = self.get_session_duration()
        if session_duration.total_seconds() == 0:
            return 0.0
        
        total_habit_seconds = self.total_habit_time.total_seconds()
        current_habit_seconds = self.current_habit_duration.total_seconds()
        
        return safe_divide(
            total_habit_seconds + current_habit_seconds,
            session_duration.total_seconds()
        ) * 100
    
    def get_average_session_duration(self):
        """Get average habit session duration"""
        if not self.habit_sessions:
            return timedelta(0)
        
        total_duration = sum(
            [session["duration"] for session in self.habit_sessions],
            timedelta(0)
        )
        
        return total_duration / len(self.habit_sessions)
    
    def get_detection_rate(self):
        """Get detection rate (detections per minute)"""
        session_duration = self.get_session_duration()
        if session_duration.total_seconds() == 0:
            return 0.0
        
        minutes = session_duration.total_seconds() / 60
        return safe_divide(self.total_detections, minutes)
    
    def get_current_stats(self):
        """Get current statistics summary"""
        return {
            "session_duration": self.get_session_duration(),
            "total_detections": self.total_detections,
            "total_habit_time": self.total_habit_time,
            "current_habit_duration": self.current_habit_duration,
            "habit_sessions_count": len(self.habit_sessions),
            "average_session_duration": self.get_average_session_duration(),
            "habit_percentage": self.get_habit_percentage(),
            "detection_rate": self.get_detection_rate(),
            "is_habit_active": self.is_habit_active
        }
    
    def get_formatted_stats(self):
        """Get formatted statistics for display"""
        stats = self.get_current_stats()
        
        return {
            "session_duration": format_duration(stats["session_duration"]),
            "total_detections": stats["total_detections"],
            "total_habit_time": format_duration(stats["total_habit_time"]),
            "current_habit_duration": format_duration(stats["current_habit_duration"]),
            "habit_sessions_count": stats["habit_sessions_count"],
            "average_session_duration": format_duration(stats["average_session_duration"]),
            "habit_percentage": f"{stats['habit_percentage']:.1f}%",
            "detection_rate": f"{stats['detection_rate']:.1f}/min",
            "is_habit_active": stats["is_habit_active"]
        }
    
    def _save_statistics(self):
        """Save statistics to file"""
        try:
            data = {
                "session_start_time": self.session_start_time.isoformat() if self.session_start_time else None,
                "total_detections": self.total_detections,
                "total_habit_time_seconds": self.total_habit_time.total_seconds(),
                "habit_sessions": [
                    {
                        "start_time": session["start_time"].isoformat(),
                        "end_time": session["end_time"].isoformat(),
                        "duration_seconds": session["duration"].total_seconds()
                    }
                    for session in self.habit_sessions
                ],
                "detection_history": [
                    {
                        "timestamp": event["timestamp"].isoformat(),
                        "detected": event["detected"],
                        "confidence": event["confidence"],
                        "class": event["class"]
                    }
                    for event in self.detection_history
                ]
            }
            
            with open(self.stats_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Statistics saved to {self.stats_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save statistics: {e}")
    
    def _load_statistics(self):
        """Load statistics from file"""
        try:
            with open(self.stats_file, 'r') as f:
                data = json.load(f)
            
            # Restore session data
            if data.get("session_start_time"):
                self.session_start_time = datetime.fromisoformat(data["session_start_time"])
            
            self.total_detections = data.get("total_detections", 0)
            self.total_habit_time = timedelta(seconds=data.get("total_habit_time_seconds", 0))
            
            # Restore habit sessions
            self.habit_sessions = []
            for session_data in data.get("habit_sessions", []):
                self.habit_sessions.append({
                    "start_time": datetime.fromisoformat(session_data["start_time"]),
                    "end_time": datetime.fromisoformat(session_data["end_time"]),
                    "duration": timedelta(seconds=session_data["duration_seconds"])
                })
            
            # Restore detection history
            self.detection_history = []
            for event_data in data.get("detection_history", []):
                self.detection_history.append({
                    "timestamp": datetime.fromisoformat(event_data["timestamp"]),
                    "detected": event_data["detected"],
                    "confidence": event_data["confidence"],
                    "class": event_data["class"]
                })
            
            self.logger.info(f"Statistics loaded from {self.stats_file}")
            
        except FileNotFoundError:
            self.logger.info("No existing statistics file found, starting fresh")
        except Exception as e:
            self.logger.error(f"Failed to load statistics: {e}")
    
    def reset_statistics(self):
        """Reset all statistics"""
        self.session_start_time = None
        self.habit_start_time = None
        self.total_habit_time = timedelta(0)
        self.current_habit_duration = timedelta(0)
        self.is_habit_active = False
        self.total_detections = 0
        self.habit_sessions = []
        self.detection_history = []
        
        self.logger.info("Statistics reset") 