"""
ASOF capture reference

This file is for documentation and screenshot capture only.
It summarizes the current ASOF operating concept in one place.
"""


# Operating schedule
DAY_START = "04:00"
DAY_END = "19:00"


# Relay control mode
RELAY_MODE = "pulse"
AUTO_RELAY_ENABLED = True


def relay_turn_on():
    """Turn system power ON through relay control."""
    pass


def relay_turn_off():
    """Turn system power OFF through relay control."""
    pass


ASOF_SUMMARY = {
    "function": "Autonomous System ON/OFF Function",
    "schedule": "04:00~19:00 ON / other time OFF",
    "daily_on_hours": 15,
    "daily_off_hours": 9,
    "power_on_ratio_percent": 62.5,
    "power_off_ratio_percent": 37.5,
    "expected_idle_power_saving_percent": 37.5,
    "relay_mode": RELAY_MODE,
    "auto_relay_enabled": AUTO_RELAY_ENABLED,
}
