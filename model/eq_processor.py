from machine import ADC
import json
import uasyncio as asyncio

class EQProcessor:
    def __init__(self, deadzone=300):
        self.adc = {
            "low": ADC(26),
            "mid": ADC(27),
            "high": ADC(28)
        }
        
        self.last_raw = {"low": 0.0, "mid": 0.0, "high": 0.0}
        self.live_db = {"low": 0.0, "mid": 0.0, "high": 0.0}
        self.target_eq = {"low": 0.0, "mid": 0.0, "high": 0.0}
        self.deadzone = deadzone
        self.update_callbacks = []
    
    def add_update_callback(self, callback):
        self.update_callbacks.append(callback)
    
    def adc_to_db(self, raw):
        scaled = raw / 65535 * 4095
        db = -12 + (scaled / 4095 * 24.0)
        return -round(max(-12.0, min(db, 12.0)), 1)
    
    def monitor_dials(self):
        current = {band: self.adc[band].read_u16() for band in self.adc}
        updated = False

        for band in current:
            prev = self.last_raw[band]
            curr = current[band]

            if prev is None or abs(curr - prev) > self.deadzone:
                self.last_raw[band] = curr
                self.live_db[band] = self.adc_to_db(curr)
                updated = True

        if updated:
            print(f"[EQ] Low: {self.live_db['low']} dB, Mid: {self.live_db['mid']} dB, High: {self.live_db['high']} dB")
            
            # Notify all callbacks
            for callback in self.update_callbacks:
                callback(self.live_db.copy())
    
    def set_target_eq(self, band, value):
        if band in self.target_eq:
            try:
                self.target_eq[band] = float(value)
                print(f"[EQ SET] {band}: {value} dB (from slider)")
            except ValueError:
                print(f"[EQ ERROR] Invalid value for {band}: {value}")
    
    async def monitor_loop(self, interval_ms=50):
        while True:
            self.monitor_dials()
            await asyncio.sleep_ms(interval_ms)