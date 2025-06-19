"""
WiFi Configuration Test Server
A local test server that simulates the WiFi functionality for development and testing
"""

from lib.microdot import Microdot, Response, send_file
import json
import time
import random

app = Microdot()

# Mock WiFi state
class MockWiFiState:
    def __init__(self):
        self.mode = 'ap'  # 'ap' or 'station'
        self.ap_config = {'ssid': 'PicoW-Audio-Test', 'password': 'testpass123'}
        self.station_config = {'ssid': '', 'password': ''}
        self.connected = True
        self.ip = '192.168.4.1'
        self.mock_networks = [
            {'ssid': 'TestNetwork_5G', 'rssi': -45, 'authmode': 3, 'channel': 6, 'bssid': '00:11:22:33:44:55', 'hidden': False},
            {'ssid': 'MyWiFi', 'rssi': -55, 'authmode': 3, 'channel': 11, 'bssid': '66:77:88:99:AA:BB', 'hidden': False},
            {'ssid': 'OpenNetwork', 'rssi': -65, 'authmode': 0, 'channel': 1, 'bssid': 'CC:DD:EE:FF:00:11', 'hidden': False},
            {'ssid': 'WeakSignal', 'rssi': -80, 'authmode': 3, 'channel': 3, 'bssid': '22:33:44:55:66:77', 'hidden': False},
            {'ssid': 'Office_Guest', 'rssi': -50, 'authmode': 2, 'channel': 9, 'bssid': '88:99:AA:BB:CC:DD', 'hidden': False},
        ]

wifi_state = MockWiFiState()

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

# Mock audio endpoints (simplified)
@app.post('/toggle-voice-mode')
def toggle_mode(request):
    modes = ['normal', 'voice', 'music']
    mode = modes[random.randint(0, len(modes)-1)]
    return f'<span id="currentMode">Current Mode: {mode}</span>'

@app.post('/trigger-ducking')
def toggle_ducking(request):
    enabled = random.randint(0, 1) == 1
    return f'<span id="musicDucking">Ducking: {"on" if enabled else "off"}</span>'

@app.post('/trigger-feedback')
def toggle_feedback(request):
    enabled = random.randint(0, 1) == 1
    return f'<span id="feedback">Feedback: {"on" if enabled else "off"}</span>'

@app.route('/current-state-json')
def current_state_json(request):
    """Return mock current system state as JSON"""
    modes = ['normal', 'voice', 'music']
    return {
        'mode': modes[random.randint(0, len(modes)-1)],
        'ducking': random.randint(0, 1) == 1,
        'feedback': random.randint(0, 1) == 1,
        'eq': {
            'low': round(random.uniform(-6, 6), 1),
            'mid': round(random.uniform(-6, 6), 1), 
            'high': round(random.uniform(-6, 6), 1)
        }
    }

@app.route('/current-eq-json')
def current_eq_json(request):
    """Return mock current EQ values as JSON"""
    return {
        'low': round(random.uniform(-6, 6), 1),
        'mid': round(random.uniform(-6, 6), 1), 
        'high': round(random.uniform(-6, 6), 1)
    }

# WiFi Configuration Endpoints (Mock Implementation)
@app.route('/wifi/status')
def wifi_status(request):
    """Return current WiFi status"""
    print(f"[TEST] WiFi status requested - Mode: {wifi_state.mode}")
    
    if wifi_state.mode == 'ap':
        return {
            'mode': 'Access Point',
            'ssid': wifi_state.ap_config['ssid'],
            'ip': wifi_state.ip,
            'connected': True
        }
    elif wifi_state.mode == 'station' and wifi_state.station_config['ssid']:
        return {
            'mode': 'Station',
            'ssid': wifi_state.station_config['ssid'],
            'ip': wifi_state.ip,
            'connected': wifi_state.connected
        }
    else:
        return {
            'mode': 'Disconnected',
            'ssid': None,
            'ip': None,
            'connected': False
        }

