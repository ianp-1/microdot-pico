from lib.microdot import Microdot, Response, send_file, websocket
from lib.microdot.websocket import with_websocket
import lib.mm_wlan as mm_wlan
import uasyncio as asyncio
from model.model import AudioModel
import network
import json

USE_AP_MODE = True

ssid = 'SUGA Guest 5G'
password = 'suga22wifi'

app = Microdot()
model = AudioModel()

@app.route('/')
def index(request):
    return send_file('templates/dashboard.html')

@app.route('/static/<path:path>')
def static_files(request, path):
    if path.endswith('.js'):
        return send_file(f'static/{path}', content_type='application/javascript')
    return send_file(f'static/{path}')

@app.post('/toggle-voice-mode')
def toggle_mode(request):
    mode = model.voice_mode_manager.toggle_mode()
    return f'<span id="currentMode">Current Mode: {mode}</span>'

@app.route('/current-state-json')
def current_state_json(request):
    """Return current system state as JSON"""
    return {
        'mode': model.voice_mode_manager.current_mode,
        'eq': {
            'low': model.eq_processor.live_db['low'],
            'mid': model.eq_processor.live_db['mid'], 
            'high': model.eq_processor.live_db['high']
        }
    }

@app.route('/ws')
@with_websocket
async def websocket_handler(request, ws):
    model.ws_manager.add_client(ws)
    
    # Send initial state to newly connected client
    try:
        initial_state = {
            'type': 'initial_state',
            'mode': model.voice_mode_manager.current_mode,
            'eq': {
                'low': model.eq_processor.live_db['low'],
                'mid': model.eq_processor.live_db['mid'], 
                'high': model.eq_processor.live_db['high']
            }
        }
        await ws.send(json.dumps(initial_state))
        print(f"[WS] Sent initial state to client: {initial_state}")
    except Exception as e:
        print(f"[WS] Error sending initial state: {e}")
    
    try:
        while True:
            message = await ws.receive()
            
            if message:
                try:
                    # Handle URL-encoded form data from HTMX
                    if isinstance(message, str) and '=' in message and not message.startswith('{'):
                        data = dict(item.split('=') for item in message.split('&'))
                    else:
                        # Handle JSON data
                        data = json.loads(message)
                    
                    action = data.get('action')
                    
                    # Add this simple ping test
                    if action == 'ping':
                        await ws.send(json.dumps({
                            'type': 'pong', 
                            'timestamp': data.get('timestamp')
                        }))
                        continue
                    
                    if action == 'toggle_voice_mode':
                        new_mode = model.voice_mode_manager.toggle_mode()
                        print(f"[WS] Voice mode toggled to: {new_mode}")
                        
                    elif action == 'eq_update':
                        band = data.get('band')
                        value = data.get('value')
                        if band and value is not None:
                            # Set digital control priority for this band
                            model.set_target_eq(band, value, source='digital')
                            print(f"[WS] EQ update: {band} = {value}dB (digital)")
                            
                    elif action == 'get_current_state':
                        # Send current state back to client
                        state_data = {
                            'type': 'initial_state',
                            'mode': model.voice_mode_manager.current_mode,
                            'eq': {
                                'low': model.eq_processor.live_db['low'],
                                'mid': model.eq_processor.live_db['mid'], 
                                'high': model.eq_processor.live_db['high']
                            }
                        }
                        await ws.send(json.dumps(state_data))
                        print(f"[WS] Sent current state")
                        
                except (ValueError, json.JSONDecodeError) as e:
                    print(f"[WS] Error parsing message: {e}")
                    
    except Exception as e:
        print(f"[WS] Client disconnected: {e}")
    finally:
        model.ws_manager.remove_client(ws)

@app.route('/current-eq-json')
def current_eq_json(request):
    """Return current EQ values as JSON"""
    return {
        'low': model.eq_processor.live_db['low'],
        'mid': model.eq_processor.live_db['mid'], 
        'high': model.eq_processor.live_db['high']
    }

async def setup_network():
    if USE_AP_MODE:
        ap = network.WLAN(network.AP_IF)
        ap.config(essid='PicoW', password='12345678')
        ap.active(True)
        while not ap.active():
            await asyncio.sleep(1)
        print("Access Point active:", ap.ifconfig())
    else:
        mm_wlan.connect_to_network(ssid, password)
        print("Connected to WLAN")


# server start
async def main():
    asyncio.create_task(model.monitor_dials_loop())
    await app.start_server(port=80)

# run everything
asyncio.run(main())