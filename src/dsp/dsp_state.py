import _thread

# Core 0 to Core 1 (DSP) communication

dsp_params = {
    'volume': 100,
    'mute': False,
}

lock = _thread.allocate_lock()

def set_param(key, value):
    with lock:
        dsp_params[key] = value

def get_param(key):
    with lock:
        return dsp_params.get(key)
