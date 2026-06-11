# main.py

import threading
import time
from queue import Queue
import tkinter as tk

from config import DEFAULT_CONFIG
from config_io import load_config, save_config
from keyboard_input import KeyboardInput
from keyer import Keyer
from decoder import Decoder
from audio import AudioEngine
from gui import MorseGUI


def run_dispatcher(source: Queue, targets: list[Queue]):
    """
    Fan-out dispatcher: copies every keyer event to all consumers.
    Prevents AudioEngine and Decoder from racing on the same queue.
    """
    while True:
        event = source.get()
        for q in targets:
            q.put(event)


def run_decoder(decoder: Decoder, event_queue: Queue):
    """
    Decoder loop:
    consumes ELEMENT timing events and produces characters.
    Uses a short timeout so gap detection can fire between events.
    """
    from queue import Empty
    while True:
        try:
            event = event_queue.get(timeout=0.05)
            decoder.push(event)
        except Empty:
            decoder.check_gaps()


def run_keyer(keyer: Keyer):
    """
    Keyer loop:
    runs state machine continuously.
    """
    while True:
        keyer.process()
        time.sleep(0.001)  # small yield to prevent CPU spin


def run_audio(audio: AudioEngine):
    """
    Audio loop:
    processes ELEMENT_START / END events.
    """
    while True:
        audio.process()
        time.sleep(0.001)


def run_keyboard(keyboard: KeyboardInput):
    """
    Keyboard listener runs in its own thread.
    """
    keyboard.start()
    while True:
        time.sleep(1)


def main():
    config = load_config()

    # Shared event queues
    q1 = Queue()  # keyboard → keyer
    q2 = Queue()  # keyer → dispatcher
    q_audio = Queue()   # dispatcher → audio
    q_decoder = Queue() # dispatcher → decoder

    # Components
    keyboard = KeyboardInput(q1, config)
    keyer = Keyer(q1, q2, config)

    decoder = Decoder(config)
    audio = AudioEngine(q_audio, config)

    # Start audio stream
    audio.start()

    # Threads
    threads = [
        threading.Thread(target=run_keyboard, args=(keyboard,), daemon=True),
        threading.Thread(target=run_keyer, args=(keyer,), daemon=True),
        threading.Thread(target=run_dispatcher, args=(q2, [q_audio, q_decoder]), daemon=True),
        threading.Thread(target=run_audio, args=(audio,), daemon=True),
        threading.Thread(target=run_decoder, args=(decoder, q_decoder), daemon=True),
    ]

    for t in threads:
        t.start()

    root = tk.Tk()
    MorseGUI(root, config, decoder, audio, keyboard)

    def _on_close():
        save_config(config)
        audio.stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)
    root.mainloop()


if __name__ == "__main__":
    main()    