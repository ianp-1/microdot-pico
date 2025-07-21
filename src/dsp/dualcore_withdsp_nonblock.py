import os
import time
import micropython
import _thread
import sys
import select
import uasyncio as asyncio
from machine import I2S, Pin, SPI
from lib.sdcard import SDCard

# ========= HARDWARE CONFIG =========
SPI_ID = 1
SCK_PIN = Pin(10)
MOSI_PIN = Pin(11)
MISO_PIN = Pin(12)
CS_PIN = Pin(13)

I2S_ID = 0
SCK_I2S_PIN = Pin(20)
WS_I2S_PIN = Pin(21)
SD_I2S_PIN = Pin(18)
# Enable the amplifier if you have an XMT pin (e.g., on a Pico Audio Pack)
XMT_PIN = Pin(16, Pin.OUT)
XMT_PIN.on()

# ========= AUDIO CONFIG =========
WAV_FILE_1 = "audio1.wav"
WAV_FILE_2 = "audio2.wav"
WAV_SAMPLE_SIZE_IN_BITS = 16
SAMPLE_RATE_IN_HZ = 11000
FORMAT = I2S.STEREO

MONO_BUFFER_SIZE = 2048
RING_BUFFER_SIZE = 16384
I2S_BUFFER_SIZE = 8192

# ========= MIXER CONFIG & GLOBALS =========
# These parameters can be changed live via the REPL
P_gain_ch1 = 0.3
P_gain_ch2 = 0.3
P_pan = 0  # -1.0 (full left) to 1.0 (full right)
P_master_gain = 0.5 # Start master gain at 0.5 to prevent clipping when summing
mixer_lock = _thread.allocate_lock() # Lock for safely changing params

def SetMixerParam(gain_ch1=None, gain_ch2=None, pan=None, master_gain=None):
    """Thread-safe function to update mixer parameters."""
    global P_gain_ch1, P_gain_ch2, P_pan, P_master_gain
    with mixer_lock:
        if gain_ch1 is not None: P_gain_ch1 = max(0.0, float(gain_ch1))
        if gain_ch2 is not None: P_gain_ch2 = max(0.0, float(gain_ch2))
        if pan is not None: P_pan = max(-1.0, min(1.0, float(pan)))
        if master_gain is not None: P_master_gain = max(0.0, float(master_gain))
    print(f"Mixer: g1={P_gain_ch1:.2f}, g2={P_gain_ch2:.2f}, pan={P_pan:.2f}, master={P_master_gain:.2f}")

# ========= VIPER DSP (MIXER) - TRUE STEREO BALANCE LOGIC =========
@micropython.viper
def mix_audio_viper(dest, a, b, n: int, g1: int, g2: int, pan: int, master: int):
    """
    Treats 'a' and 'b' as independent left and right sources, and 'pan'
    acts as a balance control between them for true stereo separation.
    """
    FIX = 8  # 8 fractional bits for fixed-point math

    for i in range(n):
        # --- 1. Fetch signed 16-bit samples ---
        s1 = int(a[i])  # Source 'a' is the left channel input
        s2 = int(b[i])  # Source 'b' is the right channel input

        # --- 2. Apply individual gains and master gain ---
        l = (((s1 * g1) >> FIX) * master) >> FIX
        r = (((s2 * g2) >> FIX) * master) >> FIX

        # --- 3. Apply balance control (pan) ---
        # This logic ensures full separation at the extremes.
        if pan > 0:  # Pan to the right, reduce left channel volume
            # pan_gain goes from 256 (no reduction) down to 0 (full reduction)
            pan_gain = 256 - pan
            l = (l * pan_gain) >> FIX
        elif pan < 0:  # Pan to the left, reduce right channel volume
            # pan is negative, so adding it reduces the gain.
            # pan_gain goes from 256 (no reduction) down to 0 (full reduction)
            pan_gain = 256 + pan
            r = (r * pan_gain) >> FIX

        # --- 4. Final clip & store ---
        if l > 32767: l = 32767
        elif l < -32768: l = -32768
        if r > 32767: r = 32767
        elif r < -32768: r = -32768

        di = i << 1  # i*2
        dest[di] = l
        dest[di + 1] = r


# ========= GLOBALS =========
audio_running = True
ring_buffer = bytearray(RING_BUFFER_SIZE)
rb_head = 0
rb_tail = 0
rb_lock = _thread.allocate_lock()
wav1 = wav2 = None
wav1_mv = wav2_mv = None
stereo_buf = None

