from machine import Pin
from lib.updebouncein.debounced_input import DebouncedInput

class ButtonManager:
    def __init__(self, button_config):
        self.callbacks = {}
        self.buttons = []
        self._setup_buttons(button_config)
    
    def _setup_buttons(self, button_config):
        for pin_number, callback in button_config.items():
            if callback:
                self.callbacks[pin_number] = callback
                button = DebouncedInput(
                    pin_number,
                    callback=self._handle_button_event,
                    debounce_ms=4,
                    pin_logic_pressed=True,
                    pin_pull=Pin.PULL_DOWN
                )
                self.buttons.append(button)
    
    def _handle_button_event(self, pin_number, is_pressed, duration_ms):
        if is_pressed and pin_number in self.callbacks:
            print(f"[BUTTON] GP{pin_number} pressed")
            self.callbacks[pin_number]()