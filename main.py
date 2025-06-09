from lib.microdot import Microdot, Response, send_file, websocket
from lib.microdot.websocket import with_websocket
import lib.mm_wlan as mm_wlan
import uasyncio as asyncio
from model.model import AudioModel
from time import sleep

ssid = 'SUGA Guest 5G'
password = 'suga22wifi'

mm_wlan.connect_to_network(ssid, password) 

model = AudioModel()

app = Microdot()

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

# @app.route('/ws')
# @with_websocket
# async def websocket_handler(request, ws):
#     model.ws_clients.add(ws)
#     try:
#         while True:
#             await ws.receive()  # or handle incoming messages
#     except:
#         pass
#     finally:
#         model.ws_clients.discard(ws)
@app.route('/ws')
@with_websocket
async def websocket_handler(request, ws):
    model.ws_manager.add_client(ws)
    try:
        while True:
            message = await ws.receive()
            
            if message:
                print(f"[WS] Received: {message}")
                try:
                    import json
                    
                    # Handle URL-encoded form data from HTMX
                    if isinstance(message, str):
                        if message.startswith('{'):
                            # JSON data
                            data = json.loads(message)
                        elif '=' in message:
                            # URL-encoded form data
                            data = dict(item.split('=', 1) for item in message.split('&'))
                        else:
                            print(f"[WS] Unknown message format: {message}")
                            continue
                    else:
                        data = message
                    
                    action = data.get('action')
                    print(f"[WS] Action: {action}")
                    
                    if action == 'toggle_voice_mode':
                        new_mode = model.voice_mode_manager.toggle_mode()
                        print(f"[WS] Voice mode toggled to: {new_mode}")
                        
                    elif action == 'eq_update':
                        band = data.get('band')
                        value = float(data.get('value', 0))
                        if band and value is not None:
                            model.set_target_eq(band, value)
                            print(f"[WS] EQ update: {band} = {value}dB")
                            
                    elif action == 'get_current_eq':
                        # Send current EQ values back to client
                        eq_data = {
                            'type': 'dial',
                            'low': model.eq_processor.live_db['low'],
                            'mid': model.eq_processor.live_db['mid'],
                            'high': model.eq_processor.live_db['high']
                        }
                        await ws.send(json.dumps(eq_data))
                        print(f"[WS] Sent current EQ values")
                        
                except Exception as e:
                    print(f"[WS] Error processing message: {e}")
                    
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


# server start
async def main():
    asyncio.create_task(model.monitor_dials_loop())
    await app.start_server(port=80)

# run everything
asyncio.run(main())