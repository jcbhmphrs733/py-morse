# config.py

from dataclasses import dataclass
from enum import Enum, auto


class InputMode(Enum):
    STRAIGHT_KEY = auto()
    IAMBIC = auto()


class PaddleLayout(Enum):
    LEFT_DIT_RIGHT_DAH = auto()
    LEFT_DAH_RIGHT_DIT = auto()


@dataclass(slots=True)
class Config:
    """
    Application configuration.

    All timing values are derived from WPM.
    """

    # Morse settings
    wpm: int = 15

    # Audio settings
    sidetone_hz: int = 700
    sidetone_volume: float = 1.0
    sample_rate: int = 44100

    # Visualizer
    carrier_color: str = "#3a7ebf"

    # Keyer settings
    input_mode: InputMode = InputMode.IAMBIC
    paddle_layout: PaddleLayout = PaddleLayout.LEFT_DIT_RIGHT_DAH

    # Keyboard mappings (VK codes)
    left_paddle_key:  int = 96
    right_paddle_key: int = 101
    straight_key:     int = 32

    # Decoder gap tolerances (multiplier of one dit duration)
    # Standard Morse is 3× and 7×; larger values give more time between letters/words
    char_gap_multiplier: float = 5.0
    word_gap_multiplier: float = 12.0

    # Dah weight: ratio of dah to dit length (standard = 3.0)
    dah_weight: float = 3.0

    @property
    def dit_seconds(self) -> float:
        """
        Standard PARIS timing.

        dit duration = 1200 / WPM milliseconds
        """
        return 1.2 / self.wpm

    @property
    def dah_seconds(self) -> float:
        """A dah is dah_weight dits."""
        return self.dit_seconds * self.dah_weight

    @property
    def intra_element_gap_seconds(self) -> float:
        """Gap between elements within a character."""
        return self.dit_seconds

    @property
    def character_gap_seconds(self) -> float:
        """
        Total character gap.

        Character spacing is 3 units.
        Since an element already ends with 1 unit of silence,
        the decoder typically waits for 3 total units.
        """
        return self.dit_seconds * 3

    @property
    def word_gap_seconds(self) -> float:
        """Word spacing is 7 units."""
        return self.dit_seconds * 7


# Default application configuration
DEFAULT_CONFIG = Config()