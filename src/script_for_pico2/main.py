import os
import time
import sys
import struct
import micropython
from sdcard import SDCard
from machine import I2S, Pin, SPI, UART, freq

# ========= PERFORMANCE & HARDWARE CONFIG =========
freq(200000000)

# -- SD Card on SPI1 --
SPI_ID = 1
SCK_PIN = Pin(10)
MOSI_PIN = Pin(11)
MISO_PIN = Pin(12)
CS_PIN = Pin(13)

# -- I2S on I2S(0) --
I2S_ID = 0
SCK_I2S_PIN = Pin(7)
WS_I2S_PIN = Pin(8)
SD_I2S_PIN = Pin(6) 
XMT_PIN = Pin(15, Pin.OUT)

# -- UART on UART(0) --
# Default pins are GP0 (TX) and GP1 (RX)
UART_ID = 0
BAUD_RATE = 115200

# ========= AUDIO CONFIG =========
WAV_FILE_1 = "audio1.wav"
WAV_FILE_2 = "audio2.wav"
WAV_SAMPLE_SIZE_IN_BITS = 16
SAMPLE_RATE_IN_HZ = 16000
FORMAT = I2S.STEREO
MONO_BUFFER_SIZE = 8192
I2S_BUFFER_SIZE = 32768

# ========= MIXER CONFIG & GLOBALS =========
audio_running = True
P_gain_ch1 = 0.5
P_gain_ch2 = 0.5
P_pan = 0.0
P_master_gain = 0.7

def SetMixerParam(gain_ch1=None, gain_ch2=None, pan=None, master_gain=None):
    """Function to update mixer parameters."""
    global P_gain_ch1, P_gain_ch2, P_pan, P_master_gain
    if gain_ch1 is not None: P_gain_ch1 = max(0.0, float(gain_ch1))
    if gain_ch2 is not None: P_gain_ch2 = max(0.0, float(gain_ch2))
    if pan is not None: P_pan = max(-1.0, min(1.0, float(pan)))
    if master_gain is not None: P_master_gain = max(0.0, float(master_gain))
    # Print to the local REPL to confirm the change was received
    print(f"UART CMD RX -> Mixer: g1={P_gain_ch1:.2f}, g2={P_gain_ch2:.2f}, pan={P_pan:.2f}, master={P_master_gain:.2f}")

# ========= FIXED-POINT INTEGER DSP (MIXER) =========
FIXED_POINT_SHIFT = 12
FIXED_POINT_ONE = 1 << FIXED_POINT_SHIFT
INT16_MAX = 32767
INT16_MIN = -32768

@micropython.native
def mix_audio_fixed(dest_buf: memoryview, src1: memoryview, src2: memoryview, n_samples: int, g1: float, g2: float, pan: float, master: float):
    """Mixes two mono sources into a stereo output using fixed-point integer math."""
    master_gain_fp = int(master * FIXED_POINT_ONE)
    pan_l_fp = FIXED_POINT_ONE
    pan_r_fp = FIXED_POINT_ONE

    if pan > 0:
        pan_l_fp = int((1.0 - pan) * FIXED_POINT_ONE)
    elif pan < 0:
        pan_r_fp = int((1.0 + pan) * FIXED_POINT_ONE)

    final_gain1_fp = (int(g1 * master_gain_fp) * pan_l_fp) >> FIXED_POINT_SHIFT
    final_gain2_fp = (int(g2 * master_gain_fp) * pan_r_fp) >> FIXED_POINT_SHIFT

    for i in range(n_samples):
        s1 = struct.unpack_from('<h', src1, i * 2)[0]
        s2 = struct.unpack_from('<h', src2, i * 2)[0]
        l_sample = (s1 * final_gain1_fp) >> FIXED_POINT_SHIFT
        r_sample = (s2 * final_gain2_fp) >> FIXED_POINT_SHIFT

        if l_sample > INT16_MAX: l_sample = INT16_MAX
        elif l_sample < INT16_MIN: l_sample = INT16_MIN
        if r_sample > INT16_MAX: r_sample = INT16_MAX
        elif r_sample < INT16_MIN: r_sample = INT16_MIN

        struct.pack_into('<hh', dest_buf, i * 4, l_sample, r_sample)

