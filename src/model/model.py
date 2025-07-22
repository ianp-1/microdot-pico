from model.hardware.led_manager import LEDManager
from model.hardware.button_manager import ButtonManager
from model.audio.eq_processor import EQProcessor
from model.websocket.web_socket_manager import WebSocketManager
from model.audio.voice_mode_manager import VoiceModeManager
from dsp import dsp_state

class AudioModel:
    def __init__(self):
        # Initialize components
        self.led_manager = LEDManager()
        self.eq_processor = EQProcessor()
        self.ws_manager = WebSocketManager()
        self.voice_mode_manager = VoiceModeManager()
        
        # Set up inter-component communication
        self._setup_callbacks()
        
        # Initialize button manager with actions
        button_config = {
            6: self.voice_mode_manager.toggle_feedback,  
            7: self.voice_mode_manager.toggle_ducking,  
            8: None,  # Reserved
            9: self.voice_mode_manager.toggle_mode
        }
        self.button_manager = ButtonManager(button_config)
        
        # Initial LED state
        self.led_manager.set_mode(self.voice_mode_manager.current_mode)
    
    def _setup_callbacks(self):
        # Voice mode changes update LEDs and notify WebSocket clients
        self.voice_mode_manager.add_change_callback(self.led_manager.set_mode)
        self.voice_mode_manager.add_change_callback(self.ws_manager.broadcast_mode_change)
        
        # Ducking and feedback changes notify WebSocket clients
        self.voice_mode_manager.add_ducking_callback(self.ws_manager.broadcast_ducking_change)
        self.voice_mode_manager.add_feedback_callback(self.ws_manager.broadcast_feedback_change)
        
        # Mute changes notify WebSocket clients
        self.voice_mode_manager.add_mute_callback(self.ws_manager.broadcast_mute_change)
        
        # EQ changes notify WebSocket clients
        self.eq_processor.add_update_callback(self.ws_manager.broadcast_eq_update)
        
        # DSP mixer changes notify WebSocket clients
        dsp_state.add_mixer_change_callback(self.ws_manager.broadcast_dsp_mixer_update)
    
    @property
    def ws_clients(self):
        return self.ws_manager.clients
    
    def set_target_eq(self, band, value, source='digital'):
        """Set target EQ value with source tracking"""
        self.eq_processor.set_target_eq(band, value, source)
    
    def set_dsp_mixer_param(self, param, value):
        """Set DSP mixer parameter"""
        from .utils import validate_dsp_mixer_update
        param, value = validate_dsp_mixer_update(param, value)
        dsp_state.set_param(param, value)
    
    async def monitor_dials_loop(self, interval_ms=100):
        await self.eq_processor.monitor_loop(interval_ms)