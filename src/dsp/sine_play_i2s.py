import machine, time
from machine import I2S
from machine import Pin
from dsp.dsp_state import get_param

# ======= I2S CONFIGURATION =======
SCK_PIN = 18		# BCLK
WS_PIN = 19     	# LRCK
SD_PIN = 20		# DOUT
I2S_ID = 0
BUFFER_LENGTH_IN_BYTES = 1000

# ======= AUDIO CONFIGURATION =======
buf_0LE_SIZE_IN_BITS = 16
FORMAT = I2S.STEREO
SAMPLE_RATE_IN_HZ = 48000
# ======= AUDIO CONFIGURATION =======

def audio_task():
    audio_out = I2S(
        I2S_ID,
        sck=Pin(SCK_PIN),
        ws=Pin(WS_PIN),
        sd=Pin(SD_PIN),
        mode=I2S.TX,
        bits=buf_0LE_SIZE_IN_BITS,
        format=FORMAT,
        rate=SAMPLE_RATE_IN_HZ,
        ibuf=BUFFER_LENGTH_IN_BYTES,
    )

    # 16-bit samples (sine wave)
    seq_1 = [0x52dd,0x4d44,0x4757,0x411b,0x3a98,0x33d5,0x2cd8,0x25ab,
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
        0x7132,0x6ef8,0x6c44,0x691a,0x657d,0x6170,0x5cf9,0x581b]

    buf_0 = bytearray(400)
    buf_1 = bytearray(400)

    for i in range(0,len(seq_1)):
        # left sample
        buf_0[i * 4] = (seq_1[i] & 0xFF00) >> 8
        buf_0[i * 4 + 1] = (seq_1[i] & 0xFF)
        buf_1[i * 4 + 2] = (seq_1[i] & 0xFF00) >> 8
        buf_1[i * 4 + 3] = (seq_1[i] & 0xFF)
        # right sample
        buf_0[i * 4 + 2] = 0
        buf_0[i * 4 + 3] = 0
        buf_1[i * 4] = 0
        buf_1[i * 4 + 1] = 0

    pin = Pin(14, Pin.OUT)
    pin.value(1)

    print("==========  START PLAYBACK ==========")
    try:
        while True:
            if (time.time() & 2):
                buf_mv = memoryview(buf_1)
            else:
                buf_mv = memoryview(buf_0)
            _ = audio_out.write(buf_mv[:(len(seq_1) * 4)])

            # Check volume and mute state
            volume = get_param('volume')
            mute = get_param('mute')
            if mute:
                machine.Pin(SCK_PIN, Pin.OUT).value(0)
            else:
                pass
            
            machine.idle()
            

    except (KeyboardInterrupt, Exception) as e:
        print("caught exception {} {}".format(type(e).__name__, e))
    finally:
        # cleanup
        audio_out.deinit()
        print("Done")