class VoiceModeManager:
    def __init__(self, modes=None, initial_index=4):
        self.voice_modes = modes or ["music", "live", "club", "monitor", "off"]
        self.current_mode_index = initial_index
        self.current_mode = self.voice_modes[self.current_mode_index]
        self.change_callbacks = []
    
    def add_change_callback(self, callback):
        self.change_callbacks.append(callback)
    
    def toggle_mode(self):
        self.current_mode_index = (self.current_mode_index + 1) % len(self.voice_modes)
        self.current_mode = self.voice_modes[self.current_mode_index]
        print(f"[MODE] Voice mode changed to: {self.current_mode}")
        
        # Notify all callbacks
        for callback in self.change_callbacks:
            callback(self.current_mode)
        
        return self.current_mode