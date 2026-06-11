# gui.py

import tkinter as tk
from tkinter import ttk

from config import Config, InputMode, PaddleLayout
from config_io import save_config
from decoder import Decoder
from events import EventType
from morse_table import CHAR_TO_MORSE
from carrier_visualizer import CarrierVisualizer


# Dark theme palette
_BG      = "#1e1e1e"
_BG2     = "#2d2d2d"
_FG      = "#d4d4d4"
_MUTED   = "#6b737c"
_ACCENT  = "#3a7ebf"
_BORDER  = "#3c3c3c"
_SELECT  = "#264f78"


class MorseGUI:
    """
    MVP tkinter GUI for Morse Trainer.

    Displays decoded output and exposes config sliders/dropdowns
    that take effect immediately at runtime.
    """

    def __init__(self, root: tk.Tk, config: Config, decoder: Decoder, audio, keyboard_input):
        self.root = root
        self.config = config
        self.decoder = decoder
        self._audio = audio
        self._keyboard = keyboard_input

        self.root.title("Morse Trainer")
        self.root.resizable(False, False)

        self._apply_dark_theme()

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True)

        main_tab     = ttk.Frame(notebook)
        settings_tab = ttk.Frame(notebook)
        notebook.add(main_tab,     text="  Main  ")
        notebook.add(settings_tab, text="  Settings  ")

        self._build_output(main_tab)
        self._build_visualizer(main_tab)
        mid = ttk.Frame(main_tab)
        mid.pack(fill="x", padx=10, pady=(4, 10))
        mid.columnconfigure(1, weight=1)
        self._build_controls(mid)
        self._build_cheatsheet(mid)

        self._build_settings_tab(settings_tab)

        self._poll_decoder()
        self._visualizer.start()

    def _apply_dark_theme(self):
        self.root.configure(bg=_BG)

        # Combobox dropdown list (tk Listbox, not ttk)
        self.root.option_add("*TCombobox*Listbox.background",        _BG2)
        self.root.option_add("*TCombobox*Listbox.foreground",        _FG)
        self.root.option_add("*TCombobox*Listbox.selectBackground",  _SELECT)
        self.root.option_add("*TCombobox*Listbox.selectForeground",  _FG)

        s = ttk.Style(self.root)
        s.theme_use("clam")

        s.configure(".",
            background=_BG, foreground=_FG,
            fieldbackground=_BG2, bordercolor=_BORDER,
            darkcolor=_BG, lightcolor=_BG2,
            troughcolor=_BG2, selectbackground=_SELECT,
            selectforeground=_FG, insertcolor=_FG,
        )
        s.configure("TFrame",      background=_BG)
        s.configure("TLabel",      background=_BG,  foreground=_FG)
        s.configure("TLabelframe", background=_BG,  foreground=_FG, bordercolor=_BORDER)
        s.configure("TLabelframe.Label", background=_BG, foreground=_FG)
        s.configure("TButton",
            background=_BG2, foreground=_FG,
            bordercolor=_BORDER, focuscolor=_BG, relief="flat",
        )
        s.map("TButton",
            background=[("active", _BORDER), ("pressed", _SELECT)],
        )
        s.configure("TCombobox",
            fieldbackground=_BG2, background=_BG2,
            foreground=_FG, arrowcolor=_FG,
            selectbackground=_SELECT, selectforeground=_FG,
        )
        s.map("TCombobox",
            fieldbackground=[("readonly", _BG2)],
            selectbackground=[("readonly", _SELECT)],
        )
        s.configure("TScale",
            background=_BG, troughcolor=_BG2,
            sliderlength=14, sliderrelief="flat",
        )
        s.map("TScale", background=[("active", _ACCENT)])
        s.configure("TScrollbar",
            background=_BG2, troughcolor=_BG,
            arrowcolor=_FG, bordercolor=_BORDER, relief="flat",
        )
        s.configure("TEntry",
            fieldbackground=_BG2, foreground=_FG,
            insertcolor=_FG, bordercolor=_BORDER, relief="flat",
        )
        s.configure("TNotebook",
            background=_BG, bordercolor=_BORDER, tabmargins=[0, 0, 0, 0],
        )
        s.configure("TNotebook.Tab",
            background=_BG2, foreground=_MUTED,
            padding=[12, 5], bordercolor=_BORDER,
        )
        s.map("TNotebook.Tab",
            background=[("selected", _BG)],
            foreground=[("selected", _FG)],
        )

    # -------------------------
    # OUTPUT PANEL
    # -------------------------

    def _build_output(self, parent):
        frame = ttk.LabelFrame(parent, text="Decoded Output", padding=6)
        frame.pack(fill="both", expand=True, padx=10, pady=(10, 4))

        self.output = tk.Text(
            frame, width=60, height=5, state="disabled",
            wrap="word", font=("Courier", 13),
            bg=_BG2, fg=_FG, insertbackground=_FG,
            selectbackground=_SELECT, selectforeground=_FG,
            relief="flat", bd=0,
        )
        self.output.pack(fill="both", expand=True)

        ttk.Button(frame, text="Clear", command=self._clear_output).pack(
            anchor="e", pady=(4, 0)
        )

    def _build_visualizer(self, parent):
        frame = ttk.LabelFrame(parent, text="Carrier", padding=4)
        frame.pack(fill="x", padx=10, pady=(0, 4))
        self._visualizer = CarrierVisualizer(
            frame, self._audio,
            bg=_BG, color_on=self.config.carrier_color, color_mid=_BORDER,
        )
        self._visualizer.pack(fill="x")

    # -------------------------
    # CONTROLS PANEL
    # -------------------------

    def _build_controls(self, parent):
        frame = ttk.LabelFrame(parent, text="Configuration", padding=8)
        frame.grid(row=0, column=0, sticky="nw", padx=(0, 8))

        self._add_int_row(
            frame, 0, "WPM", 5, 40, self.config.wpm,
            lambda v: self._set_wpm(v),
        )
        self._add_float_row(
            frame, 1, "Dah Weight", 2.5, 3.5, self.config.dah_weight,
            lambda v: self._set_dah_weight(v),
        )
        self._add_float_row(
            frame, 2, "Letter Gap (×dit)", 2.0, 12.0, self.config.char_gap_multiplier,
            lambda v: self._set_timing("char_gap_multiplier", v),
        )
        self._add_float_row(
            frame, 3, "Word Gap (×dit)", 5.0, 25.0, self.config.word_gap_multiplier,
            lambda v: self._set_timing("word_gap_multiplier", v),
        )

        # Live timing display
        ttk.Separator(frame, orient="horizontal").grid(
            row=4, column=0, columnspan=3, sticky="ew", pady=(8, 4)
        )
        self._dit_ms_var = tk.StringVar()
        self._dah_ms_var = tk.StringVar()
        self._update_timing_display()

        ttk.Label(frame, text="Dit", foreground=_MUTED).grid(
            row=5, column=0, sticky="w", padx=(0, 8)
        )
        ttk.Label(frame, textvariable=self._dit_ms_var, foreground=_FG).grid(
            row=5, column=1, sticky="w"
        )
        ttk.Label(frame, text="Dah", foreground=_MUTED).grid(
            row=6, column=0, sticky="w", padx=(0, 8), pady=(2, 0)
        )
        ttk.Label(frame, textvariable=self._dah_ms_var, foreground=_FG).grid(
            row=6, column=1, sticky="w"
        )

    def _add_int_row(self, parent, row, label, lo, hi, initial, on_change):
        last = [initial]
        var = tk.StringVar(value=str(initial))

        ttk.Label(parent, text=label).grid(
            row=row, column=0, sticky="w", pady=3, padx=(0, 8)
        )

        entry = ttk.Entry(parent, textvariable=var, width=7)
        entry.grid(row=row, column=1, sticky="w", padx=(0, 6))

        ttk.Label(parent, text=f"{lo} – {hi}", foreground=_MUTED).grid(
            row=row, column=2, sticky="w"
        )

        def _apply(*_):
            try:
                v = max(lo, min(hi, int(float(var.get()))))
                last[0] = v
                on_change(v)
                var.set(str(v))
            except ValueError:
                var.set(str(last[0]))

        entry.bind("<Return>", _apply)
        entry.bind("<FocusOut>", _apply)

    def _add_float_row(self, parent, row, label, lo, hi, initial, on_change):
        last = [initial]
        var = tk.StringVar(value=f"{initial:.1f}")

        ttk.Label(parent, text=label).grid(
            row=row, column=0, sticky="w", pady=3, padx=(0, 8)
        )

        entry = ttk.Entry(parent, textvariable=var, width=7)
        entry.grid(row=row, column=1, sticky="w", padx=(0, 6))

        ttk.Label(parent, text=f"{lo:.1f} – {hi:.1f}", foreground=_MUTED).grid(
            row=row, column=2, sticky="w"
        )

        def _apply(*_):
            try:
                v = max(lo, min(hi, round(float(var.get()), 1)))
                last[0] = v
                on_change(v)
                var.set(f"{v:.1f}")
            except ValueError:
                var.set(f"{last[0]:.1f}")

        entry.bind("<Return>", _apply)
        entry.bind("<FocusOut>", _apply)

    # -------------------------
    # CHEAT SHEET PANEL
    # -------------------------

    def _build_cheatsheet(self, parent):
        frame = ttk.LabelFrame(parent, text="Morse Code Reference", padding=6)
        frame.grid(row=0, column=1, sticky="nw")

        letters = sorted(c for c in CHAR_TO_MORSE if c.isalpha())
        digits  = sorted(c for c in CHAR_TO_MORSE if c.isdigit())
        entries = letters + digits

        cols = 4
        for i, char in enumerate(entries):
            row = i // cols
            col = i % cols
            ttk.Label(
                frame,
                text=f"{char} {CHAR_TO_MORSE[char]}",
                font=("Courier", 9),
                width=8,
                anchor="w",
            ).grid(row=row, column=col, padx=4, pady=0, sticky="w")

    def _toggle_cheatsheet(self):
        pass  # no longer used — sheet is always visible

    # -------------------------
    # SETTINGS TAB
    # -------------------------

    def _build_settings_tab(self, parent):
        audio_frame = ttk.LabelFrame(parent, text="Audio", padding=8)
        audio_frame.pack(anchor="nw", padx=10, pady=10)

        self._add_float_row(
            audio_frame, 0, "Volume", 0.0, 1.0, self.config.sidetone_volume,
            lambda v: setattr(self.config, "sidetone_volume", v),
        )
        self._add_int_row(
            audio_frame, 1, "Sidetone (Hz)", 200, 1200, self.config.sidetone_hz,
            lambda v: setattr(self.config, "sidetone_hz", v),
        )

        keyer_frame = ttk.LabelFrame(parent, text="Keyer", padding=8)
        keyer_frame.pack(anchor="nw", padx=10, pady=(0, 10))

        ttk.Label(keyer_frame, text="Input Mode").grid(
            row=0, column=0, sticky="w", pady=4, padx=(0, 8)
        )
        self._input_mode_var = tk.StringVar(value=self.config.input_mode.name)
        cb_input = ttk.Combobox(
            keyer_frame, textvariable=self._input_mode_var,
            values=[m.name for m in InputMode], state="readonly", width=18,
        )
        cb_input.grid(row=0, column=1, sticky="w")
        cb_input.bind(
            "<<ComboboxSelected>>",
            lambda _: setattr(
                self.config, "input_mode", InputMode[self._input_mode_var.get()]
            ),
        )

        ttk.Label(keyer_frame, text="Paddle Layout").grid(
            row=1, column=0, sticky="w", pady=4, padx=(0, 8)
        )
        self._paddle_layout_var = tk.StringVar(value=self.config.paddle_layout.name)
        cb_layout = ttk.Combobox(
            keyer_frame, textvariable=self._paddle_layout_var,
            values=[m.name for m in PaddleLayout], state="readonly", width=18,
        )
        cb_layout.grid(row=1, column=1, sticky="w")
        cb_layout.bind(
            "<<ComboboxSelected>>",
            lambda _: setattr(
                self.config, "paddle_layout",
                PaddleLayout[self._paddle_layout_var.get()]
            ),
        )

        keys_frame = ttk.LabelFrame(parent, text="Key Bindings", padding=8)
        keys_frame.pack(anchor="nw", padx=10, pady=(0, 10))

        self._key_labels = {}
        bindings = [
            ("Left Paddle",  "left_paddle_key"),
            ("Right Paddle", "right_paddle_key"),
            ("Straight Key", "straight_key"),
        ]
        for row, (label, attr) in enumerate(bindings):
            ttk.Label(keys_frame, text=label, width=14, anchor="w").grid(
                row=row, column=0, sticky="w", pady=4, padx=(0, 8)
            )
            lbl = ttk.Label(
                keys_frame,
                text=self._vk_name(getattr(self.config, attr)),
                width=16, anchor="w", foreground=_ACCENT,
            )
            lbl.grid(row=row, column=1, sticky="w", padx=(0, 8))
            self._key_labels[attr] = lbl

            btn = ttk.Button(
                keys_frame, text="Capture",
                command=lambda a=attr, b=lbl: self._start_capture(a, b),
            )
            btn.grid(row=row, column=2, sticky="w")
            self._key_labels[attr + "_btn"] = btn

        vis_frame = ttk.LabelFrame(parent, text="Visualizer", padding=8)
        vis_frame.pack(anchor="nw", padx=10, pady=(0, 10))

        ttk.Label(vis_frame, text="Carrier Colour", width=14, anchor="w").grid(
            row=0, column=0, sticky="w", padx=(0, 8)
        )
        self._carrier_swatch = tk.Label(
            vis_frame, width=4,
            bg=self.config.carrier_color, relief="flat",
        )
        self._carrier_swatch.grid(row=0, column=1, sticky="w", padx=(0, 8))
        ttk.Button(
            vis_frame, text="Choose…",
            command=self._pick_carrier_color,
        ).grid(row=0, column=2, sticky="w")

    def _pick_carrier_color(self):
        from tkinter import colorchooser
        result = colorchooser.askcolor(
            color=self.config.carrier_color,
            title="Carrier Colour",
            parent=self.root,
        )
        if result and result[1]:
            color = result[1]
            self.config.carrier_color = color
            self._visualizer._color_on = color
            self._carrier_swatch.config(bg=color)

    def _start_capture(self, attr: str, label: ttk.Label):
        label.config(text="Press a key…", foreground=_MUTED)

        def _captured(vk: int):
            setattr(self.config, attr, vk)
            self._keyboard.reload_keys()
            label.config(text=self._vk_name(vk), foreground=_ACCENT)

        self._keyboard.capture_callback = _captured

    @staticmethod
    def _vk_name(vk: int) -> str:
        """Human-readable label for a VK code."""
        names = {
            32:  "Space",
            8:   "Backspace",
            9:   "Tab",
            13:  "Enter",
            27:  "Escape",
            37:  "Left Arrow",
            38:  "Up Arrow",
            39:  "Right Arrow",
            40:  "Down Arrow",
            96:  "Numpad 0",
            97:  "Numpad 1",
            98:  "Numpad 2",
            99:  "Numpad 3",
            100: "Numpad 4",
            101: "Numpad 5",
            102: "Numpad 6",
            103: "Numpad 7",
            104: "Numpad 8",
            105: "Numpad 9",
        }
        if vk in names:
            return names[vk]
        if 65 <= vk <= 90:
            return chr(vk)          # A–Z
        if 48 <= vk <= 57:
            return chr(vk)          # 0–9
        return f"VK {vk}"

    # -------------------------
    # CONFIG SETTERS
    # -------------------------

    def _set_wpm(self, val: int):
        self.config.wpm = max(5, val)
        self.decoder._sync_config()
        self._update_timing_display()

    def _set_dah_weight(self, val: float):
        self.config.dah_weight = val
        self._update_timing_display()

    def _update_timing_display(self):
        dit_ms = int(self.config.dit_seconds * 1000)
        dah_ms = int(self.config.dah_seconds * 1000)
        self._dit_ms_var.set(f"{dit_ms} ms")
        self._dah_ms_var.set(f"{dah_ms} ms")

    def _set_timing(self, attr: str, val: float):
        setattr(self.config, attr, val)
        self.decoder._sync_config()

    # -------------------------
    # OUTPUT HELPERS
    # -------------------------

    def _clear_output(self):
        self.output.config(state="normal")
        self.output.delete("1.0", "end")
        self.output.config(state="disabled")

    def _poll_decoder(self):
        """
        Poll decoder output every 50 ms and append any new characters.
        Runs on the tkinter event loop via after().
        """
        events = self.decoder.get_events()
        if events:
            self.output.config(state="normal")
            for event in events:
                if event.event_type == EventType.CHARACTER_DECODED:
                    self.output.insert("end", event.character)
                elif event.event_type == EventType.WORD_BREAK:
                    self.output.insert("end", " ")
            self.output.see("end")
            self.output.config(state="disabled")

        self.root.after(50, self._poll_decoder)
