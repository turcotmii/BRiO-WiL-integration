"""Constants for the BRiO WiL integration."""

DOMAIN = "brio_wil"
DEFAULT_PORT = 30302
SCAN_INTERVAL_SECONDS = 60
# Pause after a command before re-reading state (same as the Node-RED flow).
SETTLE_DELAY = 1.0

# Mode id -> display name (taken from the original Node-RED flow).
MODES: dict[int, str] = {
    0: "Warm white",
    1: "White",
    2: "Blue",
    3: "Lagoon",
    4: "Cyan",
    5: "Purple",
    6: "Magenta",
    7: "Pink",
    8: "Red",
    9: "Orange",
    10: "Green",
    16: "Gradient",
    17: "Rainbow",
    18: "Parade",
    19: "Techno",
    20: "Horizon",
    21: "Hazard",
    22: "Magical",
}

SPEEDS: dict[int, str] = {0: "Slow", 1: "Medium", 2: "Fast"}

# Device brightness levels 0..3 (Low..Maximum) mapped onto HA's 1..255.
MAX_LEVEL = 3
