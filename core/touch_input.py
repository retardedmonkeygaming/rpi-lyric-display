import time
import threading
import RPi.GPIO as GPIO
from typing import Callable, Optional
from config import TOUCH_BUTTON_PIN


class TouchInputHandler:
    """
    Handles single capacitive touch button gestures on GPIO 27:
    - Short Press (< 1.0s): Cycle Next
    - Double Tap: Select / Confirm
    - Triple Tap: Stop Playback / Cancel
    - Long Press (>= 1.0s): Back / Menu Reset
    """

    def __init__(
        self,
        pin: int = TOUCH_BUTTON_PIN,
        on_short_press: Optional[Callable] = None,
        on_double_tap: Optional[Callable] = None,
        on_triple_tap: Optional[Callable] = None,
        on_long_press: Optional[Callable] = None,
    ):
        self.pin = pin
        self.on_short_press = on_short_press
        self.on_double_tap = on_double_tap
        self.on_triple_tap = on_triple_tap
        self.on_long_press = on_long_press

        self._running = False
        self._thread: Optional[threading.Thread] = None

        self._tap_count = 0
        self._last_release_time = 0.0
        self._press_start_time = 0.0
        self._is_pressed = False

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def start_listening(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop_listening(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)

    def _poll_loop(self):
        last_state = GPIO.input(self.pin)

        while self._running:
            current_state = GPIO.input(self.pin)
            now = time.time()

            if current_state == GPIO.HIGH and last_state == GPIO.LOW:
                self._is_pressed = True
                self._press_start_time = now

            elif current_state == GPIO.LOW and last_state == GPIO.HIGH:
                self._is_pressed = False
                duration = now - self._press_start_time

                if duration >= 1.0:
                    if self.on_long_press:
                        self.on_long_press()
                    self._tap_count = 0
                else:
                    if (now - self._last_release_time) < 0.40:
                        self._tap_count += 1
                    else:
                        self._tap_count = 1

                    self._last_release_time = now

                    threading.Thread(
                        target=self._evaluate_taps, args=(now, self._tap_count), daemon=True
                    ).start()

            last_state = current_state
            time.sleep(0.02)

    def _evaluate_taps(self, trigger_time: float, tap_count: int):
        time.sleep(0.40)
        if self._last_release_time == trigger_time:
            if tap_count == 1 and self.on_short_press:
                self.on_short_press()
            elif tap_count == 2 and self.on_double_tap:
                self.on_double_tap()
            elif tap_count >= 3 and self.on_triple_tap:
                self.on_triple_tap()
            self._tap_count = 0

    def cleanup(self):
        self.stop_listening()
        try:
            GPIO.cleanup(self.pin)
        except Exception:
            pass