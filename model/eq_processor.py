from machine import ADC
import json
import uasyncio as asyncio
import time

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
        
        # Track last control source for each band
        self.last_control_source = {"low": "physical", "mid": "physical", "high": "physical"}
        self.last_control_time = {"low": 0, "mid": 0, "high": 0}
        # Remove automatic timeout - digital control persists until physical movement
    
    def add_update_callback(self, callback):
        self.update_callbacks.append(callback)
    
    def adc_to_db(self, raw):
        scaled = raw / 65535 * 4095
        db = -11.8 + (scaled / 4095 * 24.0)
        return -round(max(-12.0, min(db, 12.0)), 1)
    
    def monitor_dials(self):
        """Monitor physical dials with last-controlled priority"""
        current = {band: self.adc[band].read_u16() for band in self.adc}
        updated = False
        current_time = time.ticks_ms()

        for band in current:
            # Check if digital control has priority - no automatic timeout
            if self.last_control_source[band] == 'digital':
                # Skip physical monitoring while in digital mode
                # Only physical movement can override digital control
                prev = self.last_raw[band]
                curr = current[band]
                
                # Check for significant physical movement (larger threshold to avoid accidental override)
                if prev is not None and abs(curr - prev) > self.deadzone * 2:
                    print(f"[EQ] Physical movement detected for {band}, overriding digital control")
                    # Fall through to process the physical change
                else:
                    # No significant physical movement, stay in digital mode
                    continue
            
            # Process physical dial changes
            prev = self.last_raw[band]
            curr = current[band]

            if prev is None or abs(curr - prev) > self.deadzone:
                old_value = self.live_db[band]
                new_value = self.adc_to_db(curr)
                
                self.last_raw[band] = curr
                self.live_db[band] = new_value
                
                # Update control tracking
                self.last_control_source[band] = 'physical'
                self.last_control_time[band] = current_time
                
                print(f"[EQ DIAL] {band}: {old_value:.1f} -> {new_value:.1f} dB (physical control)")
                updated = True

        if updated:
            print(f"[EQ] Current - Low: {self.live_db['low']:.1f} dB, Mid: {self.live_db['mid']:.1f} dB, High: {self.live_db['high']:.1f} dB")
            
            # Notify all callbacks with both EQ data and control source info
            callback_data = {
                'eq': self.live_db.copy(),
                'control_sources': self.last_control_source.copy()
            }
            for callback in self.update_callbacks:
                callback(callback_data)
    
    def set_target_eq(self, band, value, source='digital'):
        """Set target EQ value with source tracking"""
        if band in self.target_eq:
            try:
                old_value = self.live_db[band]
                new_value = float(value)
                
                self.target_eq[band] = new_value
                self.live_db[band] = new_value
                
                # Update control tracking
                self.last_control_source[band] = source
                self.last_control_time[band] = time.ticks_ms()
                
                print(f"[EQ SET] {band}: {old_value:.1f} -> {new_value:.1f} dB ({source} control - persists until physical movement)")
                
                # Notify callbacks immediately with both EQ data and control source info
                callback_data = {
                    'eq': self.live_db.copy(),
                    'control_sources': self.last_control_source.copy()
                }
                for callback in self.update_callbacks:
                    callback(callback_data)
                    
            except ValueError:
                print(f"[EQ ERROR] Invalid value for {band}: {value}")
    
    async def monitor_loop(self, interval_ms=50):
        while True:
            self.monitor_dials()
            await asyncio.sleep_ms(interval_ms)