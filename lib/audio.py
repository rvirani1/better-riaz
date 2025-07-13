"""
Audio manager for habit detection warnings
"""

import os
import sys
import time
import logging
from threading import Lock


class AudioManager:
    """Handles audio warnings for habit detection"""
    
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
                self._play_sound(habit_type)
                self.last_warning_time = current_time
                self.logger.info(f"Audio warning played for {habit_type}")
            except Exception as e:
                self.logger.error(f"Failed to play audio warning: {e}")
    
    def _play_sound(self, habit_type):
        """Play the actual sound based on platform"""
        try:
            if sys.platform == "win32":
                self._play_windows_sound(habit_type)
            elif sys.platform == "darwin":  # macOS
                self._play_macos_sound(habit_type)
            else:  # Linux and other Unix-like systems
                self._play_linux_sound(habit_type)
        except Exception as e:
            # Fallback to terminal bell
            print("\a")
            self.logger.warning(f"Fallback to terminal bell: {e}")
    
    def _play_windows_sound(self, habit_type):
        """Play sound on Windows"""
        try:
            import winsound
            # Different beep patterns for different habits
            if habit_type == "shirt_chewing":
                winsound.Beep(800, 500)  # 800Hz for 500ms
            elif habit_type == "face_touching":
                winsound.Beep(1000, 300)  # 1000Hz for 300ms
            else:
                winsound.Beep(600, 400)  # Default beep
        except ImportError:
            print("\a")
    
    def _play_macos_sound(self, habit_type):
        """Play sound on macOS"""
        # Different system sounds for different habits
        sound_map = {
            "shirt_chewing": "/System/Library/Sounds/Ping.aiff",
            "face_touching": "/System/Library/Sounds/Pop.aiff",
            "default": "/System/Library/Sounds/Ping.aiff"
        }
        
        sound_file = sound_map.get(habit_type, sound_map["default"])
        
        # Check if sound file exists
        if os.path.exists(sound_file):
            os.system(f"afplay {sound_file}")
        else:
            # Fallback to say command
            messages = {
                "shirt_chewing": "Stop chewing your shirt",
                "face_touching": "Stop touching your face",
                "default": "Bad habit detected"
            }
            message = messages.get(habit_type, messages["default"])
            os.system(f"say '{message}'")
    
    def _play_linux_sound(self, habit_type):
        """Play sound on Linux"""
        # Try different audio systems
        audio_commands = [
            "paplay /usr/share/sounds/alsa/Front_Left.wav",
            "aplay /usr/share/sounds/alsa/Front_Left.wav",
            "play /usr/share/sounds/sound-icons/bell.wav",
            "speaker-test -t sine -f 800 -l 1",
        ]
        
        for cmd in audio_commands:
            try:
                if os.system(cmd + " 2>/dev/null") == 0:
                    return
            except:
                continue
        
        # If all else fails, use terminal bell
        print("\a")
    
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
            "platform": sys.platform
        } 