# ======================================================
#               MAIN EXECUTION
# ======================================================
def main():
    """Initializes and runs the audio player and UART command listener."""
    global audio_running
    
    wav1_buffer = bytearray(MONO_BUFFER_SIZE)
    wav2_buffer = bytearray(MONO_BUFFER_SIZE)
    stereo_buffer = bytearray(MONO_BUFFER_SIZE * 2)
    
    wav1_mv = memoryview(wav1_buffer)
    wav2_mv = memoryview(wav2_buffer)
    stereo_mv = memoryview(stereo_buffer)

    audio_out = None
    wav1 = None
    wav2 = None
    uart = None
    
    def fill_and_write_buffer(arg):
        """This is the workhorse function scheduled by the IRQ."""
        global audio_running, P_gain_ch1, P_gain_ch2, P_pan, P_master_gain
        if not audio_running: return
        try:
            n1 = wav1.readinto(wav1_mv)
            if n1 < MONO_BUFFER_SIZE:
                wav1.seek(44)
                n1 += wav1.readinto(wav1_mv[n1:])
            n2 = wav2.readinto(wav2_mv)
            if n2 < MONO_BUFFER_SIZE:
                wav2.seek(44)
                n2 += wav2.readinto(wav2_mv[n2:])
            bytes_to_process = min(n1, n2)
            if bytes_to_process == 0: return
            samples_to_process = bytes_to_process // 2
            mix_audio_fixed(stereo_mv, wav1_mv, wav2_mv, samples_to_process, P_gain_ch1, P_gain_ch2, P_pan, P_master_gain)
            audio_out.write(stereo_mv[:bytes_to_process * 2])
        except Exception as e:
            print(f"Error in IRQ handler: {e}")
            audio_running = False

    def i2s_callback(arg):
        micropython.schedule(fill_and_write_buffer, 0)

    try:
        XMT_PIN.on()
        print("Initializing SD card...")
        spi = SPI(SPI_ID, baudrate=1_000_000, sck=SCK_PIN, mosi=MOSI_PIN, miso=MISO_PIN)
        sd = SDCard(spi, CS_PIN)
        sd.init_spi(23_999_999)
        os.mount(sd, "/sd")
        print("SD card mounted.")

        print("Initializing UART listener...")
        uart = UART(UART_ID, BAUD_RATE)

        print("Initializing I2S audio output with IRQ...")
        audio_out = I2S(I2S_ID, sck=SCK_I2S_PIN, ws=WS_I2S_PIN, sd=SD_I2S_PIN, mode=I2S.TX, bits=WAV_SAMPLE_SIZE_IN_BITS, format=FORMAT, rate=SAMPLE_RATE_IN_HZ, ibuf=I2S_BUFFER_SIZE)
        audio_out.irq(i2s_callback)

        wav1 = open(f"/sd/{WAV_FILE_1}", "rb")
        wav2 = open(f"/sd/{WAV_FILE_2}", "rb")
        wav1.seek(44)
        wav2.seek(44)

        print("Priming I2S buffer...")
        fill_and_write_buffer(0)
        fill_and_write_buffer(0)
        
        print("-" * 40)
        print("Receiver Pico running. Listening for UART commands.")
        print("This REPL is for monitoring only.")
        print("-" * 40)
        
        while audio_running:
            # Non-blocking check for incoming UART data
            if uart.any():
                try:
                    # Read the incoming command, which should end with a newline
                    command_bytes = uart.readline()
                    if command_bytes:
                        command_str = command_bytes.decode('utf-8').strip()
                        parts = command_str.split()
                        
                        if len(parts) == 2:
                            param, value = parts
                            if param.lower() == 'g1': SetMixerParam(gain_ch1=value)
                            elif param.lower() == 'g2': SetMixerParam(gain_ch2=value)
                            elif param.lower() == 'pan': SetMixerParam(pan=value)
                            elif param.lower() == 'master': SetMixerParam(master_gain=value)
                            else: print(f"Unknown UART command: {param}")
                        else:
                            print(f"Invalid UART command format: {command_str}")
                except Exception as e:
                    print(f"Error processing UART command: {e}")
            
            # The CPU is mostly idle here, waiting for interrupts.
            time.sleep_ms(5)

    except Exception as e:
        print(f"FATAL ERROR in main: {e}")
    finally:
        print("Cleaning up resources...")
        audio_running = False
        if audio_out:
            audio_out.irq(None)
            audio_out.deinit()
        if uart:
            uart.deinit()
        if wav1: wav1.close()
        if wav2: wav2.close()
        try:
            os.umount("/sd")
        except OSError:
            pass
        XMT_PIN.off()
        print("Program finished.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCtrl+C detected. Stopping...")
    finally:
        audio_running = False

