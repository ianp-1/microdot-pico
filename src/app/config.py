# Server Configuration
SERVER_PORT = 80
SERVER_NAME = "Audio Dashboard"
VERSION = "1.0.0"

# WiFi Configuration
WIFI_MODES = ['station', 'ap', 'dual']
MIN_PASSWORD_LENGTH = 8
DEFAULT_AP_SSID = 'PicoW-Audio'
DEFAULT_AP_PASSWORD = 'picowifi'
WIFI_SCAN_TIMEOUT = 10  # seconds

# EQ Configuration  
EQ_BANDS = ['low', 'mid', 'high']
EQ_MIN_DB = -12
EQ_MAX_DB = 12
EQ_DEFAULT_DB = 0

# WebSocket Message Types
WS_MESSAGES = {
    'PING': 'ping',
    'PONG': 'pong',
    'INITIAL_STATE': 'initial_state',
    'VOICE_MODE_TOGGLE': 'toggle_voice_mode',
    'EQ_UPDATE': 'eq_update',
    'DUCKING_TOGGLE': 'toggle_ducking',
    'FEEDBACK_TOGGLE': 'toggle_feedback',
    'MUTE_TOGGLE': 'toggle_mute',
    'GET_STATE': 'get_current_state'
}

# HTTP Status Codes
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_FORBIDDEN = 403
HTTP_INTERNAL_ERROR = 500

# Logging Configuration
LOG_LEVEL_DEBUG = 0
LOG_LEVEL_INFO = 1
LOG_LEVEL_WARN = 2
LOG_LEVEL_ERROR = 3
DEFAULT_LOG_LEVEL = LOG_LEVEL_INFO
