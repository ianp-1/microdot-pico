from lib.microdot import Microdot, Response, send_file
import lib.mm_wlan as mm_wlan
import uasyncio as asyncio
from model import AudioModel
from time import sleep

model = AudioModel()

ssid = 'SUGA Guest 5G'
password = 'suga22wifi'

app = Microdot()
Response.default_content_type = 'text/html'  
mm_wlan.connect_to_network(ssid, password)

@app.route('/')
def index(request):
    return send_file('templates/dashboard.html')

@app.post('/toggle-voice-mode')
def toggle_mode(request):
    mode = model.toggle_voice_mode()
    return f'<span id="currentMode">Current Mode: {mode}</span>'


@app.route('/static/<path:path>')
def static_files(request, path):
    return send_file(f'static/{path}')


# server start
async def main():
    asyncio.create_task(model.monitor_dials_loop())
    await app.start_server(port=80)

# run everything
asyncio.run(main())