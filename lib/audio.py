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
        """Play sound on macOS using custom MP3 files or system sounds as fallback"""
        # Different custom sounds for different habits
        sound_map = {
            "about-to-chomp": "audio/about-to-chomp.mp3",
            "chomping": "audio/chomping.mp3",
            "eating": "audio/eating.mp3",
            "pondering": "audio/pondering.mp3",
            "default": "/System/Library/Sounds/Ping.aiff"
        }
        
        sound_file = sound_map.get(habit_type, sound_map["default"])
        os.system(f"afplay {sound_file}")
    
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