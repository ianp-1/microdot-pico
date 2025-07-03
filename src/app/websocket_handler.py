"""
WebSocket message handlers
"""
import json
from .config import WS_MESSAGES
from .utils import ValidationError, validate_eq_update
from .logger import ws_logger

class WebSocketHandler:
    def __init__(self, model):
        self.model = model
        self.logger = ws_logger
        self.handlers = {
            WS_MESSAGES['PING']: self._handle_ping,
            WS_MESSAGES['VOICE_MODE_TOGGLE']: self._handle_voice_mode_toggle,
            WS_MESSAGES['EQ_UPDATE']: self._handle_eq_update,
            WS_MESSAGES['DUCKING_TOGGLE']: self._handle_ducking_toggle,
            WS_MESSAGES['FEEDBACK_TOGGLE']: self._handle_feedback_toggle,
            WS_MESSAGES['MUTE_TOGGLE']: self._handle_mute_toggle,
            WS_MESSAGES['GET_STATE']: self._handle_get_state,
        }
    
    async def handle_connection(self, ws):
        """Handle WebSocket connection lifecycle"""
        self.model.ws_manager.add_client(ws)
        
        try:
            await self._send_initial_state(ws)
            await self._message_loop(ws)
        except Exception as e:
            self.logger.exception("Client disconnected", e)
        finally:
            self.model.ws_manager.remove_client(ws)
    
    async def _send_initial_state(self, ws):
        """Send initial state to newly connected client"""
        from dsp.dsp_state import get_param
        
        initial_state = {
            'type': WS_MESSAGES['INITIAL_STATE'],
            'mode': self.model.voice_mode_manager.current_mode,
            'feedback': self.model.voice_mode_manager.feedback_enabled,
            'ducking': self.model.voice_mode_manager.ducking_enabled,
            'mute': get_param('mute'),
            'eq': self._get_eq_state()
        }
        await ws.send(json.dumps(initial_state))
        self.logger.info("Sent initial state to client")
    
    async def _message_loop(self, ws):
        """Main message processing loop"""
        while True:
            message = await ws.receive()
            if message:
                await self._process_message(ws, message)
    
    async def _process_message(self, ws, message):
        """Process incoming WebSocket message"""
        try:
            data = json.loads(message)
            action = data.get('action')
            
            handler = self.handlers.get(action)
            if handler:
                await handler(ws, data)
            else:
                self.logger.warn(f"Unknown action: {action}")
                
        except (ValueError, json.JSONDecodeError) as e:
            self.logger.error(f"Error parsing message: {e}")
        except Exception as e:
            self.logger.exception("Error processing message", e)
    
    async def _handle_ping(self, ws, data):
        """Handle ping message"""
        await ws.send(json.dumps({
            'type': WS_MESSAGES['PONG'],
            'timestamp': data.get('timestamp')
        }))
    
    async def _handle_voice_mode_toggle(self, ws, data):
        """Handle voice mode toggle"""
        new_mode = self.model.voice_mode_manager.toggle_mode()
        self.logger.info(f"Voice mode toggled to: {new_mode}")
    
    async def _handle_eq_update(self, ws, data):
        """Handle EQ update"""
        try:
            band = data.get('band')
            value = data.get('value')
            
            # Validate input
            band, value = validate_eq_update(band, value)
            
            # Update model
            self.model.set_target_eq(band, value, source='digital')
            self.logger.info(f"EQ update: {band} = {value}dB (digital)")
            
        except ValidationError as e:
            self.logger.error(f"EQ validation error: {e}")
    
    async def _handle_ducking_toggle(self, ws, data):
        """Handle ducking toggle"""
        new_state = self.model.voice_mode_manager.toggle_ducking()
        self.logger.info(f"Ducking toggled to: {new_state}")
    
    async def _handle_feedback_toggle(self, ws, data):
        """Handle feedback toggle"""
        new_state = self.model.voice_mode_manager.toggle_feedback()
        self.logger.info(f"Feedback toggled to: {new_state}")
    
    async def _handle_mute_toggle(self, ws, data):
        """Handle mute toggle"""
        new_state = self.model.voice_mode_manager.toggle_mute()
        self.logger.info(f"Mute toggled to: {new_state}")
    
    async def _handle_get_state(self, ws, data):
        """Handle get current state request"""
        state_data = {
            'type': WS_MESSAGES['INITIAL_STATE'],
            'mode': self.model.voice_mode_manager.current_mode,
            'eq': self._get_eq_state()
        }
        await ws.send(json.dumps(state_data))
        self.logger.info("Sent current state")
    
    def _get_eq_state(self):
        """Get current EQ state"""
        return {
            'low': self.model.eq_processor.live_db['low'],
            'mid': self.model.eq_processor.live_db['mid'], 
            'high': self.model.eq_processor.live_db['high']
        }
