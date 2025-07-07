from machine import Pin

class LEDManager:
    def __init__(self):
        self.mode_leds = {
            "music":   Pin(5, Pin.OUT),
            "live":    Pin(4, Pin.OUT),
            "club":    Pin(3, Pin.OUT),
            "monitor": Pin(2, Pin.OUT)
        }
        self.turn_off_all()
    
    def turn_off_all(self):
        for led in self.mode_leds.values():
            led.value(1)
    
    def set_mode(self, mode):
        self.turn_off_all()
        if mode in self.mode_leds:
            self.mode_leds[mode].value(0)