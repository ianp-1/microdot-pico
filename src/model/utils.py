"""
Utilities for model-layer data validation.
"""

# Configuration for UART command parameters
UART_PARAMS = ['g1', 'g2', 'pan', 'master', 'bl', 'tl', 'br', 'tr']
UART_GAIN_MIN = 0.0
UART_GAIN_MAX = 2.0
UART_PAN_MIN = -1.0
UART_PAN_MAX = 1.0
UART_EQ_MIN = 0.0
UART_EQ_MAX = 10.0

class ValidationError(Exception):
    """Custom validation error for model-related data."""
    pass

def validate_uart_command(param, value):
    """Validate UART command parameter and value"""
    if param not in UART_PARAMS:
        raise ValidationError(f"Invalid UART command parameter: {param}")
    
    if not isinstance(value, (int, float)):
        raise ValidationError("UART command value must be a number")
    
    # Different validation ranges for different parameters
    if param == 'pan':
        if not (UART_PAN_MIN <= value <= UART_PAN_MAX):
            raise ValidationError(f"Pan value must be between {UART_PAN_MIN} and {UART_PAN_MAX}")
    elif param in ['bl', 'tl', 'br', 'tr']:  # EQ parameters
        if not (UART_EQ_MIN <= value <= UART_EQ_MAX):
            raise ValidationError(f"EQ value must be between {UART_EQ_MIN} and {UART_EQ_MAX}")
    else:  # gain parameters
        if not (UART_GAIN_MIN <= value <= UART_GAIN_MAX):
            raise ValidationError(f"Gain value must be between {UART_GAIN_MIN} and {UART_GAIN_MAX}")
    
    return param, float(value)
