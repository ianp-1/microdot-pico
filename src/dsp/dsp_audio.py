import array

P_gain_ch1 = 0.5
P_gain_ch2 = 0.5
P_pan = 0
P_master_gain = 1

def SetMixerParam(gain_ch1=None, gain_ch2=None, pan=None, master_gain=None):
    global P_gain_ch1, P_gain_ch2, P_pan, P_master_gain
    
    if gain_ch1 is not None:
        P_gain_ch1 = gain_ch1
    if gain_ch2 is not None:
        P_gain_ch2 = gain_ch2
    if pan is not None:
        P_pan = pan
    if master_gain is not None:
        P_master_gain = master_gain

def scale(x, y, gain):
    for i in range(len(x)):
        y[i] = x[i] * gain

def sum(x, y, z):
    for i in range(len(x)):
        z[i] = x[i] + y[i]

def round(x, y):
    for i in range(len(x)):
        if x[i] < 0:
            y[i] = int(x[i] - 0.5)
        else:
            y[i] = int(x[i] + 0.5)

def round2bytes(x, y, bx, by):
    for i in range(len(x) // 2):
        if x[i] < 0:
            v = int(x[i] - 0.5)
        else:
            v = int(x[i] + 0.5)
        bx[2 * i] = v & 0xFF
        bx[2 * i + 1] = (v >> 8) & 0xFF
        if y[i] < 0:
            v = int(y[i] - 0.5)
        else:
            v = int(y[i] + 0.5)
        by[2 * i] = v & 0xFF
        by[2 * i + 1] = (v >> 8) & 0xFF

def dsp_mix_audio(in_1, in_2):
    frame_len = len(in_1) // 2
    #
    # make local floating point copy
    sig1 = [0] * frame_len
    sig2 = [0] * frame_len
    for i in range(frame_len):
        sig1[i] = float((in_1[i * 2 + 1] << 8) | in_1[i * 2])
        sig2[i] = float((in_2[i * 2 + 1] << 8) | in_2[i * 2])
    #
    # apply channel gain
    scale(sig1, sig1, P_gain_ch1)
    scale(sig2, sig2, P_gain_ch2)
    #
    # mix
    sum(sig1, sig2, sig2)
    #
    # apply master volume
    scale(sig2, sig2, P_master_gain)
    #
    # apply panning
    scale(sig2, sig1, 1 - (2 * P_pan))
    scale(sig2, sig2, 1 + (2 * P_pan))
    #
    # apply rounding and write byte arrays
    round2bytes(sig1, sig2, in_1, in_2)
