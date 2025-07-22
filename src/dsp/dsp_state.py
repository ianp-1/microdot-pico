import _thread
from .dualcore_withdsp_nonblock import SetMixerParam

# Core 0 to Core 1 (DSP) communication

dsp_params = {
    'volume': 100,
    'mute': False,
    'master_gain': 1.0,
    'gain_ch1': 0.5,
    'gain_ch2': 0.5,
    'pan': 0.0,
    'audio_enabled': True
}

lock = _thread.allocate_lock()
mixer_change_callbacks = []

def add_mixer_change_callback(callback):
    """Add a callback to be called when mixer parameters change"""
    mixer_change_callbacks.append(callback)

def set_param(key, value):
    with lock:
        if key in dsp_params:
            dsp_params[key] = value
            # Update DSP audio parameters immediately
            _update_dsp_audio_params()
            print(f"[DSP_STATE] Set {key} = {value}")
            
            # Notify callbacks if mixer parameter changed
            if key in ['master_gain', 'gain_ch1', 'gain_ch2', 'pan']:
                _notify_mixer_change()
            
            return True
        else:
            print(f"[DSP_STATE] Warning: Unknown parameter {key}")
            return False

def _notify_mixer_change():
    """Internal function to notify all callbacks of mixer parameter changes"""
    mixer_params = {
        'master_gain': dsp_params['master_gain'],
        'gain_ch1': dsp_params['gain_ch1'],
        'gain_ch2': dsp_params['gain_ch2'],
        'pan': dsp_params['pan']
    }
    
    for callback in mixer_change_callbacks:
        try:
            callback(mixer_params)
        except Exception as e:
            print(f"[DSP_STATE] Error in mixer callback: {e}")

def get_param(key):
    with lock:
        return dsp_params.get(key)

def get_all_params():
    """Thread-safe get all parameters from Core 0"""
    with lock:
        return dsp_params.copy()

def _update_dsp_audio_params():
    """Internal function to update dsp_audio.py parameters"""
    # This is called from within the lock, so it's thread-safe
    SetMixerParam(
        master_gain=dsp_params['master_gain'],
        gain_ch1=dsp_params['gain_ch1'],
        gain_ch2=dsp_params['gain_ch2'],
        pan=dsp_params['pan']
    )

def core1_update_params():
    """Called from Core 1 to get latest parameters"""
    with lock:
        # Update DSP audio parameters on Core 1
        _update_dsp_audio_params()
        return dsp_params.copy()

def initialize_dsp_state():
    """Initialize DSP state on startup"""
    print("[DSP_STATE] Initializing DSP state...")
    with lock:
        _update_dsp_audio_params()
    print("[DSP_STATE] DSP state initialized")
