import time
import threading
import RPi.GPIO as GPIO
from typing import Callable, Optional
from config import TOUCH_BUTTON_PIN


class TouchInputHandler:
    """
    Handles single capacitive touch button gestures on GPIO 27 using 
    thread-safe polling (bypasses broken RPi.GPIO edge detection):
    - Short Press (< 1.0s): Cycle Next
    - Double Tap: Select / Confirm
    - Long Press (>= 1.0s): Back / Cancel / Pause
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

        self._running = False
        self._thread: Optional[threading.Thread] = None

        self._last_release_time = 0.0
        self._press_start_time = 0.0
        self._is_pressed = False

        # Initialize GPIO
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def start_listening(self):
        """Starts background polling thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop_listening(self):
        """Stops background polling thread."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)

    def _poll_loop(self):
        """20ms polling loop to detect state changes cleanly."""
        last_state = GPIO.input(self.pin)

        while self._running:
            current_state = GPIO.input(self.pin)
            now = time.time()

            # Rising edge: Touch started
            if current_state == GPIO.HIGH and last_state == GPIO.LOW:
                self._is_pressed = True
                self._press_start_time = now

            # Falling edge: Touch released
            elif current_state == GPIO.LOW and last_state == GPIO.HIGH:
                self._is_pressed = False
                duration = now - self._press_start_time

                if duration >= 1.0:
                    # Long Press Event
                    if self.on_long_press:
                        self.on_long_press()
                else:
                    # Check for Double Tap (within 0.35s window)
                    if (now - self._last_release_time) < 0.35:
                        if self.on_double_tap:
                            self.on_double_tap()
                        self._last_release_time = 0.0  # Reset
                    else:
                        self._last_release_time = now
                        # Launch short-press delay checker
                        threading.Thread(
                            target=self._check_single_tap, args=(now,), daemon=True
                        ).start()

            last_state = current_state
            time.sleep(0.02)  # 20ms poll rate (50Hz)

    def _check_single_tap(self, trigger_time: float):
        """Waits 0.35s to ensure no second tap occurs before executing short press."""
        time.sleep(0.35)
        if self._last_release_time == trigger_time:
            if self.on_short_press:
                self.on_short_press()

    def cleanup(self):
        """Safely stops listener and cleans up GPIO."""
        self.stop_listening()
        try:
            GPIO.cleanup(self.pin)
        except Exception:
            pass


if __name__ == "__main__":
    print("Testing Touch Sensor on GPIO 27 (Polled)... Press Ctrl+C to stop.")

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