# ========= RING BUFFER HELPERS (UNCHANGED) =========
def ring_buffer_space():
    global rb_head, rb_tail
    if rb_head >= rb_tail: return RING_BUFFER_SIZE - (rb_head - rb_tail) - 1
    else: return (rb_tail - rb_head) - 1

def ring_buffer_available():
    global rb_head, rb_tail
    if rb_head >= rb_tail: return rb_head - rb_tail
    else: return RING_BUFFER_SIZE - (rb_tail - rb_head)

def ring_buffer_write(data: memoryview):
    global rb_head
    data_len = len(data)
    with rb_lock:
        if data_len > ring_buffer_space(): return 0
        end_space = RING_BUFFER_SIZE - rb_head
        part1_len = min(data_len, end_space)
        ring_buffer[rb_head : rb_head + part1_len] = data[0 : part1_len]
        rb_head = (rb_head + part1_len) % RING_BUFFER_SIZE
        part2_len = data_len - part1_len
        if part2_len > 0:
            ring_buffer[0 : part2_len] = data[part1_len : data_len]
            rb_head = part2_len
    return data_len

def ring_buffer_read(max_bytes):
    global rb_tail
    available = ring_buffer_available()
    if available == 0: return b''
    out_len = min(available, max_bytes)
    out = bytearray(out_len)
    with rb_lock:
        end_space = RING_BUFFER_SIZE - rb_tail
        part1_len = min(out_len, end_space)
        out[0:part1_len] = ring_buffer[rb_tail : rb_tail + part1_len]
        rb_tail = (rb_tail + part1_len) % RING_BUFFER_SIZE
        part2_len = out_len - part1_len
        if part2_len > 0:
            out[part1_len:out_len] = ring_buffer[0 : part2_len]
            rb_tail = part2_len
    return out

# ========= CORE 1: SD/DSP PRODUCER (MODIFIED) =========
def audio_core_task():
    global wav1, wav2, wav1_mv, wav2_mv, stereo_buf
    try:
        print("[Core 1] Initializing SD card...")
        spi = SPI(SPI_ID, baudrate=1_000_000, sck=SCK_PIN, mosi=MOSI_PIN, miso=MISO_PIN)
        sd = SDCard(spi, CS_PIN)
        sd.init_spi(23_000_000)
        os.mount(sd, "/sd")
        print("[Core 1] SD card mounted.")

        wav1 = open(f"/sd/{WAV_FILE_1}", "rb")
        wav2 = open(f"/sd/{WAV_FILE_2}", "rb")
        wav1.seek(44)
        wav2.seek(44)

        wav1_mv = memoryview(bytearray(MONO_BUFFER_SIZE))
        wav2_mv = memoryview(bytearray(MONO_BUFFER_SIZE))
        stereo_buf = memoryview(bytearray(MONO_BUFFER_SIZE * 2))

        print("[Core 1] Starting audio production loop...")
        while audio_running:
            if ring_buffer_space() < (MONO_BUFFER_SIZE * 2):
                time.sleep_us(10)
                continue

            n1 = wav1.readinto(wav1_mv)
            if n1 == 0:
                wav1.seek(44)
                n1 = wav1.readinto(wav1_mv)
            
            n2 = wav2.readinto(wav2_mv)
            if n2 == 0:
                wav2.seek(44)
                n2 = wav2.readinto(wav2_mv)

            to_process_bytes = min(n1, n2)
            if to_process_bytes == 0:
                continue

            # Get current mixer params safely
            with mixer_lock:
                g1 = P_gain_ch1
                g2 = P_gain_ch2
                pan = P_pan
                master = P_master_gain
            
            # Convert float params to fixed-point integers for viper
            g1_fixed = int(g1 * 256)
            g2_fixed = int(g2 * 256)
            pan_fixed = int(pan * 256)
            master_fixed = int(master * 256)

            samples = to_process_bytes // 2
            
            # Call the new viper mixer function
            mix_audio_viper(stereo_buf, wav1_mv, wav2_mv, samples, g1_fixed, g2_fixed, pan_fixed, master_fixed)

            bytes_written = ring_buffer_write(stereo_buf[:to_process_bytes * 2])
            if bytes_written == 0:
                print("[Core 1] Warning: Ring buffer write failed (full).")

    except Exception as e:
        print(f"[Core 1] FATAL ERROR: {e}")
    finally:
        print("[Core 1] Producer finished. Cleaning up...")
        if wav1: wav1.close()
        if wav2: wav2.close()
        try: os.umount("/sd")
        except OSError: pass
        print("[Core 1] Cleanup complete.")

