# main.py

import threading
import time
from queue import Queue

from config import DEFAULT_CONFIG
from keyboard_input import KeyboardInput
from keyer import Keyer
from decoder import Decoder
from audio import AudioEngine
from events import EventType


def run_decoder(decoder: Decoder, event_queue: Queue):
    """
    Decoder loop:
    consumes ELEMENT timing events and produces characters.
    """
    while True:
        decoder.push(event_queue.get())


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


def run_display(decoder: Decoder):
    """
    Simple terminal display loop.
    Shows decoded characters as they arrive.
    """
    last_output_len = 0

    while True:
        events = decoder.get_events()

        for event in events:
            if event.event_type == EventType.CHARACTER_DECODED:
                print(event.character, end="", flush=True)

            elif event.event_type == EventType.WORD_BREAK:
                print(" ", end="", flush=True)

        time.sleep(0.01)


def main():
    config = DEFAULT_CONFIG

    # Shared event queues
    q1 = Queue()  # keyboard → keyer
    q2 = Queue()  # keyer → audio + decoder

    # Components
    keyboard = KeyboardInput(q1, config)
    keyer = Keyer(q1, config)

    decoder = Decoder(config)
    audio = AudioEngine(q1, config)

    # Start audio stream
    audio.start()

    # Threads
    threads = [
        threading.Thread(target=run_keyboard, args=(keyboard,), daemon=True),
        threading.Thread(target=run_keyer, args=(keyer,), daemon=True),
        threading.Thread(target=run_audio, args=(audio,), daemon=True),
        threading.Thread(target=run_decoder, args=(decoder, q1), daemon=True),
        threading.Thread(target=run_display, args=(decoder,), daemon=True),
    ]

    for t in threads:
        t.start()

    print("Morse Trainer running... Press Ctrl+C to exit.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()    