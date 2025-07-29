import os
import time
import sys
import micropython
import gc
import audiodsp  # Import the new C module
from sdcard import SDCard
from machine import I2S, Pin, SPI, UART, freq

# ========= PERFORMANCE & HARDWARE CONFIG =========
# Set a high clock frequency for better performance
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
XMT_PIN = Pin(15, Pin.OUT) # To enable the I2S amplifier

# -- UART on UART(0) --
# Default pins are GP0 (TX) and GP1 (RX)
UART_ID = 0
BAUD_RATE = 115200

# ========= AUDIO CONFIG =========
WAV_FILE_1 = "left.wav"  # Will be treated as Left channel input
WAV_FILE_2 = "right.wav"  # Will be treated as Right channel input
WAV_SAMPLE_SIZE_IN_BITS = 16
SAMPLE_RATE_IN_HZ = 44000
FORMAT = I2S.STEREO # The C module outputs stereo
MONO_BUFFER_SIZE  = 32768
I2S_BUFFER_SIZE   = 32768

# -- EQ/Filter settings --
# Crossover frequency for the 2-band EQ, normalized by sample rate.
# E.g., 880 Hz crossover: 880 / 44000 = 0.02
CROSSOVER_FC_NORM = 500 / SAMPLE_RATE_IN_HZ
# Q factor for the crossover filters. 0.707 is a good general-purpose value.
CROSSOVER_Q = 0.707

# ========= MIXER/DSP CONFIG & GLOBALS =========
audio_running = True
# Channel gains
P_gain_ch1 = 0.7
P_gain_ch2 = 0.7
# Pan/Balance (-1.0 for full left, 0.0 for center, 1.0 for full right)
P_pan = 0.0
# Master volume
P_master_gain = 0.3
# EQ gains (1.0 is flat)
P_bass_l = 6.0
P_treble_l = 2.0
P_bass_r = 6.0
P_treble_r = 2.0

def SetDspParam(g1=None, g2=None, pan=None, master=None, bl=None, tl=None, br=None, tr=None):
    """
    Function to update DSP parameters from UART commands.
    New commands:
    'bl <value>' -> bass left
    'tl <value>' -> treble left
    'br <value>' -> bass right
    'tr <value>' -> treble right
    """
    global P_gain_ch1, P_gain_ch2, P_pan, P_master_gain, P_bass_l, P_treble_l, P_bass_r, P_treble_r
    if g1 is not None: P_gain_ch1 = max(0.0, float(g1))
    if g2 is not None: P_gain_ch2 = max(0.0, float(g2))
    if pan is not None: P_pan = max(-1.0, min(1.0, float(pan)))
    if master is not None: P_master_gain = max(0.0, float(master))
    if bl is not None: P_bass_l = max(0.0, float(bl))
    if tl is not None: P_treble_l = max(0.0, float(tl))
    if br is not None: P_bass_r = max(0.0, float(br))
    if tr is not None: P_treble_r = max(0.0, float(tr))

    # Print to the local REPL to confirm the change was received
    print(f"UART CMD RX -> g1={P_gain_ch1:.2f}, g2={P_gain_ch2:.2f}, pan={P_pan:.2f}, master={P_master_gain:.2f}")
    print(f"             -> EQ L: bass={P_bass_l:.2f} treble={P_treble_l:.2f} | R: bass={P_bass_r:.2f} treble={P_treble_r:.2f}")

