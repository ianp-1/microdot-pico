from lib.microdot import Microdot, Response, send_file, websocket
from lib.microdot.websocket import with_websocket
import uasyncio as asyncio
from model.model import AudioModel
from model.wifi_manager import WiFiManager
import json
import machine

app = Microdot()
model = AudioModel()
wifi_manager = WiFiManager()

@app.route('/')
def index(request):
    return send_file('templates/dashboard.min.html', compressed=True, file_extension='.gz')


@app.route('/static/<path:path>')
def static_files(request, path):
    if '..' in path:
        return 'Forbidden', 403
    return send_file(f'static/{path}', compressed=True, file_extension='.gz')


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

@app.route('/wifi/status-detailed')
def wifi_status_detailed(request):
    """Return detailed WiFi status"""
    return wifi_manager.get_current_status_detailed()

@app.route('/wifi/config')
def wifi_config(request):
    """Return saved WiFi configuration for autofill"""
    try:
        config = wifi_manager.config
        return {
            'success': True,
            'config': {
                'mode': config.get_mode(),
                'station': config.get_station_config(),
                'ap': config.get_ap_config()
            }
        }
    except Exception as e:
        print(f"[WiFi] Config fetch error: {e}")
        return {'success': False, 'message': 'Failed to fetch configuration'}

@app.post('/wifi/set-mode')
async def wifi_set_mode(request):
    """Set network mode (station, ap, dual)"""
    try:
        data = json.loads(request.body.decode('utf-8'))
        mode = data.get('mode', '').strip().lower()
        restart_required = data.get('restart_required', True)
        
        if mode not in ['station', 'ap', 'dual']:
            return {'success': False, 'message': 'Invalid mode. Use: station, ap, or dual'}
        
        result = await wifi_manager.set_network_mode(mode, restart_required)
        return result
        
    except (ValueError, KeyError) as e:
        print(f"[WiFi] JSON parse error: {e}")
        return {'success': False, 'message': 'Invalid request data'}
    except Exception as e:
        print(f"[WiFi] Set mode error: {e}")
        return {'success': False, 'message': 'Failed to set network mode'}

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

@app.post('/wifi/connect-station-dual')
async def wifi_connect_station_dual(request):
    """Connect to a WiFi network while keeping AP active (dual mode)"""
    try:
        # Parse JSON data from request body
        data = json.loads(request.body.decode('utf-8'))
        ssid = data.get('ssid', '').strip()
        password = data.get('password', '')
        
        if not ssid:
            return {'success': False, 'message': 'SSID is required'}
        
        result = await wifi_manager.connect_to_station_dual_mode(ssid, password)
        return result
        
    except (ValueError, KeyError) as e:
        print(f"[WiFi] JSON parse error: {e}")
        return {'success': False, 'message': 'Invalid request data'}
    except Exception as e:
        print(f"[WiFi] Dual station connect error: {e}")
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

@app.post('/wifi/save-station-config')
def wifi_save_station_config(request):
    """Save station configuration to file"""
    try:
        data = json.loads(request.body.decode('utf-8'))
        ssid = data.get('ssid', '').strip()
        password = data.get('password', '')
        
        if not ssid:
            return {'success': False, 'message': 'SSID is required'}
        
        if not password:
            return {'success': False, 'message': 'Password is required'}
        
        # Save station configuration
        success = wifi_manager.config.set_station_config(ssid, password)
        
        if success:
            return {
                'success': True, 
                'message': f'WiFi configuration saved for network: {ssid}'
            }
        else:
            return {'success': False, 'message': 'Failed to save configuration'}
        
    except (ValueError, KeyError) as e:
        print(f"[WiFi] JSON parse error: {e}")
        return {'success': False, 'message': 'Invalid request data'}
    except Exception as e:
        print(f"[WiFi] Save station config error: {e}")
        return {'success': False, 'message': 'Failed to save configuration'}

@app.post('/wifi/save-ap-config')
def wifi_save_ap_config(request):
    """Save access point configuration to file"""
    try:
        data = json.loads(request.body.decode('utf-8'))
        ssid = data.get('ssid', '').strip()
        password = data.get('password', '')
        
        if not ssid:
            return {'success': False, 'message': 'SSID is required'}
        
        if len(password) < 8:
            return {'success': False, 'message': 'Password must be at least 8 characters'}
        
        # Save AP configuration
        success = wifi_manager.config.set_ap_config(ssid, password)
        
        if success:
            return {
                'success': True, 
                'message': f'Access Point configuration saved: {ssid}'
            }
        else:
            return {'success': False, 'message': 'Failed to save configuration'}
        
    except (ValueError, KeyError) as e:
        print(f"[WiFi] JSON parse error: {e}")
        return {'success': False, 'message': 'Invalid request data'}
    except Exception as e:
        print(f"[WiFi] Save AP config error: {e}")
        return {'success': False, 'message': 'Failed to save configuration'}

async def setup_network():
    """Setup network using WiFi manager"""
    print("[MAIN] Setting up network...")
    try:
        result = await wifi_manager.setup_network()
        return result.get('success', False)
    except Exception as e:
        print(f"[MAIN] Network setup error: {e}")
        return False

async def setup_background_tasks():
    """Setup background tasks after network is ready"""
    print("Starting background tasks...")
    try:
        asyncio.create_task(model.monitor_dials_loop())
    except Exception as e:
        print(f"[MAIN] Background tasks error: {e}")

# server start
async def main():
    print("Starting Microdot server on port 80...")
    
    # Start network setup in background - don't wait for it
    network_task = asyncio.create_task(setup_network())
    
    # Start background tasks regardless of network status
    background_task = asyncio.create_task(setup_background_tasks())
    
    # Start server immediately
    try:
        await app.start_server(port=80)
    except Exception as e:
        print(f"[MAIN] Server error: {e}")

# run everything
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Server stopped by user")
except Exception as e:
    print(f"Main error: {e}")
    import machine
    machine.reset()