"""
Middleware utilities for request/response handling
"""
from .utils import create_error_response
from .logger import main_logger
import utime

class ErrorHandler:
    """Middleware for handling errors and exceptions"""
    
    def __init__(self, app):
        self.app = app
        self.logger = main_logger
    
    def handle_request_error(self, request, error):
        """Handle request processing errors"""
        self.logger.exception("Request error", error)
        return create_error_response("Internal server error"), 500
    
    def handle_validation_error(self, error):
        """Handle validation errors"""
        self.logger.warn(f"Validation error: {error}")
        return create_error_response(str(error)), 400

class RequestLogger:
    """Middleware for logging requests"""
    
    def __init__(self):
        self.logger = main_logger
    
    def log_request(self, request):
        """Log incoming request"""
        start_time = utime.ticks_ms()
        method = request.method
        path = request.path
        self.logger.debug(f"{method} {path} - Started")
        return start_time
    
    def log_response(self, request, start_time, status_code=200):
        """Log response completion"""
        end_time = utime.ticks_ms()
        duration = utime.ticks_diff(end_time, start_time)
        method = request.method
        path = request.path
        self.logger.info(f"{method} {path} - {status_code} ({duration}ms)")

# Global middleware instances
error_handler = ErrorHandler(None)
request_logger = RequestLogger()
