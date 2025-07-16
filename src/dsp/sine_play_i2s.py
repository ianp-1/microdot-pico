import machine, time, os
from machine import I2S, Pin, SPI
from lib.sdcard import SDCard
from .dsp_audio import dsp_mix_audio
from . import dsp_state

# ======= SD Card CONFIGURATION =======
SD_SPI = 1
SD_SCK = 10
SD_MOSI = 11
SD_MISO = 12
SD_CS = 13

# ======= I2S CONFIGURATION =======
SCK_PIN = 20        # BCLK
WS_PIN = 21         # LRCK (must be SCK_PIN + 1)
SD_PIN = 18         # DOUT
I2S_ID = 0
XMT_PIN = Pin(16, Pin.OUT)
XMT_PIN.on()
BUFFER_LENGTH_IN_BYTES = 40000

# ======= AUDIO CONFIGURATION =======
BITS_PER_SAMPLE = 16
CHANNEL_FORMAT = I2S.STEREO
SAMPLE_RATE_HZ = 11000
BYTES_PER_FRAME = 4  # 2 bytes per channel (16-bit stereo)

def init_sd_card():
    """Initialize the SD card."""
    try:
        cs = Pin(13, machine.Pin.OUT)
        spi = SPI(
            1,
            baudrate=1_000_000,  # this has no effect on spi bus speed to SD Card
            polarity=0,
            phase=0,
            bits=8,
            firstbit=machine.SPI.MSB,
            sck=Pin(10),
            mosi=Pin(11),
            miso=Pin(12),
        )
        sd = SDCard(spi, cs)
        sd.init_spi(10_000_000)  # increase SPI bus speed to SD card
        os.mount(sd, "/sd")
        print("SD card mounted successfully")
        return True
    except OSError as e:
        print(f"Error mounting SD card: {e}")
        return False

def audio_task():
    if not init_sd_card():
        return

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
    
    chunk0 = bytearray(1024)

    # stereo WAV files
    wav_file_path = '/sd/sound3.wav'
    wav_file_path2 = '/sd/sound4.wav'

    try:
        with open(wav_file_path, 'rb') as f1, open(wav_file_path2, 'rb') as f2:
            f1.seek(44)
            f2.seek(44)
            
            print("========== START PLAYBACK FROM SD CARD ==========")
            
            while True:
                # Update DSP parameters from Core 0 via shared state
                dsp_state.core1_update_params()
                
                chunk1 = bytearray(f1.read(1024))  
                chunk2 = bytearray(f2.read(1024)) 
                if not chunk1:
                    f1.seek(44)
                    continue
                if not chunk2:
                    f2.seek(44)
                    continue
                
                # Use DSP audio mixing functions with real-time parameters
                dsp_mix_audio(chunk1, chunk2)
                audio_out.write(chunk1)

    except (KeyboardInterrupt, Exception) as e:
        print("Caught exception:", type(e).__name__, e)

    finally:
        audio_out.deinit()
        os.umount("/sd")