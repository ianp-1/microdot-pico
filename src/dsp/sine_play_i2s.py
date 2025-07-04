import machine, time
from machine import I2S, Pin
from dsp.dsp_state import get_param

# ======= I2S CONFIGURATION =======
SCK_PIN = 20        # BCLK
WS_PIN = 21         # LRCK (must be SCK_PIN + 1)
SD_PIN = 18         # DOUT
I2S_ID = 0
BUFFER_LENGTH_IN_BYTES = 1000

# ======= AUDIO CONFIGURATION =======
BITS_PER_SAMPLE = 16
CHANNEL_FORMAT = I2S.STEREO
SAMPLE_RATE_HZ = 48000
BYTES_PER_FRAME = 4  # 2 bytes per channel (16-bit stereo)

# ======= SINE WAVE SEQUENCE =======
SINE_WAVE = [
    0x52dd,0x4d44,0x4757,0x411b,0x3a98,0x33d5,0x2cd8,0x25ab,
    0x1e55,0x16dd,0x0f4c,0x07aa,0x0000,0xf856,0xf0b4,0xe923,
    0xe1ab,0xda55,0xd327,0xcc2b,0xc568,0xbee5,0xb8a9,0xb2bc,
    0xad23,0xa7e5,0xa307,0x9e90,0x9a83,0x96e6,0x93bc,0x9108,
    0x8ece,0x8d10,0x8bd1,0x8b10,0x8ad0,0x8b10,0x8bd1,0x8d10,
    0x8ece,0x9108,0x93bc,0x96e6,0x9a83,0x9e90,0xa307,0xa7e5,
    0xad23,0xb2bc,0xb8a9,0xbee5,0xc568,0xcc2b,0xd328,0xda55,
    0xe1ab,0xe923,0xf0b4,0xf856,0x0000,0x07aa,0x0f4c,0x16dd,
    0x1e55,0x25ab,0x2cd9,0x33d5,0x3a98,0x411b,0x4757,0x4d44,
    0x52dd,0x581b,0x5cf9,0x6170,0x657d,0x691a,0x6c44,0x6ef8,
    0x7132,0x72f0,0x742f,0x74f0,0x7530,0x74f0,0x742f,0x72f0,
    0x7132,0x6ef8,0x6c44,0x691a,0x657d,0x6170,0x5cf9,0x581b
]

def fill_stereo_buffer(buf, samples, silence_right=True):
    for i, sample in enumerate(samples):
        left = sample
        right = 0 if silence_right else sample

        buf[i * 4 + 0] = (left >> 8) & 0xFF
        buf[i * 4 + 1] = left & 0xFF
        buf[i * 4 + 2] = (right >> 8) & 0xFF
        buf[i * 4 + 3] = right & 0xFF

def audio_task():
    audio_out = I2S(
        I2S_ID,
        sck=Pin(SCK_PIN),
        ws=Pin(WS_PIN),
        sd=Pin(SD_PIN),
        mode=I2S.TX,
        bits=BITS_PER_SAMPLE,
        format=CHANNEL_FORMAT,
        rate=SAMPLE_RATE_HZ,
        ibuf=BUFFER_LENGTH_IN_BYTES
    )

    num_frames = len(SINE_WAVE)
    buf_size = num_frames * BYTES_PER_FRAME
    buf_0 = bytearray(buf_size)
    buf_1 = bytearray(buf_size)
    silence_buf = bytearray(buf_size)  # Pre-allocated silence buffer

    fill_stereo_buffer(buf_0, SINE_WAVE)
    fill_stereo_buffer(buf_1, SINE_WAVE)
    # Ensure silence buffer is truly zeroed
    for i in range(buf_size):
        silence_buf[i] = 0

    mv_0 = memoryview(buf_0)
    mv_1 = memoryview(buf_1)
    mv_silence = memoryview(silence_buf)

    led = Pin(14, Pin.OUT)
    led.value(1)

    print("========== START PLAYBACK ==========")

    try:
        last_mute = None
        last_volume = None
        audio_active = True
        
        while True:
            # Read parameters
            volume = get_param("volume")
            mute = get_param("mute")
            # Defensive: treat None as unmuted, full volume
            if mute is None:
                mute = False
            if volume is None:
                volume = 100

            # Debug: print only on change
            if mute != last_mute or volume != last_volume:
                print(f"[DSP] mute={mute} volume={volume}")
                last_mute = mute
                last_volume = volume

            # Handle mute by stopping/starting I2S
            should_be_active = not (mute or volume == 0)
            
            if should_be_active and not audio_active:
                # Start audio
                print("[DSP] STARTING I2S audio")
                audio_active = True
            elif not should_be_active and audio_active:
                # Stop audio
                print("[DSP] STOPPING I2S audio") 
                audio_active = False
                
            # Only write audio data if active
            if audio_active:
                buffer_to_write = mv_0 if (time.ticks_ms() // 1000) % 2 == 0 else mv_1
                audio_out.write(buffer_to_write)
            else:
                # Write silence when muted
                audio_out.write(mv_silence)

            machine.idle()
            time.sleep_ms(2)

    except (KeyboardInterrupt, Exception) as e:
        print("Caught exception:", type(e).__name__, e)

    finally:
        audio_out.deinit()
        print("========== DONE ==========")
