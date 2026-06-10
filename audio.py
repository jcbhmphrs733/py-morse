# audio.py

import numpy as np
import sounddevice as sd
from queue import Empty

from events import EventType


class AudioEngine:
    """
    Generates CW sidetone from keyer events.

    Input:
        ELEMENT_START
        ELEMENT_END

    Output:
        Continuous sine wave audio stream
    """

    def __init__(self, event_queue, config):
        self.q = event_queue
        self.config = config

        self.sample_rate = config.sample_rate
        self.frequency = config.sidetone_hz

        # audio state
        self.tone_active = False
        self.phase = 0.0

        # streaming buffer control
        self.stream = None

    # -------------------------
    # PUBLIC API
    # -------------------------

    def start(self):
        """
        Start audio output stream.
        """
        self.stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=1,
            callback=self._audio_callback,
        )
        self.stream.start()

    def stop(self):
        """
        Stop audio output stream.
        """
        if self.stream:
            self.stream.stop()
            self.stream.close()

    def process(self):
        """
        Poll events from queue.
        """
        try:
            while True:
                event = self.q.get_nowait()
                self._handle_event(event)
        except Empty:
            pass

    # -------------------------
    # EVENT HANDLING
    # -------------------------

    def _handle_event(self, event):

        if event.event_type == EventType.ELEMENT_START:
            self.tone_active = True

        elif event.event_type == EventType.ELEMENT_END:
            self.tone_active = False

    # -------------------------
    # AUDIO CALLBACK
    # -------------------------

    def _audio_callback(self, outdata, frames, time, status):
        """
        Real-time audio generation callback.
        """

        if status:
            # In a real app you'd log this
            pass

        # time vector for this buffer
        t = (np.arange(frames) + self.phase) / self.sample_rate

        if self.tone_active:
            wave = np.sin(2 * np.pi * self.frequency * t)
        else:
            wave = np.zeros(frames)

        outdata[:] = wave.reshape(-1, 1)

        # update phase to avoid clicks
        self.phase += frames
        self.phase %= self.sample_rate