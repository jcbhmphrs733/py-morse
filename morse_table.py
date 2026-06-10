# morse_table.py

"""
International Morse Code lookup tables.

MVP supports:
    A-Z
    0-9

Anything else should decode to '?'.
"""

MORSE_TO_CHAR = {
    # Letters
    ".-": "A",
    "-...": "B",
    "-.-.": "C",
    "-..": "D",
    ".": "E",
    "..-.": "F",
    "--.": "G",
    "....": "H",
    "..": "I",
    ".---": "J",
    "-.-": "K",
    ".-..": "L",
    "--": "M",
    "-.": "N",
    "---": "O",
    ".--.": "P",
    "--.-": "Q",
    ".-.": "R",
    "...": "S",
    "-": "T",
    "..-": "U",
    "...-": "V",
    ".--": "W",
    "-..-": "X",
    "-.--": "Y",
    "--..": "Z",

    # Numbers
    "-----": "0",
    ".----": "1",
    "..---": "2",
    "...--": "3",
    "....-": "4",
    ".....": "5",
    "-....": "6",
    "--...": "7",
    "---..": "8",
    "----.": "9",
}

CHAR_TO_MORSE = {
    char: morse
    for morse, char in MORSE_TO_CHAR.items()
}


def decode(sequence: str) -> str:
    """
    Convert Morse symbols to a character.

    Example:
        '.-' -> 'A'
        '--..' -> 'Z'

    Returns '?' for unknown sequences.
    """
    return MORSE_TO_CHAR.get(sequence, "?")


def encode(character: str) -> str:
    """
    Convert a character to Morse.

    Example:
        'A' -> '.-'
        'Z' -> '--..'

    Returns an empty string for unsupported characters.
    """
    return CHAR_TO_MORSE.get(character.upper(), "")