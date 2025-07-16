"""
App package - Audio Dashboard Application
Exposes main components for simplified imports
"""

# Configuration constants
from .config import (
    SERVER_PORT, SERVER_NAME, VERSION,
    WIFI_MODES, DEFAULT_AP_SSID, DEFAULT_AP_PASSWORD,
    EQ_BANDS, EQ_MIN_DB, EQ_MAX_DB,
    WS_MESSAGES, HTTP_OK, HTTP_BAD_REQUEST, HTTP_FORBIDDEN, HTTP_INTERNAL_ERROR
)

# Loggers
from .logger import main_logger, wifi_logger, ws_logger, api_logger

# Route handlers
from .routes.audio_routes import AudioRoutes
from .routes.wifi_routes import WiFiRoutes
from .websocket_handler import WebSocketHandler

# Utilities
from .utils import (
    ValidationError,
    validate_wifi_mode,
    validate_wifi_credentials, 
    validate_eq_update,
    create_success_response,
    create_error_response,
    safe_json_parse
)

# Export key components for easy importing
__all__ = [
    # Configuration constants
    'SERVER_PORT', 'SERVER_NAME', 'VERSION',
    'WIFI_MODES', 'DEFAULT_AP_SSID', 'DEFAULT_AP_PASSWORD',
    'EQ_BANDS', 'EQ_MIN_DB', 'EQ_MAX_DB',
    'WS_MESSAGES', 'HTTP_OK', 'HTTP_BAD_REQUEST', 'HTTP_FORBIDDEN', 'HTTP_INTERNAL_ERROR',
    # Route handlers
    'AudioRoutes', 'WiFiRoutes', 'WebSocketHandler',
    # Loggers
    'main_logger', 'wifi_logger', 'ws_logger', 'api_logger',
    # Utilities
    'ValidationError', 'validate_wifi_mode', 'validate_wifi_credentials',
    'validate_eq_update', 'create_success_response', 'create_error_response',
    'safe_json_parse'
]
