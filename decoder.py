# decoder.py

from collections import deque
from dataclasses import dataclass, field

from events import Event, EventType
from morse_table import decode


@dataclass(slots=True)
class DecoderState:
    """
    Tracks timing-based decoding state.
    """

    # Current sequence of dots/dashes being built
    current_sequence: list[str] = field(default_factory=list)

    # Timing tracking
    last_event_time: float | None = None

    # Thresholds (filled in from config at runtime)
    dit_threshold: float = 0.15
    dah_threshold: float = 0.35

    # Gap detection
    intra_char_gap: float = 0.15
    char_gap: float = 0.35
    word_gap: float = 0.7


class Decoder:
    """
    Converts tone timing events into Morse characters.

    Input:
        ELEMENT_START
        ELEMENT_END

    Output:
        CHARACTER_DECODED
        WORD_BREAK
        Raw '?' for unknown sequences
    """

    def __init__(self, config):
        self.config = config
        self.state = DecoderState()

        # buffer of output events
        self.output: deque[Event] = deque()

        # update thresholds from config
        self._sync_config()

    def _sync_config(self):
        """
        Convert config timing into thresholds.

        We classify elements based on duration:
            < 2 units -> dit
            >= 2 units -> dah
        """
        dit = self.config.dit_seconds

        self.state.dit_threshold = dit * 2
        self.state.dah_threshold = dit * 4

        self.state.intra_char_gap = dit * 1.5
        self.state.char_gap = dit * 3.0
        self.state.word_gap = dit * 7.0

    def push(self, event: Event):
        """
        Main entry point.

        The decoder only cares about ELEMENT_START and ELEMENT_END.
        """

        if event.event_type == EventType.ELEMENT_START:
            self._on_start(event)

        elif event.event_type == EventType.ELEMENT_END:
            self._on_end(event)

    def _on_start(self, event: Event):
        self.state.last_event_time = event.timestamp

    def _on_end(self, event: Event):
        if self.state.last_event_time is None:
            return

        duration = event.timestamp - self.state.last_event_time

        symbol = self._classify(duration)
        self.state.current_sequence.append(symbol)

        self.state.last_event_time = event.timestamp

    def _classify(self, duration: float) -> str:
        """
        Convert timing into '.' or '-'
        """
        if duration < self.state.dit_threshold:
            return "."
        return "-"

    def finalize_character(self):
        """
        Called when a character gap is detected.
        """
        if not self.state.current_sequence:
            return

        seq = "".join(self.state.current_sequence)
        char = decode(seq)

        self.output.append(
            Event(
                event_type=EventType.CHARACTER_DECODED,
                character=char,
            )
        )

        self.state.current_sequence.clear()

    def finalize_word(self):
        """
        Called when a word gap is detected.
        """
        self.finalize_character()

        self.output.append(
            Event(
                event_type=EventType.WORD_BREAK,
            )
        )

    def get_events(self) -> list[Event]:
        """
        Drain output events.
        """
        events = list(self.output)
        self.output.clear()
        return events