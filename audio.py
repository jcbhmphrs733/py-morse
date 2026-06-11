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
        self._envelope = 0.0   # current amplitude 0.0–1.0 (ramped)

        # Ramp length: 5 ms
        self._ramp_samples = max(1, int(0.005 * self.sample_rate))

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
            pass

        target = 1.0 if self.tone_active else 0.0
        step   = 1.0 / self._ramp_samples

        if self._envelope == target:
            env = np.full(frames, target)
        else:
            direction = 1.0 if target > self._envelope else -1.0
            raw = self._envelope + direction * step * (np.arange(frames) + 1)
            if direction > 0:
                env = np.minimum(raw, target)
            else:
                env = np.maximum(raw, target)

        self._envelope = float(env[-1])

        t = (np.arange(frames) + self.phase) / self.sample_rate
        wave = np.sin(2 * np.pi * self.config.sidetone_hz * t) * env * self.config.sidetone_volume

        outdata[:] = wave.reshape(-1, 1)

        self.phase += frames
        self.phase %= self.sample_rate