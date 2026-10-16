"""
games.py — Game catalog and profile manager
═════════════════════════════════════════════════════════════════════
Profiles, URLs, control mappings, dynamic custom game creation,
and hand gesture blueprints.
"""

from typing import List, Dict, Any
from config import get_setting, set_setting

DEFAULT_GAME_CATALOG: List[Dict[str, Any]] = [
    {
        "id":          "hill_climb",
        "name":        "🏎  Racing Limits",
        "genre":       "HIGHWAY RACING",
        "mode":        "racing",
        "difficulty":  "🟢 Easy",
        "url":         "https://www.crazygames.com/game/racing-limits",
        "icon":        "🏎",
        "description": "Race through highway traffic in a desktop-browser driving game on CrazyGames.",
        "keys_summary": "← / → = Balance/Tilt | ↑ = Gas | ↓ = Brake",
        "gestures": [
            ("👈 Hand Left",   "Tilt Backwards", "← (Left Arrow)"),
            ("👉 Hand Right",  "Tilt Forwards",  "→ (Right Arrow)"),
            ("👍 Thumb / Palm", "Accelerate Gas", "↑ (Up Arrow)"),
            ("✊ Fist / Down",  "Brake / Reverse", "↓ (Down Arrow)"),
            ("☝️ Point Trigger", "Instant Boost", "SPACE / Nitro"),
        ]
    },
    {
        "id":          "moto_x3m",
        "name":        "🏍  MX Offroad Master",
        "genre":       "OFFROAD RACING",
        "mode":        "racing",
        "difficulty":  "🟡 Medium",
        "url":         "https://www.crazygames.com/game/mx-offroad-master",
        "icon":        "🏍",
        "description": "Ride technical offroad courses in a desktop-browser motocross game on CrazyGames.",
        "keys_summary": "← / → = Mid-Air Rotation | ↑ = Full Throttle | ↓ = Brake",
        "gestures": [
            ("👈 Hand Left",   "Backflip / Tilt Left",  "← (Left Arrow)"),
            ("👉 Hand Right",  "Frontflip / Tilt Right", "→ (Right Arrow)"),
            ("👍 Thumb / Palm", "Gas Throttle",          "↑ (Up Arrow)"),
            ("✊ Closed Fist",  "Precision Brake",       "↓ (Down Arrow)"),
            ("✌️ Peace Sign",  "Quick Reset",           "R"),
        ]
    },
    {
        "id":          "temple_run_2",
        "name":        "🌃  Night City Racing",
        "genre":       "CITY RACING",
        "mode":        "racing",
        "difficulty":  "🔴 Pro Reflex",
        "url":         "https://www.crazygames.com/game/night-city-racing",
        "icon":        "🌃",
        "description": "Race through a neon city in a desktop-browser driving game on CrazyGames.",
        "keys_summary": "← / → = Turn 90° | Swipe/↑ = Jump | Swipe/↓ = Slide",
        "gestures": [
            ("👈 Swipe/Tilt Left",  "Turn 90° Left",       "← (Left Arrow)"),
            ("👉 Swipe/Tilt Right", "Turn 90° Right",      "→ (Right Arrow)"),
            ("🖐 Open Palm / Swipe ↑", "Super Jump",       "↑ (Up Arrow) / SPACE"),
            ("✊ Fist / Swipe ↓",     "Power Slide",        "↓ (Down Arrow)"),
            ("☝️ Point Trigger",       "Shield / Special",  "SPACE"),
        ]
    },
    {
        "id":          "subway_surfers",
        "name":        "🚙  Rally Racer Dirt",
        "genre":       "RALLY RACING",
        "mode":        "racing",
        "difficulty":  "🟡 Medium",
        "url":         "https://www.crazygames.com/game/rally-racer-dirt",
        "icon":        "🚙",
        "description": "Drift across asphalt and dirt stages in a desktop-browser rally game on CrazyGames.",
        "keys_summary": "← / → = Switch Lanes | ↑ = Jump | ↓ = Roll/Slide",
        "gestures": [
            ("👈 Hand Left",   "Dodge Lane Left",   "← (Left Arrow)"),
            ("👉 Hand Right",  "Dodge Lane Right",  "→ (Right Arrow)"),
            ("🖐 Open Palm",    "Jump Over Barriers", "↑ (Up Arrow)"),
            ("✊ Closed Fist",  "Roll Under Obstacles", "↓ (Down Arrow)"),
            ("✌️ Peace ✌️",     "Activate Hoverboard", "SPACE"),
        ]
    },
    {
        "id":          "drift_boss",
        "name":        "🏁  Crazy Grand Prix",
        "genre":       "FORMULA RACING",
        "mode":        "racing",
        "difficulty":  "🟡 Medium",
        "url":         "https://www.crazygames.com/game/crazy-grand-prix",
        "icon":        "🚗",
        "description": "Compete in formula-style circuit races in a desktop browser on CrazyGames.",
        "keys_summary": "→ / Space = Drift Right | Release = Drift Left",
        "gestures": [
            ("👉 Hand Right / Palm", "Drift Right", "→ (Right Arrow) / SPACE"),
            ("👈 Hand Left / Fist",  "Straight / Left", "Release Right"),
            ("☝️ Point Trigger",     "Boost Nitro",  "SPACE"),
        ]
    },
    {
        "id":          "road_fury",
        "name":        "🏎  Super Star Car",
        "genre":       "FORMULA RACING",
        "mode":        "racing",
        "difficulty":  "🔴 Pro Reflex",
        "url":         "https://www.crazygames.com/game/super-star-car",
        "icon":        "🚦",
        "description": "Drive a formula racing career in a desktop browser on CrazyGames.",
        "keys_summary": "← / → = Steer & Aim | Auto-Fire | ↑ = Turbo Boost",
        "gestures": [
            ("👈 Hand Left",   "Steer Left & Aim",  "← (Left Arrow)"),
            ("👉 Hand Right",  "Steer Right & Aim", "→ (Right Arrow)"),
            ("☝️ Point Trigger", "Laser Cannon",     "SPACE / Left Click"),
            ("👍 Thumb Up",     "Turbo Accelerator", "↑ (Up Arrow)"),
            ("✊ Fist / Brake",  "Slow Down Shield",  "↓ (Down Arrow)"),
        ]
    },
    {
        "id":          "car_rush",
        "name":        "🏁  Circuit Racing",
        "genre":       "CIRCUIT RACING",
        "mode":        "racing",
        "difficulty":  "🟢 Easy",
        "url":         "https://www.crazygames.com/game/circuit-racing",
        "icon":        "🏎",
        "description": "Race around paved circuits in a desktop browser on CrazyGames.",
        "keys_summary": "← / → = Steer | ↑ = Accelerate | ↓ = Brake",
        "gestures": [
            ("👈 Hand Left",   "Steer Left",   "← (Left Arrow)"),
            ("👉 Hand Right",  "Steer Right",  "→ (Right Arrow)"),
            ("👍 Thumb / Palm", "Gas Accelerate", "↑ (Up Arrow)"),
            ("✊ Closed Fist",  "Brake / Decel", "↓ (Down Arrow)"),
        ]
    },
    {
        "id":          "burnout_drift",
        "name":        "🚘  Mr. Racer",
        "genre":       "CAR RACING",
        "mode":        "racing",
        "difficulty":  "🔴 Pro Reflex",
        "url":         "https://www.crazygames.com/game/mr-racer---car-racing",
        "icon":        "🚘",
        "description": "Race and overtake traffic in a desktop-browser car game on CrazyGames.",
        "keys_summary": "← / → = Counter-Steer | ↑ = Throttle | ↓ = Foot Brake | Space = Handbrake",
        "gestures": [
            ("👈 Hand Left",   "Counter-Steer Left",  "← (Left Arrow)"),
            ("👉 Hand Right",  "Counter-Steer Right", "→ (Right Arrow)"),
            ("👍 Thumb / Palm", "Full Gas",           "↑ (Up Arrow)"),
            ("✊ Closed Fist",  "Emergency Handbrake", "SPACE"),
            ("👎 Thumb Down",   "Reverse / Brake",     "↓ (Down Arrow)"),
        ]
    },
]

# Browser process search titles for automatic OS window focusing
BROWSER_TITLES = [
    "Chrome", "Firefox", "Edge", "Opera", "Brave", "Vivaldi",
    "Google Chrome", "Mozilla Firefox", "Microsoft Edge",
]

def get_all_games() -> List[Dict[str, Any]]:
    """Returns combined list of default catalog and persistent user custom games."""
    custom = get_setting("custom_games", [])
    return DEFAULT_GAME_CATALOG + custom

def add_custom_game(game_dict: Dict[str, Any]) -> None:
    """Adds a new user game and persists it to settings.json."""
    custom = get_setting("custom_games", [])
    custom.append(game_dict)
    set_setting("custom_games", custom)

def remove_custom_game(game_id: str) -> None:
    """Removes a custom user game from settings.json."""
    custom = get_setting("custom_games", [])
    filtered = [g for g in custom if g.get("id") != game_id]
    set_setting("custom_games", filtered)

GAME_CATALOG = get_all_games()
