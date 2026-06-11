# config_io.py

"""
Persistent config load/save using JSON.

Saves all user-facing settings to config.json next to this file.
sample_rate is excluded (system constant, not a preference).
The rolling decoder calibration is also excluded — it is always
re-derived from wpm at startup.
"""

import json
from pathlib import Path

from config import Config, InputMode, PaddleLayout

_CONFIG_PATH = Path(__file__).parent / "config.json"

_ENUM_FIELDS = {
    "input_mode":    (InputMode,    lambda v: v.name,  lambda s: InputMode[s]),
    "paddle_layout": (PaddleLayout, lambda v: v.name,  lambda s: PaddleLayout[s]),
}

_INT_FIELDS = {
    "wpm", "sidetone_hz",
    "left_paddle_key", "right_paddle_key", "straight_key",
}

_FLOAT_FIELDS = {
    "sidetone_volume", "char_gap_multiplier", "word_gap_multiplier", "dah_weight",
}

_STR_FIELDS = {
    "carrier_color",
}


def save_config(config: Config) -> None:
    data = {}

    for field in _INT_FIELDS:
        data[field] = int(getattr(config, field))

    for field in _FLOAT_FIELDS:
        data[field] = float(getattr(config, field))

    for field in _STR_FIELDS:
        data[field] = str(getattr(config, field))

    for field, (_, serialise, _) in _ENUM_FIELDS.items():
        data[field] = serialise(getattr(config, field))

    _CONFIG_PATH.write_text(json.dumps(data, indent=2))


def load_config() -> Config:
    config = Config()

    if not _CONFIG_PATH.exists():
        return config

    try:
        data = json.loads(_CONFIG_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return config

    for field in _INT_FIELDS:
        if field in data:
            try:
                setattr(config, field, int(data[field]))
            except (ValueError, TypeError):
                pass

    for field in _FLOAT_FIELDS:
        if field in data:
            try:
                setattr(config, field, float(data[field]))
            except (ValueError, TypeError):
                pass

    for field in _STR_FIELDS:
        if field in data:
            try:
                setattr(config, field, str(data[field]))
            except (ValueError, TypeError):
                pass

    for field, (_, _, deserialise) in _ENUM_FIELDS.items():
        if field in data:
            try:
                setattr(config, field, deserialise(data[field]))
            except (KeyError, TypeError):
                pass

    return config
