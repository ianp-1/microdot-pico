class VoiceModeManager:
    def __init__(self, modes=None, initial_index=4):
        self.voice_modes = modes or ["music", "live", "club", "monitor", "off"]
        self.current_mode_index = initial_index
        self.current_mode = self.voice_modes[self.current_mode_index]
        self.change_callbacks = []
        
        # Add ducking and feedback state
        self.ducking_enabled = False
        self.feedback_enabled = False
        self.ducking_callbacks = []
        self.feedback_callbacks = []
        
        # Add mute state
        self.muted = False
        self.mute_callbacks = []
    
    def add_change_callback(self, callback):
        self.change_callbacks.append(callback)
    
    def add_ducking_callback(self, callback):
        self.ducking_callbacks.append(callback)
    
    def add_feedback_callback(self, callback):
        self.feedback_callbacks.append(callback)
    
    def add_mute_callback(self, callback):
        self.mute_callbacks.append(callback)
    
    def toggle_mode(self):
        self.current_mode_index = (self.current_mode_index + 1) % len(self.voice_modes)
        self.current_mode = self.voice_modes[self.current_mode_index]
        print(f"[MODE] Voice mode changed to: {self.current_mode}")
        
        # Notify all callbacks
        for callback in self.change_callbacks:
            callback(self.current_mode)
        
        return self.current_mode
    
    def toggle_ducking(self):
        self.ducking_enabled = not self.ducking_enabled
        print(f"[DUCKING] Ducking toggled to: {self.ducking_enabled}")
        
        # Notify all callbacks
        for callback in self.ducking_callbacks:
            callback(self.ducking_enabled)
        
        return self.ducking_enabled
    
    def toggle_feedback(self):
        self.feedback_enabled = not self.feedback_enabled
        print(f"[FEEDBACK] Feedback toggled to: {self.feedback_enabled}")
        
        # Notify all callbacks
        for callback in self.feedback_callbacks:
            callback(self.feedback_enabled)
        
        return self.feedback_enabled
    
    def get_mute_status(self):
        return self.muted

    def toggle_mute(self):
        self.muted = not self.muted
        print(f"[MUTE] Mute toggled to: {self.muted}")
        
        # Notify all callbacks
        for callback in self.mute_callbacks:
            callback(self.muted)
        
        return self.muted