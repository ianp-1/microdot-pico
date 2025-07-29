"""
UART Audio Control Manager

Manages UART-based audio controls (gain, pan, master) with state tracking
and callback notifications, similar to the EQ processor.
"""
from model.utils import UART_PARAMS

class UARTManager:
    def __init__(self):
        # Current state of UART controls
        self.state = {
            "master": 0.0,
            "g1": 0.0,
            "g2": 0.0,
            "pan": 0.0,
            "bl": 1.0,  # Bass left (default to 1.0 for flat response)
            "tl": 1.0,  # Treble left
            "br": 1.0,  # Bass right  
            "tr": 1.0   # Treble right
        }
        
        # Callbacks for state changes
        self._update_callbacks = []
    
    def add_update_callback(self, callback):
        """Add callback to be called when UART state changes"""
        self._update_callbacks.append(callback)
    
    def remove_update_callback(self, callback):
        """Remove callback from update notifications"""
        if callback in self._update_callbacks:
            self._update_callbacks.remove(callback)
    
    def update_param(self, param, value):
        """Update a UART parameter and notify callbacks"""
        if param in self.state:
            old_value = self.state[param]
            self.state[param] = float(value)
            
            # Only notify if value actually changed
            if old_value != self.state[param]:
                self._notify_callbacks()
    
    def get_state(self):
        """Get current UART state"""
        return self.state.copy()
    
    def reset_state(self):
        """Reset all UART parameters to default values"""
        for param in self.state:
            self.state[param] = 0.0
        self._notify_callbacks()
    
    def _notify_callbacks(self):
        """Notify all registered callbacks of state change"""
        for callback in self._update_callbacks:
            try:
                callback(self.state)
            except Exception as e:
                # Log error but don't let one callback failure affect others
                print(f"Error in UART callback: {e}")
