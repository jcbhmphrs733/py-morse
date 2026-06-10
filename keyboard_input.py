# keyboard_input.py

from pynput import keyboard
from time import perf_counter

from config import PaddleLayout
from events import Event, EventType


class KeyboardInput:
    """
    Converts keyboard events into Morse input events.

    No timing logic beyond timestamps.
    No keyer logic.
    """

    def __init__(self, event_queue, config):
        self.event_queue = event_queue
        self.config = config

        # Track current key states (important for squeeze logic later)
        self.dit_pressed = False
        self.dah_pressed = False
        self.straight_pressed = False

        # Key mapping (from config)
        self.left_paddle_key = self._normalize(config.left_paddle_key)
        self.right_paddle_key = self._normalize(config.right_paddle_key)
        self.straight_key = self._normalize(config.straight_key)

    def _normalize(self, key):
        """
        Normalize key config values. Integers (VK codes) are stored as-is;
        strings are lower-cased for comparison.
        """
        if isinstance(key, int):
            return key
        return key.lower()

    def _get_vk(self, key):
        """Extract the VK code from a pynput Key or KeyCode object."""
        if isinstance(key, keyboard.Key):
            v = key.value
            return v.vk if v is not None else None
        if isinstance(key, keyboard.KeyCode):
            return key.vk
        return None

    def _matches(self, key, stored_key) -> bool:
        """Check whether a pynput key matches a stored config key."""
        if isinstance(stored_key, int):
            return self._get_vk(key) == stored_key
        return self._key_to_string(key) == stored_key

    def _dit_key(self):
        """Return the VK/string for whichever physical key is currently dit."""
        if self.config.paddle_layout == PaddleLayout.LEFT_DIT_RIGHT_DAH:
            return self.left_paddle_key
        return self.right_paddle_key

    def _dah_key(self):
        """Return the VK/string for whichever physical key is currently dah."""
        if self.config.paddle_layout == PaddleLayout.LEFT_DIT_RIGHT_DAH:
            return self.right_paddle_key
        return self.left_paddle_key

    def start(self):
        """
        Start listening to keyboard events.
        """
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self.listener.start()

    def _now(self) -> float:
        return perf_counter()

    def _on_press(self, key):
        timestamp = self._now()

        # Straight key mode
        if self._matches(key, self.straight_key):
            if not self.straight_pressed:
                self.straight_pressed = True
                self._emit(EventType.STRAIGHT_KEY_DOWN, timestamp)

        # Paddle inputs
        elif self._matches(key, self._dit_key()):
            if not self.dit_pressed:
                self.dit_pressed = True
                self._emit(EventType.DIT_DOWN, timestamp)

        elif self._matches(key, self._dah_key()):
            if not self.dah_pressed:
                self.dah_pressed = True
                self._emit(EventType.DAH_DOWN, timestamp)

    def _on_release(self, key):
        timestamp = self._now()

        # Straight key mode
        if self._matches(key, self.straight_key):
            if self.straight_pressed:
                self.straight_pressed = False
                self._emit(EventType.STRAIGHT_KEY_UP, timestamp)

        # Paddle inputs
        elif self._matches(key, self._dit_key()):
            if self.dit_pressed:
                self.dit_pressed = False
                self._emit(EventType.DIT_UP, timestamp)

        elif self._matches(key, self._dah_key()):
            if self.dah_pressed:
                self.dah_pressed = False
                self._emit(EventType.DAH_UP, timestamp)

    def _emit(self, event_type, timestamp):
        """
        Push event into shared queue.
        """
        
        self.event_queue.put(
            Event(
                event_type=event_type,
                timestamp=timestamp,
            )
        )
        

    def _key_to_string(self, key):
        """
        Convert pynput key object into comparable string.
        """
        try:
            if hasattr(key, "char") and key.char:
                return key.char.lower()
        except Exception:
            pass

        # Special keys (space, etc.)
        return str(key).replace("Key.", "").lower()