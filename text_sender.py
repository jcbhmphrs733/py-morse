# text_sender.py

"""
Converts a text string into Morse ELEMENT_START / ELEMENT_END events
and feeds them directly into the dispatcher queue (q2).

Runs in its own daemon thread so the GUI stays responsive.
Supports stop() to cancel mid-send.
"""

import threading
from time import perf_counter, sleep

from events import Event, EventType, ElementType
from morse_table import CHAR_TO_MORSE


def _precise_sleep(seconds: float):
    """
    Sleep with better-than-15ms accuracy on Windows.
    Uses time.sleep for the bulk, then spin-waits the last 5ms.
    """
    if seconds <= 0:
        return
    deadline = perf_counter() + seconds
    bulk = seconds - 0.005
    if bulk > 0:
        sleep(bulk)
    while perf_counter() < deadline:
        pass


class TextSender:
    """
    Sends a text string as Morse tones into an event queue.

    Usage:
        sender = TextSender(q2, config)
        sender.send("HELLO WORLD")   # starts background thread
        sender.stop()                # cancels if running
    """

    def __init__(self, output_queue, config):
        self._q = output_queue
        self.config = config
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self.current_index: int = -1  # index into text being sent, -1 = idle

    # -------------------------
    # PUBLIC API
    # -------------------------

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def send(self, text: str):
        """Start sending text. Cancels any in-progress send first."""
        self.stop()
        self.current_index = -1
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, args=(text.upper(),), daemon=True
        )
        self._thread.start()

    def stop(self):
        """Signal the sender to stop and wait for it to finish."""
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join(timeout=1.0)
        self.current_index = -1

    # -------------------------
    # INTERNAL
    # -------------------------

    def _run(self, text: str):
        for i, char in enumerate(text):
            if self._stop_event.is_set():
                return

            self.current_index = i

            if char == " ":
                # word gap = 7 dits, but a char gap (3 dits) already follows
                # the previous character, so we only add the remaining 4 dits
                _precise_sleep(self.config.dit_seconds * 4)
                continue

            sequence = CHAR_TO_MORSE.get(char)
            if sequence is None:
                continue  # skip unknown characters

            for j, symbol in enumerate(sequence):
                if self._stop_event.is_set():
                    return

                is_dit = symbol == "."
                duration = (
                    self.config.dit_seconds if is_dit
                    else self.config.dah_seconds
                )
                element = ElementType.DIT if is_dit else ElementType.DAH

                # Element on
                self._q.put(Event(
                    event_type=EventType.ELEMENT_START,
                    element=element,
                ))
                _precise_sleep(duration)

                # Element off
                self._q.put(Event(event_type=EventType.ELEMENT_END))

                # Intra-character gap (skip after last element)
                if j < len(sequence) - 1:
                    _precise_sleep(self.config.dit_seconds)

            # Character gap (3 dits) after each letter
            _precise_sleep(self.config.dit_seconds * 3)
