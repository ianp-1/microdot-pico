from lib.microdot import Microdot, Response, send_file, websocket
from lib.microdot.websocket import with_websocket
import uasyncio as asyncio
from model.model import AudioModel
from model.wifi_manager import WiFiManager
import json

app = Microdot()
model = AudioModel()
wifi_manager = WiFiManager()

@app.route('/')
def index(request):
    return send_file('templates/dashboard.html')

@app.route('/static/<path:path>')
def static_files(request, path):
    if '..' in path:
        return Response("Forbidden", status_code=403)

    # Guess content type
    if path.endswith('.js'):
        content_type = 'application/javascript'
    elif path.endswith('.css'):
        content_type = 'text/css'
    elif path.endswith('.svg'):
        content_type = 'image/svg+xml'
    elif path.endswith('.html'):
        content_type = 'text/html'
    elif path.endswith('.json'):
        content_type = 'application/json'
    else:
        content_type = 'application/octet-stream'

    # Try serving .gz version first
    gz_path = f'static/{path}.gz'
    try:
        return send_file(gz_path, content_type=content_type, compressed=True)
    except OSError:
        pass  # Fallback to normal

    # Fall back to uncompressed version
    normal_path = f'static/{path}'
    try:
        return send_file(normal_path, content_type=content_type)
    except OSError as e:
        print(f"[STATIC] File not found: {path} - {e}")
        return Response("File not found", status_code=404)


@app.post('/toggle-voice-mode')
def toggle_mode(request):
    mode = model.voice_mode_manager.toggle_mode()
    return f'<span id="currentMode">Current Mode: {mode}</span>'

@app.post('/trigger-ducking')
def toggle_ducking(request):
    enabled = model.voice_mode_manager.toggle_ducking()
    return f'<span id="musicDucking">Ducking: {"on" if enabled else "off"}</span>'

@app.post('/trigger-feedback')
def toggle_feedback(request):
    enabled = model.voice_mode_manager.toggle_feedback()
    return f'<span id="feedback">Feedback: {"on" if enabled else "off"}</span>'

@app.route('/current-state-json')
def current_state_json(request):
    """Return current system state as JSON"""
    return {
        'mode': model.voice_mode_manager.current_mode,
        'ducking': model.voice_mode_manager.ducking_enabled,
        'feedback': model.voice_mode_manager.feedback_enabled,
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
            'feedback': model.voice_mode_manager.feedback_enabled,
            'ducking': model.voice_mode_manager.ducking_enabled,
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
                    # Handle JSON data only
                    data = json.loads(message)
                    action = data.get('action')
                    
                    # Ping test
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
                    
                    elif action == 'toggle_ducking':
                        new_state = model.voice_mode_manager.toggle_ducking()
                        print(f"[WS] Ducking toggled to: {new_state}")
                        
                    elif action == 'toggle_feedback':
                        new_state = model.voice_mode_manager.toggle_feedback()
                        print(f"[WS] Feedback toggled to: {new_state}")
                            
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

# WiFi Configuration Endpoints
@app.route('/wifi/status')
def wifi_status(request):
    """Return current WiFi status"""
    return wifi_manager.get_status()

@app.post('/wifi/connect-station')
async def wifi_connect_station(request):
    """Connect to a WiFi network in station mode"""
    try:
        # Parse JSON data from request body
        data = json.loads(request.body.decode('utf-8'))
        ssid = data.get('ssid', '').strip()
        password = data.get('password', '')
        
        if not ssid:
            return {'success': False, 'message': 'SSID is required'}
        
        result = await wifi_manager.connect_to_station(ssid, password)
        return result
        
    except (ValueError, KeyError) as e:
        print(f"[WiFi] JSON parse error: {e}")
        return {'success': False, 'message': 'Invalid request data'}
    except Exception as e:
        print(f"[WiFi] Station connect error: {e}")
        return {'success': False, 'message': 'Connection failed'}

@app.post('/wifi/start-ap')
async def wifi_start_ap(request):
    """Start the device as an access point"""
    try:
        # Parse JSON data from request body
        data = json.loads(request.body.decode('utf-8'))
        ssid = data.get('ssid', 'PicoW-Audio').strip()
        password = data.get('password', 'picowifi')
        
        if len(password) < 8:
            return {'success': False, 'message': 'Password must be at least 8 characters'}
        
        result = await wifi_manager.start_access_point(ssid, password)
        return result
        
    except (ValueError, KeyError) as e:
        print(f"[WiFi] JSON parse error: {e}")
        return {'success': False, 'message': 'Invalid request data'}
    except Exception as e:
        print(f"[WiFi] AP start error: {e}")
        return {'success': False, 'message': 'Failed to start Access Point'}

@app.route('/wifi/scan')
def wifi_scan(request):
    """Scan for available WiFi networks"""
    return wifi_manager.scan_networks()

@app.post('/wifi/restart')
def wifi_restart(request):
    """Restart the device to apply WiFi configuration changes"""
    import machine
    try:
        print("[WiFi] Device restart requested")
        # Small delay to allow response to be sent
        import uasyncio as asyncio
        async def delayed_restart():
            await asyncio.sleep(1)
            machine.reset()
        asyncio.create_task(delayed_restart())
        return {'success': True, 'message': 'Device restarting...'}
    except Exception as e:
        print(f"[WiFi] Restart error: {e}")
        return {'success': False, 'message': 'Failed to restart device'}

async def setup_network():
    """Setup network using WiFi manager"""
    print("[MAIN] Setting up network...")
    result = await wifi_manager.setup_network()
    return result.get('success', False)

# server start
async def main():
    # Ensure network is ready before starting server
    network_ready = await setup_network()
    
    if not network_ready:
        print("Network setup failed, exiting...")
        return
    
    print("Starting background tasks...")
    asyncio.create_task(model.monitor_dials_loop())
    
    print("Starting Microdot server on port 80...")
    await app.start_server(port=80)

# run everything
asyncio.run(main())