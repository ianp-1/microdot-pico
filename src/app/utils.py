"""
Simple utilities for validation and responses
"""
from .config import WIFI_MODES, MIN_PASSWORD_LENGTH, EQ_BANDS, EQ_MIN_DB, EQ_MAX_DB

class ValidationError(Exception):
    """Custom validation error"""
    pass

def validate_wifi_mode(mode):
    """Validate WiFi mode"""
    if mode not in WIFI_MODES:
        raise ValidationError(f"Invalid mode. Must be one of: {', '.join(WIFI_MODES)}")
    return mode

def validate_wifi_credentials(ssid, password):
    """Validate WiFi credentials"""
    if not ssid or not ssid.strip():
        raise ValidationError("SSID is required")
    
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
    
    return ssid.strip(), password

def validate_eq_update(band, value):
    """Validate EQ band and value"""
    if band not in EQ_BANDS:
        raise ValidationError(f"Invalid EQ band: {band}")
    
    if not isinstance(value, (int, float)):
        raise ValidationError("EQ value must be a number")
    
    if not (EQ_MIN_DB <= value <= EQ_MAX_DB):
        raise ValidationError(f"EQ value must be between {EQ_MIN_DB} and {EQ_MAX_DB} dB")
    
    return band, float(value)

def create_success_response(message, data=None):
    """Create standardized success response"""
    response = {'success': True, 'message': message}
    if data:
        response.update(data)
    return response

def create_error_response(message):
    """Create standardized error response"""
    return {'success': False, 'message': message}

def safe_json_parse(request_body):
    """Safely parse JSON from request body"""
    import json
    try:
        return json.loads(request_body.decode('utf-8'))
    except (ValueError, json.JSONDecodeError):
        raise ValidationError("Invalid JSON data")
