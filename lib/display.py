"""
Display manager for CLI interface and dashboard
"""

import time
import threading
import logging
from colorama import Fore, Style
from .utils import clear_screen, print_header, print_status, format_duration


class DisplayManager:
    """Handles CLI display and dashboard updates"""
    
    def __init__(self, refresh_rate=1.0, show_header=True):
        self.refresh_rate = refresh_rate
        self.show_header = show_header
        self.running = False
        self.display_thread = None
        self.stats_tracker = None
        self.logger = logging.getLogger(__name__)
        
        # Display state
        self.last_detection_class = None
        self.last_confidence = 0.0
        
    def set_stats_tracker(self, stats_tracker):
        """Set the statistics tracker for display"""
        self.stats_tracker = stats_tracker
    
    def start_display(self):
        """Start the display update thread"""
        if self.running:
            return
        
        self.running = True
        self.display_thread = threading.Thread(target=self._display_loop)
        self.display_thread.daemon = True
        self.display_thread.start()
        
        self.logger.info("Display manager started")
    
    def stop_display(self):
        """Stop the display update thread"""
        self.running = False
        if self.display_thread:
            self.display_thread.join(timeout=2)
        
        self.logger.info("Display manager stopped")
    
    def update_detection_info(self, detection_class, confidence):
        """Update the current detection information"""
        self.last_detection_class = detection_class
        self.last_confidence = confidence
    
    def _display_loop(self):
        """Main display update loop"""
        while self.running:
            try:
                self._render_dashboard()
                time.sleep(self.refresh_rate)
            except Exception as e:
                self.logger.error(f"Display error: {e}")
                time.sleep(1)
    
    def _render_dashboard(self):
        """Render the main dashboard"""
        # Clear screen
        clear_screen()
        
        # Header
        if self.show_header:
            print_header("HABIT MONITOR - REAL-TIME STATUS")
            print()
        
        # Get current statistics
        if self.stats_tracker:
            stats = self.stats_tracker.get_formatted_stats()
            
            # Session information
            print(f"{Fore.GREEN}Session Duration: {stats['session_duration']}")
            print()
            
            # Current habit status
            if stats['is_habit_active']:
                habit_name = self._get_habit_display_name(self.last_detection_class)
                print(f"{Fore.RED}🚨 HABIT DETECTED: {habit_name}")
                print(f"{Fore.RED}Current Session: {stats['current_habit_duration']}")
                if self.last_confidence > 0:
                    print(f"{Fore.RED}Confidence: {self.last_confidence:.1%}")
            else:
                print(f"{Fore.GREEN}✅ No Bad Habits Detected")
                if self.last_confidence > 0:
                    print(f"{Fore.GREEN}Last Confidence: {self.last_confidence:.1%}")
            
            print()
            
            # Statistics section
            print(f"{Fore.YELLOW}Statistics:")
            print(f"  Total Detections: {stats['total_detections']}")
            print(f"  Total Habit Time: {stats['total_habit_time']}")
            print(f"  Number of Sessions: {stats['habit_sessions_count']}")
            print(f"  Detection Rate: {stats['detection_rate']}")
            
            if stats['habit_sessions_count'] > 0:
                print(f"  Average Session: {stats['average_session_duration']}")
                print(f"  Habit Percentage: {stats['habit_percentage']}")
            
            print()
        
        # Control information
        print(f"{Fore.MAGENTA}Press Ctrl+C to stop monitoring")
        
        # Footer
        if self.show_header:
            print(f"{Fore.CYAN}{'='*60}")
    
    def _get_habit_display_name(self, habit_class):
        """Get a user-friendly display name for a habit class"""
        habit_names = {
            "about-to-chomp": "About to Chomp 👕",
            "chomping": "Chomping 🤏",
            "eating": "Eating 💅",
            "pondering": "Pondering 💅",
            "unknown": "Unknown Habit",
            "none": "None"
        }
        
        return habit_names.get(habit_class, f"Habit: {habit_class}")
    
    def show_startup_message(self):
        """Show startup message"""
        print_header("HABIT MONITOR CLI v1.0")
        print()
        print_status("Starting habit monitoring...", "info")
        print_status("Monitoring for bad habits...", "info")
        print()
    
    def show_shutdown_message(self, stats_tracker=None):
        """Show shutdown message with session summary"""
        print(f"\n{Fore.YELLOW}Stopping habit monitoring...")
        
        if stats_tracker:
            stats = stats_tracker.get_formatted_stats()
            
            print(f"\n{Fore.GREEN}Session Summary:")
            print(f"  Total Duration: {stats['session_duration']}")
            print(f"  Total Habit Time: {stats['total_habit_time']}")
            print(f"  Total Detections: {stats['total_detections']}")
            print(f"  Number of Sessions: {stats['habit_sessions_count']}")
            print(f"  Detection Rate: {stats['detection_rate']}")
            
            if stats['habit_sessions_count'] > 0:
                print(f"  Average Session: {stats['average_session_duration']}")
                print(f"  Habit Percentage: {stats['habit_percentage']}")
    
    def show_error(self, message):
        """Show error message"""
        print_status(f"Error: {message}", "error")
    
    def show_warning(self, message):
        """Show warning message"""
        print_status(f"Warning: {message}", "warning")
    
    def show_info(self, message):
        """Show info message"""
        print_status(message, "info")
    
    def show_success(self, message):
        """Show success message"""
        print_status(message, "success")
    
    def prompt_user(self, message, default=None):
        """Prompt user for input"""
        if default:
            prompt = f"{Fore.CYAN}{message} [{default}]: {Style.RESET_ALL}"
        else:
            prompt = f"{Fore.CYAN}{message}: {Style.RESET_ALL}"
        
        try:
            response = input(prompt)
            return response.strip() if response.strip() else default
        except KeyboardInterrupt:
            return None
    
    def show_configuration(self, config_info):
        """Show current configuration"""
        print_header("CURRENT CONFIGURATION")
        print()
        
        for key, value in config_info.items():
            print(f"{Fore.CYAN}{key}: {Fore.WHITE}{value}")
        
        print()
    
    def show_validation_results(self, results):
        """Show validation results"""
        print_header("SYSTEM VALIDATION")
        print()
        
        for check_name, result in results.items():
            if result.get("success", False):
                print(f"{Fore.GREEN}✅ {check_name}: {result.get('message', 'OK')}")
            else:
                print(f"{Fore.RED}❌ {check_name}: {result.get('message', 'Failed')}")
        
        print()
    
    def show_progress(self, message, progress=None):
        """Show progress message"""
        if progress is not None:
            print(f"{Fore.YELLOW}{message} [{progress:.1f}%]")
        else:
            print(f"{Fore.YELLOW}{message}...")
    
    def __enter__(self):
        """Context manager entry"""
        self.start_display()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_display() 