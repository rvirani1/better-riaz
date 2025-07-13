"""
Statistics tracker for habit monitoring analytics
"""

import logging
from datetime import datetime, timedelta
from .utils import format_duration, safe_divide


class StatsTracker:
    """Tracks and analyzes habit detection statistics"""
    
    def __init__(self):
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
    
    def start_session(self):
        """Start a new monitoring session"""
        self.session_start_time = datetime.now()
        self.logger.info("Statistics session started")
    
    def end_session(self):
        """End the current monitoring session"""
        if self.is_habit_active:
            # End any active habit session
            self._end_habit_session()
        
        self.logger.info("Statistics session ended")
    
    def update_habit_detection(self, detected, confidence=0.0, habit_class="unknown"):
        """Update habit detection state and statistics"""
        current_time = datetime.now()
        
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
    
    def reset_statistics(self):
        """Reset all statistics"""
        self.total_detections = 0
        self.total_habit_time = timedelta(0)
        self.habit_sessions = []
        self.is_habit_active = False
        self.habit_start_time = None
        self.current_habit_duration = timedelta(0)
        
        self.logger.info("Statistics reset") 