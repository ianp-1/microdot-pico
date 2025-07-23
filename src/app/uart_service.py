

import time
from machine import UART, Pin

class UARTService:
    def __init__(self, uart_id=0, baud_rate=115200, tx_pin=0, rx_pin=1):
        self.uart = UART(uart_id, baud_rate, tx=Pin(tx_pin), rx=Pin(rx_pin))
        print("UART Controller Ready.")

    def send_command(self, param: str, value: float):
        """Formats and sends a DSP command over UART."""
        cmd = f"{param} {value}\n"
        self.uart.write(cmd)
        print(f"Sent -> {cmd.strip()}")

    def deinit(self):
        self.uart.deinit()
        print("UART closed.")

uart_service = UARTService()

