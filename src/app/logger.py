"""
Simple logging utility for consistent logging across the application
"""
import utime

class Logger:
    """Simple logger with timestamp and context"""
    
    DEBUG = 0
    INFO = 1  
    WARN = 2
    ERROR = 3
    
    level_names = {
        DEBUG: "DEBUG",
        INFO: "INFO", 
        WARN: "WARN",
        ERROR: "ERROR"
    }
    
    def __init__(self, context="MAIN", level=INFO):
        self.context = context
        self.level = level
    
    def _log(self, level, message):
        """Internal logging method"""
        if level >= self.level:
            level_name = self.level_names.get(level, "UNKNOWN")
            timestamp = utime.ticks_ms()
            print(f"[{timestamp}] [{level_name}] [{self.context}] {message}")
    
    def debug(self, message):
        """Log debug message"""
        self._log(self.DEBUG, message)
    
    def info(self, message):
        """Log info message"""
        self._log(self.INFO, message)
    
    def warn(self, message):
        """Log warning message"""
        self._log(self.WARN, message)
    
    def error(self, message):
        """Log error message"""
        self._log(self.ERROR, message)
    
    def exception(self, message, exception):
        """Log exception with error message"""
        self._log(self.ERROR, f"{message}: {exception}")

# Create module-level logger instances
main_logger = Logger("MAIN")
wifi_logger = Logger("WiFi")
ws_logger = Logger("WS")
api_logger = Logger("API")
