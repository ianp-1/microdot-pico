from machine import Pin
from lib.updebouncein.debounced_input import DebouncedInput

class AudioModel:
    def __init__(self):
        # Voice Modes and Current State
        self.voice_modes = ["music", "live", "club", "monitor", "off"]
        self.current_mode_index = 4  # Start in "off" mode
        self.current_mode = self.voice_modes[self.current_mode_index]

        # Voice Mode LEDs (active-low: 0 = ON, 1 = OFF)
        self.mode_leds = {
            "music":   Pin(5, Pin.OUT),
            "live":    Pin(4, Pin.OUT),
            "club":    Pin(3, Pin.OUT),
            "monitor": Pin(2, Pin.OUT)
        }
        self._update_mode_leds()

        # Button Actions Mapping (GP pin -> function)
        self.button_actions = {
            6: None,                  # Reserved for future use
            7: None,                  # Reserved for future use
            8: None,                  # Reserved for future use
            9: self.toggle_voice_mode  # Toggle voice mode on button press
        }

        # Set up debounced button inputs
        self.buttons = []
        for pin_number, action in self.button_actions.items():
            button = DebouncedInput(
                pin_number,
                callback=self._handle_button_event,
                debounce_ms=4,
                pin_logic_pressed=True,
                pin_pull=Pin.PULL_DOWN
            )
            self.buttons.append(button)

    def toggle_voice_mode(self):
        # Cycle to the next voice mode
        self.current_mode_index = (self.current_mode_index + 1) % len(self.voice_modes)
        self.current_mode = self.voice_modes[self.current_mode_index]
        self._update_mode_leds()
        print(f"[MODE] Voice mode changed to: {self.current_mode}")

    def _update_mode_leds(self):
        # Turn off all LEDs first
        for led in self.mode_leds.values():
            led.value(1)
        
        # Then turn on the LED for the current mode (if it's not "off")
        if self.current_mode in self.mode_leds:
            self.mode_leds[self.current_mode].value(0)

    def _handle_button_event(self, pin_number, is_pressed, duration_ms):
        # Only respond to press events (not release)
        if is_pressed:
            print(f"[BUTTON] GP{pin_number} pressed")
            action = self.button_actions.get(pin_number)
            if action:
                action()