@app.post('/wifi/connect-station')
def wifi_connect_station(request):
    """Mock station connection - always requires restart"""
    try:
        data = json.loads(request.body.decode('utf-8'))
        ssid = data.get('ssid', '').strip()
        password = data.get('password', '')
        
        print(f"[TEST] Station connection requested: {ssid}")
        
        if not ssid:
            return {'success': False, 'message': 'SSID is required'}
        
        if not password:
            return {'success': False, 'message': 'Password is required'}
        
        # Simulate some connection failures for testing
        if ssid.lower() == 'failtest':
            return {'success': False, 'message': 'Network not found'}
        
        if password == 'wrong':
            return {'success': False, 'message': 'Wrong password'}
        
        # Save configuration (mock)
        wifi_state.station_config = {'ssid': ssid, 'password': password}
        wifi_state.mode = 'station'
        
        print(f"[TEST] Station config saved: {ssid}")
        
        # Always require restart in test mode
        return {
            'success': True,
            'restart_required': True,
            'message': 'Configuration saved. Device restart required to switch to station mode.',
            'ssid': ssid,
            'mode': 'station'
        }
        
    except (ValueError, KeyError) as e:
        print(f"[TEST] JSON parse error: {e}")
        return {'success': False, 'message': 'Invalid request data'}
    except Exception as e:
        print(f"[TEST] Station connect error: {e}")
        return {'success': False, 'message': 'Connection failed'}

@app.post('/wifi/start-ap')
def wifi_start_ap(request):
    """Mock access point start"""
    try:
        data = json.loads(request.body.decode('utf-8'))
        ssid = data.get('ssid', 'PicoW-Audio-Test').strip()
        password = data.get('password', 'testpass123')
        
        print(f"[TEST] AP start requested: {ssid}")
        
        if len(password) < 8:
            return {'success': False, 'message': 'Password must be at least 8 characters'}
        
        # Save AP configuration (mock)
        wifi_state.ap_config = {'ssid': ssid, 'password': password}
        wifi_state.mode = 'ap'
        wifi_state.ip = '192.168.4.1'
        wifi_state.connected = True
        
        print(f"[TEST] AP started: {ssid}")
        
        return {
            'success': True,
            'ip': '192.168.4.1',
            'ssid': ssid,
            'password': password,
            'mode': 'ap'
        }
        
    except (ValueError, KeyError) as e:
        print(f"[TEST] JSON parse error: {e}")
        return {'success': False, 'message': 'Invalid request data'}
    except Exception as e:
        print(f"[TEST] AP start error: {e}")
        return {'success': False, 'message': 'Failed to start Access Point'}

@app.route('/wifi/scan')
def wifi_scan(request):
    """Mock network scan"""
    print("[TEST] Network scan requested")
    
    # Simulate scan delay
    time.sleep(0.5)
    
    # Add some randomness to signal strength
    networks = []
    for network in wifi_state.mock_networks:
        net_copy = network.copy()
        # Randomize signal strength slightly
        net_copy['rssi'] = network['rssi'] + random.randint(-5, 5)
        networks.append(net_copy)
    
    # Sort by signal strength
    networks.sort(key=lambda x: x['rssi'], reverse=True)
    
    print(f"[TEST] Found {len(networks)} networks")
    
    return {
        'success': True,
        'networks': networks
    }

@app.post('/wifi/restart')
def wifi_restart(request):
    """Mock device restart"""
    print("[TEST] Device restart requested")
    
    # Simulate restart behavior
    if wifi_state.mode == 'station' and wifi_state.station_config['ssid']:
        # Simulate station connection after restart
        wifi_state.connected = True
        wifi_state.ip = f"192.168.1.{random.randint(100, 200)}"
        print(f"[TEST] Simulated station connection to {wifi_state.station_config['ssid']}")
        print(f"[TEST] Assigned IP: {wifi_state.ip}")
    
    return {'success': True, 'message': 'Device restarting... (simulated)'}

# Mock WebSocket endpoint (simplified)
@app.route('/ws')
def websocket_mock(request):
    """Mock WebSocket endpoint"""
    return Response("WebSocket mock - not implemented in test server", status_code=501)

def main():
    print("=" * 60)
    print("WiFi Configuration Test Server")
    print("=" * 60)
    print("This is a mock server for testing WiFi configuration features")
    print("")
    print("Available test scenarios:")
    print("- Normal operation: Use any SSID/password")
    print("- Network not found: Use SSID 'failtest'")
    print("- Wrong password: Use password 'wrong'")
    print("- Mock networks available in scan")
    print("")
    print("Server starting on http://localhost:8000")
    print("=" * 60)
    
    try:
        app.run(port=8000, debug=True)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")

if __name__ == '__main__':
    main()
