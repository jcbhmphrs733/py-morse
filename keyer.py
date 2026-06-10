# keyer.py

from time import perf_counter, sleep
from queue import Empty

from events import Event, EventType, ElementType


class KeyerState:
    IDLE = "IDLE"
    SENDING_DIT = "SENDING_DIT"
    SENDING_DAH = "SENDING_DAH"
    ELEMENT_GAP = "ELEMENT_GAP"


class Keyer:
    """
    Iambic Morse keyer with Mode A / Mode B support.

    Consumes input events:
        DIT_DOWN / DIT_UP
        DAH_DOWN / DAH_UP
        STRAIGHT_KEY_DOWN / STRAIGHT_KEY_UP

    Produces:
        ELEMENT_START / ELEMENT_END
    """

    def __init__(self, event_queue, config):
        self.q = event_queue
        self.config = config

        # Paddle state
        self.dit_pressed = False
        self.dah_pressed = False

        # Memory (for squeeze behavior)
        self.dit_memory = False
        self.dah_memory = False

        # Straight key mode
        self.straight_active = False
        self.straight_start_time = None

        # Timing
        self.last_element = None  # "DIT" or "DAH"

        self.state = KeyerState.IDLE

        # internal timing
        self.element_start_time = None

    # -------------------------
    # MAIN LOOP ENTRY
    # -------------------------

    def process(self):
        """
        Called repeatedly from main loop.
        Handles input + state transitions.
        """

        self._drain_input_events()

        if self.config.input_mode.name == "STRAIGHT_KEY":
            self._process_straight_key()
        else:
            self._process_iambic()

    # -------------------------
    # INPUT HANDLING
    # -------------------------

    def _drain_input_events(self):
        """
        Pull all pending keyboard events.
        """
        try:
            while True:
                event = self.q.get_nowait()
                self._handle_event(event)
        except Empty:
            pass

    def _handle_event(self, event: Event):

        t = event.event_type

        # Paddle input
        if t == EventType.DIT_DOWN:
            self.dit_pressed = True
            self.dit_memory = True

        elif t == EventType.DIT_UP:
            self.dit_pressed = False

        elif t == EventType.DAH_DOWN:
            self.dah_pressed = True
            self.dah_memory = True

        elif t == EventType.DAH_UP:
            self.dah_pressed = False

        # Straight key
        elif t == EventType.STRAIGHT_KEY_DOWN:
            self.straight_active = True
            self.straight_start_time = perf_counter()

        elif t == EventType.STRAIGHT_KEY_UP:
            self.straight_active = False

    # -------------------------
    # STRAIGHT KEY MODE
    # -------------------------

    def _process_straight_key(self):
        """
        Straight key = no automation.
        """

        if self.straight_active and self.state == KeyerState.IDLE:
            self._start_element()

        elif not self.straight_active and self.state == KeyerState.SENDING_DIT:
            self._end_element()

    # -------------------------
    # IAMBIC MODE
    # -------------------------

    def _process_iambic(self):

        if self.state == KeyerState.IDLE:
            self._decide_next_element()

        elif self.state in (KeyerState.SENDING_DIT, KeyerState.SENDING_DAH):
            self._check_element_complete()

        elif self.state == KeyerState.ELEMENT_GAP:
            self._decide_next_element()

    # -------------------------
    # CORE DECISION LOGIC
    # -------------------------

    def _decide_next_element(self):

        # nothing pressed
        if not self.dit_pressed and not self.dah_pressed:
            return

        # both pressed → squeeze logic
        if self.dit_pressed and self.dah_pressed:
            if self.last_element == "DIT":
                self._start_dah()
            else:
                self._start_dit()
            return

        # single paddle
        if self.dit_pressed:
            self._start_dit()
        elif self.dah_pressed:
            self._start_dah()

    # -------------------------
    # ELEMENT CONTROL
    # -------------------------

    def _start_dit(self):
        self.state = KeyerState.SENDING_DIT
        self.element_start_time = perf_counter()
        self.last_element = "DIT"

        self.q.put(Event(
            EventType.ELEMENT_START,
            timestamp=self.element_start_time,
            element=ElementType.DIT
        ))

    def _start_dah(self):
        self.state = KeyerState.SENDING_DAH
        self.element_start_time = perf_counter()
        self.last_element = "DAH"

        self.q.put(Event(
            EventType.ELEMENT_START,
            timestamp=self.element_start_time,
            element=ElementType.DAH
        ))

    def _check_element_complete(self):
        """
        Ends element after correct duration.
        """

        now = perf_counter()
        duration = now - self.element_start_time

        # timing from config
        if self.state == KeyerState.SENDING_DIT:
            if duration >= self.config.dit_seconds:
                self._end_element()

        elif self.state == KeyerState.SENDING_DAH:
            if duration >= self.config.dah_seconds:
                self._end_element()

    def _end_element(self):

        now = perf_counter()

        self.q.put(Event(
            EventType.ELEMENT_END,
            timestamp=now
        ))

        self.state = KeyerState.ELEMENT_GAP
        self.element_start_time = None

    # -------------------------
    # OPTIONAL: GAP HANDLING HOOK
    # -------------------------

    def update_gap_timing(self):
        """
        Placeholder for future:
        - character spacing
        - word spacing
        - decoder integration
        """
        pass