import _thread
from dsp.sine_play_i2s import audio_task
from lib.microdot import Microdot, send_file
from lib.microdot.websocket import with_websocket
import uasyncio as asyncio
import machine
from model.model import AudioModel
from model.wifi_manager import WiFiManager
from app import (
    WebSocketHandler, WiFiRoutes, AudioRoutes,
    SERVER_PORT, main_logger
)

# === Start DSP on Core 1 ===
_thread.start_new_thread(audio_task, ())

# === App setup ===
app = Microdot()
model = AudioModel()
wifi_manager = WiFiManager()

# === Route handlers ===
ws_handler = WebSocketHandler(model)
wifi_routes = WiFiRoutes(wifi_manager)
audio_routes = AudioRoutes(model)

# Static routes
@app.route('/')
def index(request):
    """Serve the main dashboard with compression support"""
    return send_file('templates/dashboard.min.html', compressed=True,  file_extension='.gz')

@app.route('/static/<path:path>')
def static_files(request, path):
    """Serve static files with security checks"""
    if '..' in path:
        return 'Forbidden', 403
    return send_file(f'static/{path}', compressed=True, file_extension='.gz',max_age=31536000)

# API routes - delegate to AudioRoutes class
@app.post('/toggle-voice-mode')
def toggle_mode(request):
    """Toggle voice mode and return updated state"""
    return audio_routes.toggle_voice_mode(request)

@app.post('/trigger-ducking')
def toggle_ducking(request):
    """Toggle ducking and return updated state"""
    return audio_routes.toggle_ducking(request)

@app.post('/trigger-feedback')
def toggle_feedback(request):
    """Toggle feedback and return updated state"""
    return audio_routes.toggle_feedback(request)

@app.route('/current-state-json')
def current_state_json(request):
    """Return current system state as JSON"""
    return audio_routes.get_current_state_json(request)

@app.route('/current-eq-json')  
def current_eq_json(request):
    """Return current EQ values as JSON"""
    return audio_routes.get_current_eq_json(request)

@app.post('/update-eq')
def update_eq(request):
    """Update EQ values via HTTP POST"""
    return audio_routes.update_eq(request)

@app.route('/health')
def health_check(request):
    """Health check endpoint"""
    return audio_routes.health_check(request)

@app.route('/system-info')
def system_info(request):
    """System information endpoint"""
    return audio_routes.system_info(request)

# WebSocket route
@app.route('/ws')
@with_websocket
async def websocket_handler(request, ws):
    """Handle WebSocket connections using dedicated handler"""
    await ws_handler.handle_connection(ws)

# WiFi routes - delegate to WiFiRoutes class
@app.route('/wifi/status')
def wifi_status(request):
    return wifi_routes.get_status(request)

@app.route('/wifi/status-detailed')
def wifi_status_detailed(request):
    return wifi_routes.get_status_detailed(request)

@app.route('/wifi/config')
def wifi_config(request):
    return wifi_routes.get_config(request)

@app.route('/wifi/scan')
def wifi_scan(request):
    return wifi_routes.scan_networks(request)

@app.post('/wifi/set-mode')
async def wifi_set_mode(request):
    return await wifi_routes.set_mode(request)

@app.post('/wifi/connect-station')
async def wifi_connect_station(request):
    return await wifi_routes.connect_station(request)

@app.post('/wifi/connect-station-dual')
async def wifi_connect_station_dual(request):
    return await wifi_routes.connect_station_dual(request)

@app.post('/wifi/start-ap')
async def wifi_start_ap(request):
    return await wifi_routes.start_ap(request)

@app.post('/wifi/restart')
def wifi_restart(request):
    return wifi_routes.restart_device(request)

@app.post('/wifi/save-station-config')
def wifi_save_station_config(request):
    return wifi_routes.save_station_config(request)

@app.post('/wifi/save-ap-config')
def wifi_save_ap_config(request):
    return wifi_routes.save_ap_config(request)

# === Async setup ===
async def setup_network():
    main_logger.info("Setting up network...")
    try:
        result = await wifi_manager.setup_network()
        return result.get('success', False)
    except Exception as e:
        main_logger.exception("Network setup error", e)
        return False

async def setup_background_tasks():
    main_logger.info("Starting background tasks...")
    try:
        asyncio.create_task(model.monitor_dials_loop())
        main_logger.info("Background tasks started successfully")
    except Exception as e:
        main_logger.exception("Background tasks error", e)


async def main():
    main_logger.info(f"Starting Audio Dashboard on port {SERVER_PORT}...")
    asyncio.create_task(setup_network())
    asyncio.create_task(setup_background_tasks())
    await app.start_server(port=SERVER_PORT)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        main_logger.info("Server stopped by user")
    except Exception as e:
        main_logger.exception("Fatal error", e)
        machine.reset()