# ======================================================
#                MAIN EXECUTION
# ======================================================
def main():
    """Initializes and runs the audio player and UART command listener."""
    global audio_running

    # Create buffers for audio data
    # Two mono buffers for reading from WAV files
    wav1_buffer = bytearray(MONO_BUFFER_SIZE)
    wav2_buffer = bytearray(MONO_BUFFER_SIZE)
    # One stereo buffer for the output of the C module
    stereo_buffer = bytearray(MONO_BUFFER_SIZE * 2) # 2x because it's stereo

    # Create memoryviews for efficient buffer access
    wav1_mv = memoryview(wav1_buffer)
    wav2_mv = memoryview(wav2_buffer)
    stereo_mv = memoryview(stereo_buffer)

    # Placeholders for resources that need cleanup
    audio_out = None
    wav1 = None
    wav2 = None
    uart = None

    # --- Initialize Biquad Filters from the C module ---
    # These filters are created once and their state is managed internally by the C code.
    # We need a low-pass and high-pass filter for each channel's EQ.
    print("Initializing Biquad filters...")
    lpf_l = audiodsp.Biquad(type=audiodsp.LPF, Fc=CROSSOVER_FC_NORM, Q=CROSSOVER_Q)
    hpf_l = audiodsp.Biquad(type=audiodsp.HPF, Fc=CROSSOVER_FC_NORM, Q=CROSSOVER_Q)
    lpf_r = audiodsp.Biquad(type=audiodsp.LPF, Fc=CROSSOVER_FC_NORM, Q=CROSSOVER_Q)
    hpf_r = audiodsp.Biquad(type=audiodsp.HPF, Fc=CROSSOVER_FC_NORM, Q=CROSSOVER_Q)
    print("Filters created.")

    def fill_and_write_buffer(arg):
        """This is the workhorse function scheduled by the I2S IRQ."""
        global audio_running
        if not audio_running: return

        # Diagnostic logging: garbage collect and measure memory
        gc.collect()
        start_time = time.ticks_us()

        try:
            # Read a chunk of audio data from each WAV file
            bytes_read1 = wav1.readinto(wav1_mv)
            # If end of file, loop back to the beginning (skipping header)
            if bytes_read1 < MONO_BUFFER_SIZE:
                wav1.seek(44)
                bytes_read1 += wav1.readinto(wav1_mv[bytes_read1:])

            bytes_read2 = wav2.readinto(wav2_mv)
            if bytes_read2 < MONO_BUFFER_SIZE:
                wav2.seek(44)
                bytes_read2 += wav2.readinto(wav2_mv[bytes_read2:])

            # Ensure we process the same amount of data for both channels
            bytes_to_process = min(bytes_read1, bytes_read2)
            if bytes_to_process == 0: return

            # --- Call the C DSP function ---
            # This is the core of the audio processing. All mixing (gains, pan) and EQ
            # is now handled efficiently in the C module.
            audiodsp.process(
                stereo_mv,      # Destination buffer (stereo)
                wav1_mv,        # Source 1 (left channel input)
                wav2_mv,        # Source 2 (right channel input)
                lpf_l, hpf_l,   # Left channel filters
                lpf_r, hpf_r,   # Right channel filters
                P_gain_ch1,     # Channel 1 gain
                P_gain_ch2,     # Channel 2 gain
                P_pan,          # Pan (-1.0 to 1.0)
                P_bass_l,       # Left bass gain
                P_treble_l,     # Left treble gain
                P_bass_r,       # Right bass gain
                P_treble_r,     # Right treble gain
                P_master_gain   # Master gain
            )

            # Write the processed stereo data to the I2S output.
            # The C function processes 'bytes_to_process' worth of mono samples,
            # producing twice that many bytes for the stereo output.
            audio_out.write(stereo_mv[:bytes_to_process * 2])

            # Diagnostic logging: measure execution time
            end_time = time.ticks_us()
            execution_time = time.ticks_diff(end_time, start_time)
            #print(f"Buffer fill+write time: {execution_time} us")

        except Exception as e:
            print(f"Error in IRQ handler: {e}")
            audio_running = False

    def i2s_callback(arg):
        """The actual I2S IRQ handler, which schedules the buffer filling."""
        micropython.schedule(fill_and_write_buffer, 0)

    try:
        # Turn on the I2S amplifier
        XMT_PIN.on()

        print("Initializing SD card...")
        spi = SPI(SPI_ID, baudrate=1_000_000, sck=SCK_PIN, mosi=MOSI_PIN, miso=MISO_PIN)
        sd = SDCard(spi, CS_PIN)
        sd.init_spi(23_999_999) # Run SPI at a high clock rate
        os.mount(sd, "/sd")
        print("SD card mounted.")

        print("Initializing UART listener...")
        uart = UART(UART_ID, BAUD_RATE)

        print("Initializing I2S audio output with IRQ...")
        audio_out = I2S(
            I2S_ID,
            sck=SCK_I2S_PIN, ws=WS_I2S_PIN, sd=SD_I2S_PIN,
            mode=I2S.TX,
            bits=WAV_SAMPLE_SIZE_IN_BITS,
            format=FORMAT,
            rate=SAMPLE_RATE_IN_HZ,
            ibuf=I2S_BUFFER_SIZE
        )
        audio_out.irq(i2s_callback)

        # Open the WAV files for reading in binary mode
        wav1 = open(f"/sd/{WAV_FILE_1}", "rb")
        wav2 = open(f"/sd/{WAV_FILE_2}", "rb")
        # Skip the 44-byte WAV header
        wav1.seek(44)
        wav2.seek(44)

        print("Priming I2S buffer...")
        fill_and_write_buffer(0)
        fill_and_write_buffer(0)

        print("-" * 40)
        print("Pico running. Listening for UART commands.")
        print("Commands: g1, g2, pan, master, bl, tl, br, tr")
        print("Example: 'bl 1.5' sets left bass to 1.5")
        print("-" * 40)

        while audio_running:
            # Non-blocking check for incoming UART data
            if uart.any():
                try:
                    command_bytes = uart.readline()
                    if command_bytes:
                        command_str = command_bytes.decode('utf-8').strip()
                        parts = command_str.split()

                        if len(parts) == 2:
                            param, value = parts
                            param = param.lower()
                            if param == 'g1': SetDspParam(g1=value)
                            elif param == 'g2': SetDspParam(g2=value)
                            elif param == 'pan': SetDspParam(pan=value)
                            elif param == 'master': SetDspParam(master=value)
                            elif param == 'bl': SetDspParam(bl=value)
                            elif param == 'tl': SetDspParam(tl=value)
                            elif param == 'br': SetDspParam(br=value)
                            elif param == 'tr': SetDspParam(tr=value)
                            else: print(f"Unknown UART command: {param}")
                        else:
                            print(f"Invalid UART command format: {command_str}")
                except Exception as e:
                    print(f"Error processing UART command: {e}")

            # The CPU is mostly idle here, waiting for interrupts.
            time.sleep_ms(10)

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
            pass # Ignore error if already unmounted
        XMT_PIN.off()
        print("Program finished.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCtrl+C detected. Stopping...")
    finally:
        # This ensures audio_running is set to False to stop IRQs
        # even if cleanup in main() fails.
        audio_running = False