# ========= ASYNC I2S CONSUMER FOR WEB APP INTEGRATION =========
async def async_i2s_consumer():
    """Async version of I2S consumer for integration with web app"""
    global audio_running
    audio_out = None
    
    try:
        print("[Core 0] Initializing I2S for audio output...")
        audio_out = I2S(
            I2S_ID, sck=SCK_I2S_PIN, ws=WS_I2S_PIN, sd=SD_I2S_PIN,
            mode=I2S.TX, bits=WAV_SAMPLE_SIZE_IN_BITS, format=FORMAT,
            rate=SAMPLE_RATE_IN_HZ, ibuf=I2S_BUFFER_SIZE,
        )
        print("[Core 0] I2S initialized successfully")
        
        while audio_running:
            data = ring_buffer_read(1024)
            if data:
                # This is a blocking write, but it's usually fast.
                audio_out.write(data)
                await asyncio.sleep_ms(0) # Yield to other tasks
            else:
                # Yield control to other async tasks when no audio data
                await asyncio.sleep_ms(5)

    except Exception as e:
        print(f"[Core 0] I2S Consumer Error: {e}")
    finally:
        print("[Core 0] I2S consumer finished.")
        if audio_out:
            audio_out.deinit()
        print("[Core 0] I2S deinitialized.")

# ========= CORE 0: I2S CONSUMER & CONTROL (MODIFIED) =========
def i2s_and_control_loop():
    global audio_running
    audio_out = None
    
    # Use poll for non-blocking input from the REPL
    poller = select.poll()
    poller.register(sys.stdin, select.POLLIN)
    
    try:
        print("[Core 0] Initializing I2S...")
        audio_out = I2S(
            I2S_ID, sck=SCK_I2S_PIN, ws=WS_I2S_PIN, sd=SD_I2S_PIN,
            mode=I2S.TX, bits=WAV_SAMPLE_SIZE_IN_BITS, format=FORMAT,
            rate=SAMPLE_RATE_IN_HZ, ibuf=I2S_BUFFER_SIZE,
        )

        print("-" * 40)
        print("Enter commands in REPL to control mixer:")
        print("  g1 <value>   (e.g., g1 0.5)")
        print("  g2 <value>   (e.g., g2 1.2)")
        print("  pan <value>  (e.g., pan -0.5 for left)")
        print("  master <val> (e.g., master 0.8)")
        print("-" * 40)
        
        while audio_running:
            # Check for user input without blocking
            if poller.poll(0):
                cmd = sys.stdin.readline().strip()
                parts = cmd.split()
                try:
                    if len(parts) == 2:
                        param, value = parts
                        if param.lower() == 'g1': SetMixerParam(gain_ch1=value)
                        elif param.lower() == 'g2': SetMixerParam(gain_ch2=value)
                        elif param.lower() == 'pan': SetMixerParam(pan=value)
                        elif param.lower() == 'master': SetMixerParam(master_gain=value)
                        else: print("Unknown command")
                    else:
                        print("Invalid command format. Use: <param> <value>")
                except Exception as e:
                    print(f"Error processing command: {e}")

            # The rest is the normal I2S drain loop
            data = ring_buffer_read(1024)
            if data:
                audio_out.write(data)
            else:
                time.sleep_us(10)

    finally:
        print("[Core 0] Playback finished.")
        if audio_out:
            audio_out.deinit()
        print("[Core 0] I2S stopped.")

# ========= STARTUP =========
if __name__ == "__main__":
    print("[Core 0] Starting Core 1 (Audio Producer)...")
    _thread.start_new_thread(audio_core_task, ())

    try:
        # Start the I2S consumer and control loop on the main core
        i2s_and_control_loop()
    except KeyboardInterrupt:
        print("\n[Core 0] Keyboard interrupt received. Stopping...")
    except Exception as e:
        print(f"[Core 0] FATAL ERROR: {e}")
    finally:
        audio_running = False
        time.sleep(1)
        print("[Core 0] Main program finished.")
