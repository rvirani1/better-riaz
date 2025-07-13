"""
Audio manager for habit detection warnings (macOS only)
"""

import os
import time
import logging
from threading import Lock


class AudioManager:
    """Handles audio warnings for habit detection on macOS"""
    
    def __init__(self, enabled=True, cooldown_seconds=5):
        self.enabled = enabled
        self.cooldown_seconds = cooldown_seconds
        self.last_warning_time = 0
        self.warning_lock = Lock()
        self.logger = logging.getLogger(__name__)
    
    def play_warning(self, habit_type="general"):
        """Play an audio warning for detected habit"""
        if not self.enabled:
            return
        
        with self.warning_lock:
            current_time = time.time()
            
            # Check cooldown period
            if current_time - self.last_warning_time < self.cooldown_seconds:
                return
            
            # Play the warning sound
            try:
                self._play_macos_sound(habit_type)
                self.last_warning_time = current_time
                self.logger.info(f"Audio warning played for {habit_type}")
            except Exception as e:
                self.logger.error(f"Failed to play audio warning: {e}")
                # Fallback to terminal bell
                print("\a")
    
    def _play_macos_sound(self, habit_type):
        """Play sound on macOS using system sounds or text-to-speech"""
        # Different system sounds for different habits
        sound_map = {
            "about-to-chomp": "/System/Library/Sounds/Ping.aiff",
            "chomping": "/System/Library/Sounds/Ping.aiff",
            "eating": "/System/Library/Sounds/Ping.aiff",
            "pondering": "/System/Library/Sounds/Ping.aiff",
            "default": "/System/Library/Sounds/Ping.aiff"
        }
        
        sound_file = sound_map.get(habit_type, sound_map["default"])
        
        # Check if sound file exists and play it
        if os.path.exists(sound_file):
            os.system(f"afplay {sound_file}")
        else:
            # Fallback to text-to-speech
            messages = {
                "about-to-chomp": "Stop chewing your shirt",
                "chomping": "Stop chomping",
                "eating": "Stop eating",
                "pondering": "Stop pondering",
                "default": "Bad habit detected"
            }
            message = messages.get(habit_type, messages["default"])
            os.system(f"say '{message}'")
    
    def test_audio(self):
        """Test audio functionality"""
        self.logger.info("Testing audio system...")
        
        # Temporarily disable cooldown for testing
        original_cooldown = self.cooldown_seconds
        self.cooldown_seconds = 0
        
        try:
            self.play_warning("test")
            self.logger.info("Audio test completed")
            return True
        except Exception as e:
            self.logger.error(f"Audio test failed: {e}")
            return False
        finally:
            self.cooldown_seconds = original_cooldown
    
    def set_enabled(self, enabled):
        """Enable or disable audio warnings"""
        self.enabled = enabled
        self.logger.info(f"Audio warnings {'enabled' if enabled else 'disabled'}")
    
    def set_cooldown(self, seconds):
        """Set cooldown period between warnings"""
        self.cooldown_seconds = max(0, seconds)
        self.logger.info(f"Audio cooldown set to {self.cooldown_seconds} seconds")
    
    def get_status(self):
        """Get current audio system status"""
        return {
            "enabled": self.enabled,
            "cooldown_seconds": self.cooldown_seconds,
            "last_warning_time": self.last_warning_time,
            "platform": "macOS"
        } 