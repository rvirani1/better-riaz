"""
Habit Monitor Library - Modular components for habit monitoring
"""

from .monitor import HabitMonitor
from .audio import AudioManager
from .display import DisplayManager
from .stats import StatsTracker
from .utils import setup_logging, format_duration

__version__ = "1.0.0"
__all__ = [
    "HabitMonitor",
    "AudioManager",
    "DisplayManager",
    "StatsTracker",
    "setup_logging",
    "format_duration"
] 