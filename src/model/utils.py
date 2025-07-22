"""
Utilities for model-layer data validation.
"""

# Configuration for DSP mixer parameters
DSP_MIXER_PARAMS = ['master_gain', 'gain_ch1', 'gain_ch2', 'pan']
DSP_GAIN_MIN = 0.0
DSP_GAIN_MAX = 2.0
DSP_PAN_MIN = -1.0
DSP_PAN_MAX = 1.0

class ValidationError(Exception):
    """Custom validation error for model-related data."""
    pass

def validate_dsp_mixer_update(param, value):
    """Validate DSP mixer parameter and value"""
    if param not in DSP_MIXER_PARAMS:
        raise ValidationError(f"Invalid DSP mixer parameter: {param}")
    
    if not isinstance(value, (int, float)):
        raise ValidationError("DSP mixer value must be a number")
    
    # Different validation ranges for different parameters
    if param == 'pan':
        if not (DSP_PAN_MIN <= value <= DSP_PAN_MAX):
            raise ValidationError(f"Pan value must be between {DSP_PAN_MIN} and {DSP_PAN_MAX}")
    else:  # gain parameters
        if not (DSP_GAIN_MIN <= value <= DSP_GAIN_MAX):
            raise ValidationError(f"Gain value must be between {DSP_GAIN_MIN} and {DSP_GAIN_MAX}")
    
    return param, float(value)
