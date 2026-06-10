# carrier_visualizer.py

"""
Scrolling carrier waveform visualizer.

Polls audio.tone_active at a fixed interval and renders a square-wave
trace on a tkinter Canvas — high when the tone is on, low when off.

No queues are shared with other components; the only dependency is
reading the boolean AudioEngine.tone_active flag.
"""

import tkinter as tk
from collections import deque


class CarrierVisualizer:
    """
    Embeddable tkinter Canvas showing a scrolling square-wave of
    carrier state: tone ON = high rail, tone OFF = low rail.

    The canvas fills whatever horizontal space its parent offers.
    pixels_per_sample controls how many screen pixels each sample
    occupies, stretching the waveform for easier reading.

    Usage:
        vis = CarrierVisualizer(parent_frame, audio_engine, ...)
        vis.pack(fill="x")
        vis.start()          # call once after mainloop begins
    """

    _SAMPLE_MS   = 20    # poll interval in ms (50 samples / sec)
    _MAX_SAMPLES = 2000  # ring buffer ceiling — more than any window width

    def __init__(
        self,
        parent: tk.Widget,
        audio,
        *,
        height: int = 48,
        pixels_per_sample: int = 3,
        bg: str = "#1e1e1e",
        color_on: str = "#569cd6",
        color_mid: str = "#3c3c3c",
    ):
        self._audio             = audio
        self._height            = height
        self._pixels_per_sample = pixels_per_sample
        self._color_on          = color_on
        self._color_mid         = color_mid

        # Ring buffer — large enough for any window width
        self._samples: deque[bool] = deque(maxlen=self._MAX_SAMPLES)

        # No explicit width — the canvas expands to fill its parent
        self.canvas = tk.Canvas(
            parent,
            height=height,
            bg=bg,
            highlightthickness=0,
            bd=0,
        )

    # -------------------------
    # GEOMETRY DELEGATION
    # -------------------------

    def pack(self, **kwargs):
        self.canvas.pack(**kwargs)

    def grid(self, **kwargs):
        self.canvas.grid(**kwargs)

    # -------------------------
    # PUBLIC API
    # -------------------------

    def start(self):
        """Begin polling. Call once after the tkinter mainloop is running."""
        self._tick()

    # -------------------------
    # INTERNAL
    # -------------------------

    def _tick(self):
        self._samples.append(bool(self._audio.tone_active))
        self._redraw()
        self.canvas.after(self._SAMPLE_MS, self._tick)

    def _redraw(self):
        c = self.canvas
        w = c.winfo_width()
        if w < 2:
            return  # canvas not yet realized

        c.delete("all")

        h   = self._height
        pps = self._pixels_per_sample

        y_high = 6
        y_low  = h - 6
        y_mid  = h // 2

        # Dashed centre axis
        c.create_line(
            0, y_mid, w, y_mid,
            fill=self._color_mid, dash=(2, 6),
        )

        # How many samples fit at the current zoom level
        n_visible = w // pps
        samples = list(self._samples)[-n_visible:]

        # Build a step-function polyline.
        # Insert a vertical-edge point before each y-transition so the
        # trace goes horizontal then vertical rather than diagonal.
        pts: list[int] = []
        prev_y: int | None = None
        for i, active in enumerate(samples):
            x = i * pps
            y = y_high if active else y_low
            if prev_y is not None and y != prev_y:
                pts += [x, prev_y]   # vertical edge of step
            pts += [x, y]
            prev_y = y

        if len(pts) >= 4:
            c.create_line(pts, fill=self._color_on, width=2, smooth=False)
