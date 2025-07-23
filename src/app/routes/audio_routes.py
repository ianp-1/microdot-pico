"""
API route handlers for audio system controls
"""
from ..utils import create_success_response, create_error_response, ValidationError, validate_eq_update, safe_json_parse
from model.utils import validate_uart_command
from ..logger import api_logger
from ..config import SERVER_NAME, VERSION
import utime

class AudioRoutes:
    """Handler for audio-related API routes"""
    
    def __init__(self, model, uart_service):
        self.model = model
        self.uart_service = uart_service
        self.logger = api_logger
    
    def toggle_voice_mode(self, request):
        """Toggle voice mode and return updated state"""
        try:
            mode = self.model.voice_mode_manager.toggle_mode()
            self.logger.info(f"Voice mode toggled to: {mode}")
            return f'<span id="currentMode">Current Mode: {mode}</span>'
        except Exception as e:
            self.logger.exception("Voice mode toggle failed", e)
            return "Error: Failed to toggle voice mode"
    
    def toggle_ducking(self, request):
        """Toggle ducking and return updated state"""
        try:
            enabled = self.model.voice_mode_manager.toggle_ducking()
            self.logger.info(f"Ducking toggled to: {'on' if enabled else 'off'}")
            return f'<span id="musicDucking">Ducking: {"on" if enabled else "off"}</span>'
        except Exception as e:
            self.logger.exception("Ducking toggle failed", e)
            return "Error: Failed to toggle ducking"
    
    def toggle_feedback(self, request):
        """Toggle feedback and return updated state"""
        try:
            enabled = self.model.voice_mode_manager.toggle_feedback()
            self.logger.info(f"Feedback toggled to: {'on' if enabled else 'off'}")
            return f'<span id="feedback">Feedback: {"on" if enabled else "off"}</span>'
        except Exception as e:
            self.logger.exception("Feedback toggle failed", e)
            return "Error: Failed to toggle feedback"
    
    def toggle_mute(self, request):
        """Toggle mute and return updated state"""
        try:
            muted = self.model.voice_mode_manager.toggle_mute()
            self.logger.info(f"Mute toggled to: {'muted' if muted else 'unmuted'}")
            return f'<span id="muteStatus">{"muted" if muted else "unmuted"}</span>'
        except Exception as e:
            self.logger.exception("Mute toggle failed", e)
            return "Error: Failed to toggle mute"
    
    def get_current_state_json(self, request):
        """Return current system state as JSON"""
        try:
            return {
                'mode': self.model.voice_mode_manager.current_mode,
                'ducking': self.model.voice_mode_manager.ducking_enabled,
                'feedback': self.model.voice_mode_manager.feedback_enabled,
                'muted': self.model.voice_mode_manager.get_mute_status(),
                'eq': self._get_eq_state()
            }
        except Exception as e:
            self.logger.exception("Failed to get current state", e)
            return create_error_response("Failed to get current state")
    
    def get_current_eq_json(self, request):
        """Return current EQ values as JSON"""
        try:
            return self._get_eq_state()
        except Exception as e:
            self.logger.exception("Failed to get EQ state", e)
            return create_error_response("Failed to get EQ state")
    
    def update_eq(self, request):
        """Update EQ values via HTTP POST"""
        try:
            data = safe_json_parse(request.body)
            band = data.get('band')
            value = data.get('value')
            source = data.get('source', 'web')
            
            # Validate input
            band, value = validate_eq_update(band, value)
            
            # Update model
            self.model.set_target_eq(band, value, source=source)
            self.logger.info(f"EQ updated: {band} = {value}dB (source: {source})")
            
            return create_success_response(
                f"EQ updated: {band} = {value}dB",
                {'band': band, 'value': value, 'source': source}
            )
            
        except ValidationError as e:
            return create_error_response(str(e))
        except Exception as e:
            self.logger.exception("EQ update failed", e)
            return create_error_response("Failed to update EQ")
    
    def health_check(self, request):
        """Health check endpoint"""
        try:
            return create_success_response("System is healthy", {
                'server': SERVER_NAME,
                'version': VERSION,
                'uptime_ms': utime.ticks_ms(),
                'status': 'ok'
            })
        except Exception as e:
            self.logger.exception("Health check failed", e)
            return create_error_response("Health check failed")
    
    def system_info(self, request):
        """Return system information"""
        try:
            import gc
            import micropython
            
            # Get memory info
            gc.collect()
            free_mem = gc.mem_free()
            allocated_mem = gc.mem_alloc()
            
            return create_success_response("System information", {
                'server': SERVER_NAME,
                'version': VERSION,
                'uptime_ms': utime.ticks_ms(),
                'memory': {
                    'free': free_mem,
                    'allocated': allocated_mem,
                    'total': free_mem + allocated_mem
                },
                'voice_mode': self.model.voice_mode_manager.current_mode,
                'muted': self.model.voice_mode_manager.get_mute_status(),
                'eq_state': self._get_eq_state()
            })
        except Exception as e:
            self.logger.exception("System info failed", e)
            return create_error_response("Failed to get system information")
    
    def update_dsp_mixer(self, request):
        """Update DSP mixer parameters"""
        try:
            # Parse JSON body
            data = safe_json_parse(request.body)
            if not data:
                return create_error_response("Invalid JSON format")
            
            # Validate required parameters
            param = data.get('param')
            value = data.get('value')
            
            if not param or value is None:
                return create_error_response("Missing required parameters: param, value")
            
            # Validate and send command
            param, value = validate_uart_command(param, value)
            self.uart_service.send_command(param, value)
            
            self.logger.info(f"DSP mixer updated: {param} = {value}")
            return create_success_response(f"DSP mixer {param} updated successfully", {
                'param': param,
                'value': value
            })
            
        except ValidationError as e:
            self.logger.warn(f"DSP mixer validation error: {e}")
            return create_error_response(str(e))
        except Exception as e:
            self.logger.exception("DSP mixer update failed", e)
            return create_error_response("Failed to update DSP mixer")
    
    def _get_eq_state(self):
        """Get current EQ state"""
        return {
            'low': self.model.eq_processor.live_db['low'],
            'mid': self.model.eq_processor.live_db['mid'], 
            'high': self.model.eq_processor.live_db['high']
        }
