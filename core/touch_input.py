import time
import RPi.GPIO as GPIO
from typing import Callable, Optional
from config import TOUCH_BUTTON_PIN


class TouchInputHandler:
    """
    Handles single capacitive touch button gestures on GPIO 27:
    - Short Press (< 0.5s): Cycle Next
    - Double Tap: Select / Confirm
    - Long Press (> 1.0s): Back / Cancel / Pause
    """

    def __init__(
        self,
        pin: int = TOUCH_BUTTON_PIN,
        on_short_press: Optional[Callable] = None,
        on_double_tap: Optional[Callable] = None,
        on_long_press: Optional[Callable] = None,
    ):
        self.pin = pin
        self.on_short_press = on_short_press
        self.on_double_tap = on_double_tap
        self.on_long_press = on_long_press

        self._last_press_time = 0.0
        self._press_start_time = 0.0
        self._is_pressed = False

        # Disable warnings and clean up previous pin states
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        
        try:
            GPIO.cleanup(self.pin)
        except Exception:
            pass

        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def start_listening(self):
        """Attaches GPIO interrupt handler for button state changes."""
        try:
            # Clean up existing event detects on this pin if any
            GPIO.remove_event_detect(self.pin)
        except Exception:
            pass

        try:
            GPIO.add_event_detect(
                self.pin, GPIO.BOTH, callback=self._gpio_callback, bouncetime=50
            )
        except RuntimeError:
            print(f"[WARNING] Edge detection failed on GPIO {self.pin}. Resetting pin...")
            GPIO.cleanup(self.pin)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(
                self.pin, GPIO.BOTH, callback=self._gpio_callback, bouncetime=50
            )

    def stop_listening(self):
        """Removes GPIO interrupt handlers."""
        try:
            GPIO.remove_event_detect(self.pin)
        except Exception:
            pass

    def _gpio_callback(self, channel: int):
        current_state = GPIO.input(self.pin)
        now = time.time()

        if current_state == GPIO.HIGH and not self._is_pressed:
            # Button Touch Detected
            self._is_pressed = True
            self._press_start_time = now

        elif current_state == GPIO.LOW and self._is_pressed:
            # Button Released
            self._is_pressed = False
            duration = now - self._press_start_time

            if duration >= 1.0:
                # Long Press Event
                if self.on_long_press:
                    self.on_long_press()
            else:
                # Check for Double Tap (within 0.35s window)
                if (now - self._last_press_time) < 0.35:
                    if self.on_double_tap:
                        self.on_double_tap()
                    self._last_press_time = 0.0
                else:
                    self._last_press_time = now
                    time.sleep(0.35)
                    if (time.time() - self._last_press_time) >= 0.35:
                        if self.on_short_press:
                            self.on_short_press()

    def cleanup(self):
        """Safely cleans up GPIO pin configuration."""
        self.stop_listening()
        try:
            GPIO.cleanup(self.pin)
        except Exception:
            pass


if __name__ == "__main__":
    print("Testing Touch Sensor on GPIO 27... Press Ctrl+C to stop.")

    def on_short():
        print("-> [EVENT] Short Press (Next Item)")

    def on_double():
        print("-> [EVENT] Double Tap (Select/Confirm)")

    def on_long():
        print("-> [EVENT] Long Press (Back/Pause)")

    handler = TouchInputHandler(
        on_short_press=on_short,
        on_double_tap=on_double,
        on_long_press=on_long,
    )
    handler.start_listening()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        handler.cleanup()
        print("\nTouch Handler Stopped.")