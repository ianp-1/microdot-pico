import json
import uasyncio as asyncio

class WebSocketManager:
    def __init__(self):
        self.clients = set()
    
    def add_client(self, ws):
        self.clients.add(ws)
    
    def remove_client(self, ws):
        self.clients.discard(ws)
    
    def broadcast_mode_change(self, mode):
        msg = json.dumps({"type": "mode", "mode": mode})
        self._broadcast(msg)
    
    def broadcast_ducking_change(self, enabled):
        msg = json.dumps({"type": "ducking", "enabled": enabled})
        self._broadcast(msg)
    
    def broadcast_feedback_change(self, enabled):
        msg = json.dumps({"type": "feedback", "enabled": enabled})
        self._broadcast(msg)
    
    def broadcast_mute_change(self, enabled):
        msg = json.dumps({"type": "mute", "enabled": enabled})
        self._broadcast(msg)
    
    def broadcast_dsp_mixer_update(self, mixer_params):
        msg = json.dumps({
            "type": "dsp_mixer",
            "master_gain": mixer_params["master_gain"],
            "gain_ch1": mixer_params["gain_ch1"],
            "gain_ch2": mixer_params["gain_ch2"],
            "pan": mixer_params["pan"]
        })
        self._broadcast(msg)
    
    def broadcast_eq_update(self, callback_data):
        # Handle both old format (just eq data) and new format (eq + control sources)
        if isinstance(callback_data, dict) and 'eq' in callback_data:
            eq_data = callback_data['eq']
            control_sources = callback_data.get('control_sources', {})
        else:
            # Backward compatibility - callback_data is just the eq values
            eq_data = callback_data
            control_sources = {}
        
        msg = json.dumps({
            "type": "dial",
            "low": eq_data["low"],
            "mid": eq_data["mid"],
            "high": eq_data["high"],
            "control_sources": control_sources
        })
        self._broadcast(msg)
    
    def _broadcast(self, message):
        for ws in list(self.clients):
            try:
                asyncio.create_task(ws.send(message))
            except:
                self.clients.discard(ws)