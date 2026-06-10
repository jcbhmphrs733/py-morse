# events.py

from dataclasses import dataclass, field
from enum import Enum, auto
from time import perf_counter


class EventType(Enum):
    """All events used throughout the application."""

    # Input events
    DIT_DOWN = auto()
    DIT_UP = auto()

    DAH_DOWN = auto()
    DAH_UP = auto()

    STRAIGHT_KEY_DOWN = auto()
    STRAIGHT_KEY_UP = auto()

    # Keyer output events
    ELEMENT_START = auto()
    ELEMENT_END = auto()

    # Decoder events
    CHARACTER_DECODED = auto()
    WORD_BREAK = auto()


class ElementType(Enum):
    """Morse elements."""

    DIT = auto()
    DAH = auto()


@dataclass(slots=True)
class Event:
    """
    Generic event passed between application components.

    Examples:
        Event(EventType.DIT_DOWN)

        Event(
            EventType.ELEMENT_START,
            element=ElementType.DIT
        )

        Event(
            EventType.CHARACTER_DECODED,
            character="A"
        )
    """

    event_type: EventType

    # Automatically assigned when event is created
    timestamp: float = field(default_factory=perf_counter)

    element: ElementType | None = None
    character: str | None = None

    # Optional payload data
    element: ElementType | None = None
    character: str | None = None