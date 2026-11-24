import json
import os
import sys
import time
from datetime import datetime
import requests
from colorama import Fore, Style, init

# Configure streams for Windows consoles and silent pythonw background execution
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "badge_rotator.log")

if sys.stdout is None:
    sys.stdout = open(LOG_FILE_PATH, "a", encoding="utf-8", buffering=1)
if sys.stderr is None:
    sys.stderr = open(LOG_FILE_PATH, "a", encoding="utf-8", buffering=1)

if sys.platform.startswith("win"):
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

init(autoreset=True)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
DISCORD_API_BASE = "https://discord.com/api/v9"

# Standard base badges unlocked on every server with Clan Tags
# NOTE: Toadstool / Mushroom (Badge #3) is EXCLUDED per user request!
BASE_BADGES = [
    (7, "💖 Heart"),
    (0, "🗡️ Sword"),
    (6, "🍃 Leaf"),
    (8, "🔥 Flame"),
    (1, "💧 Water Drop"),
    (2, "💀 Skull"),
    (4, "🌙 Crescent Moon"),
    (5, "⚡ Lightning"),
    (9, "🧭 Compass"),
]

# Boost packs unlocked with Server Boosts
# NOTE: Trophy/Cup (#28), Money Bag/Pot (#29), and Dollar Sign (#30) are EXCLUDED per user request!
PACK_BADGES = {
    "GUILD_TAGS_BADGE_PACK_PETS": [
        (21, "🐰 Bunny"),
        (22, "🐶 Dog"),
        (23, "🐸 Frog"),
        (24, "🐐 Goat"),
        (25, "🐱 Cat"),
    ],
    "GUILD_TAGS_BADGE_PACK_FLEX": [
        (26, "💎 Diamond"),
        (27, "👑 Crown"),
        # (28, "Trophy / Cup") EXCLUDED per user request!
        # (29, "Money Bag / Pot") EXCLUDED per user request!
        # (30, "Dollar Sign") EXCLUDED per user request!
    ],
    "GUILD_TAGS_BADGE_PACK_PLANT": [
        (31, "🍀 Clover"),
        (32, "🌸 Blossom"),
        (33, "🪴 Potted Plant"),
        (34, "🍁 Maple"),
        (35, "🥀 Wilted Flower"),
    ],
    "GUILD_TAGS_BADGE_PACK_CREEPY_CRAWLIES": [
        (36, "🦋 Butterfly"),
        (37, "🐌 Snail"),
        (38, "🐛 Caterpillar"),
        (39, "🕷️ Spider"),
        (40, "🐝 Bee"),
    ],
}

# The 14 official Discord color palette presets (Matching the 14 tiles in Discord settings)
DISCORD_COLOR_PALETTE = [
    ("#ff1c90", "#ff7fc0", "1/14 Pastel Pink"),
    ("#ff8f1c", "#ffae77", "2/14 Sunset Orange"),
    ("#eebe1a", "#fffc7f", "3/14 Golden Yellow"),
    ("#32a070", "#57b59e", "4/14 Mint Green"),
    ("#32839a", "#71c2d9", "5/14 Sky Blue"),
    ("#8a43ff", "#bd95ff", "6/14 Royal Purple"),
    ("#9b3fe5", "#cc8dff", "7/14 Vivid Violet"),
    ("#942e8f", "#d46cb5", "8/14 Orchid Purple"),
    ("#d14242", "#ff8989", "9/14 Crimson Red"),
    ("#814300", "#a88a6c", "10/14 Warm Brown"),
    ("#717224", "#c3c3c3", "11/14 Olive Green"),
    ("#5d1d47", "#c58fbb", "12/14 Burgundy Rose"),
    ("#222222", "#cccccc", "13/14 Silver Grey"),
    ("#ffffff", "#dcdde1", "14/14 Pure Frost White"),
]


def get_guild_boost_badges(token: str, guild_id: str):
    headers = {
        "Authorization": token,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
    boost_count = 0
    tier = 0
    features = []

    try:
        r_g = requests.get(f"{DISCORD_API_BASE}/guilds/{guild_id}", headers=headers, timeout=8)
        if r_g.status_code == 200:
            d = r_g.json()
            boost_count = d.get("premium_subscription_count", 0)
            tier = d.get("premium_tier", 0)
            features = d.get("features", [])
    except Exception:
        pass

    try:
        r_p = requests.get(f"{DISCORD_API_BASE}/guilds/{guild_id}/profile", headers=headers, timeout=8)
        if r_p.status_code == 200:
            d_p = r_p.json()
            if not boost_count:
                boost_count = d_p.get("premium_subscription_count", 0)
            if not tier:
                tier = d_p.get("premium_tier", 0)
            for f in d_p.get("features", []):
                if f not in features:
                    features.append(f)
    except Exception:
        pass

    badges_to_rotate = list(BASE_BADGES)
    unlocked_packs = []

    for pack_feat, pack_badges in PACK_BADGES.items():
        if pack_feat in features:
            pack_name = pack_feat.replace("GUILD_TAGS_BADGE_PACK_", "").title().replace("_", " ")
            unlocked_packs.append(pack_name)
            for b in pack_badges:
                if b not in badges_to_rotate:
                    badges_to_rotate.append(b)

    return boost_count, tier, unlocked_packs, badges_to_rotate


def log(level: str, message: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    if level == "INFO":
        tag = f"{Fore.CYAN}[INFO]{Style.RESET_ALL}"
    elif level == "SUCCESS":
        tag = f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL}"
    elif level == "WARN":
        tag = f"{Fore.YELLOW}[WARN]{Style.RESET_ALL}"
    elif level == "ERROR":
        tag = f"{Fore.RED}[ERROR]{Style.RESET_ALL}"
    else:
        tag = f"[{level}]"
    print(f"[{timestamp}] {tag} {message}")


def update_server_badge(token: str, guild_id: str, guild_name: str, badge_id: int, badge_name: str = "", primary_color: str = None, secondary_color: str = None, color_name: str = ""):
    url = f"{DISCORD_API_BASE}/guilds/{guild_id}/profile"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
    payload = {"badge": badge_id}
    if primary_color:
        payload["badge_color_primary"] = primary_color
    if secondary_color:
        payload["badge_color_secondary"] = secondary_color

    try:
        res = requests.patch(url, headers=headers, json=payload, timeout=10)
        if res.status_code == 200:
            badge_str = f"{badge_name} (#{badge_id})" if badge_name else f"Badge #{badge_id}"
            color_str = f" {Fore.CYAN}[Color: {color_name} ({primary_color})]{Style.RESET_ALL}" if primary_color else ""
            log("SUCCESS", f"[{guild_name}] Badge updated: {Fore.GREEN}{badge_str}{Style.RESET_ALL}{color_str} (Applied for ALL members!)")
            return "SUCCESS", None
        elif res.status_code == 403:
            log("ERROR", f"403 Forbidden on '{guild_name}'. You need 'Manage Server' or 'Administrator' permissions.")
            return "PERMISSION_DENIED", None
        elif res.status_code == 404:
            log("ERROR", f"404 Unknown Guild for ID: {guild_id}. Ensure you are in this server.")
            return "NOT_FOUND", None
        elif res.status_code == 429:
            data = {}
            try:
                data = res.json()
            except Exception:
                pass
            msg = data.get("message", "")
            code = data.get("code")
            
            raw_retry = data.get("retry_after") or res.headers.get("Retry-After")
            try:
                discord_remaining = float(raw_retry)
            except (TypeError, ValueError):
                discord_remaining = None

            if code == 690003 or "Too many server tag updates" in msg:
                log("WARN", f"Discord cooldown on '{guild_name}': 'Too many server tag updates'.")
                if discord_remaining:
                    mins, secs = divmod(int(discord_remaining), 60)
                    log("INFO", f"Discord lock active (~{mins}m {secs}s remaining). Will retry this color every 1 minute until applied...")
                else:
                    log("INFO", "Discord server lock active. Will retry this color every 1 minute until applied...")
                return "COOLDOWN", 60
            
            retry_after = min(60, float(data.get("retry_after", 30)))
            log("WARN", f"Rate limited. Waiting {retry_after:.0f}s before retrying...")
            return "RATE_LIMIT", retry_after
        elif res.status_code == 400:
            if "GUILD_PROFILE_BADGE_INVALID" in res.text or "not a valid badge" in res.text:
                log("WARN", f"Badge '{badge_name}' (#{badge_id}) is not unlocked on '{guild_name}'. Automatically skipping!")
                return "BADGE_INVALID", None
            if "GUILD_PROFILE_GUILD_TAG_INVALID_GUILD" in res.text or "Server does not support tags" in res.text:
                log("ERROR", f"Server '{guild_name}' (ID: {guild_id}) does not support Server Tags / Clan Badges.")
                log("INFO", "Discord Clan Tags is an exclusive feature only available to servers selected by Discord.")
                return "TAGS_NOT_SUPPORTED", None
            log("ERROR", f"Failed with status 400: {res.text[:100]}")
            return "ERROR", None
    except Exception as e:
        log("ERROR", f"Network exception: {e}")
        return "ERROR", None


def countdown(seconds: int, text: str = "Next color change in"):
    is_interactive = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
    if not is_interactive:
        time.sleep(seconds)
        return

    for remaining in range(seconds, 0, -1):
        mins, secs = divmod(remaining, 60)
        time_str = f"{mins:02d}m {secs:02d}s" if mins > 0 else f"{secs:2d}s"
        sys.stdout.write(f"\r{Fore.LIGHTBLACK_EX}{text}: {Fore.CYAN}{time_str}{Fore.LIGHTBLACK_EX} (Ctrl+C to stop)...{Style.RESET_ALL} ")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r" + " " * 75 + "\r")
    sys.stdout.flush()


def find_admin_guilds(token: str):
    headers = {
        "Authorization": token,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
    url = f"{DISCORD_API_BASE}/users/@me/guilds"
    try:
        res = requests.get(url, headers=headers, timeout=12)
        if res.status_code != 200:
            return []
        
        admin_guilds = []
        for g in res.json():
            perms = int(g.get("permissions", 0))
            is_admin = bool(perms & (1 << 3))
            manage_guild = bool(perms & (1 << 5))
            is_owner = bool(g.get("owner", False))
            if is_admin or manage_guild or is_owner:
                admin_guilds.append({
                    "id": str(g.get("id")),
                    "name": g.get("name", "Unknown Server"),
                    "features": g.get("features", []),
                })
        return admin_guilds
    except Exception:
        return []


def main():
    print(f"""{Fore.CYAN}
+==========================================================+
|         UNIVERSAL DISCORD SERVER BADGE ROTATOR           |
|         Works on ANY Server Where You Have Admin!        |
+==========================================================+{Style.RESET_ALL}\n""")

    token = ""
    interval = 60
    configured_guild_id = ""

    config = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
                raw = config.get("token", "").strip() or config.get("admin_token", "").strip()
                token = raw.strip().strip('"').strip("'").strip()
                configured_guild_id = str(config.get("target_guild_id", "")).strip()
                interval = max(1, int(config.get("interval_seconds", 60)))
        except Exception:
            pass

    # Check Discord Token (Separate input if missing)
    if not token or token.startswith("PASTE_"):
        print(f"{Fore.CYAN}=== Discord Token Setup ==={Style.RESET_ALL}")
        token = input("Enter Discord Admin/User Token: ").strip().strip('"').strip("'")
        while not token:
            token = input(f"{Fore.YELLOW}Token cannot be empty. Enter Discord Token: {Style.RESET_ALL}").strip().strip('"').strip("'")

    while True:
        log("INFO", "Verifying Token with Discord...")
        try:
            user_res = requests.get(f"{DISCORD_API_BASE}/users/@me", headers={"Authorization": token}, timeout=10)
            if user_res.status_code == 200:
                username = user_res.json().get("username", "Unknown")
                log("SUCCESS", f"Authenticated as: {Fore.GREEN}{username}{Style.RESET_ALL}")
                config["token"] = token
                config["admin_token"] = token
                try:
                    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                        json.dump(config, f, indent=2)
                except Exception:
                    pass
                break
            elif user_res.status_code == 401:
                log("ERROR", "The Discord token in config.json is expired or invalid (401 Unauthorized)!")
                print(f"{Fore.YELLOW}[Why this happened]{Style.RESET_ALL}")
                print("1. Did you click 'Log Out' on Discord after copying? (Logging out destroys the token immediately).")
                print("2. The token expired over time.\n")
                new_token = input("Paste your fresh Discord Token here (or press Enter to exit): ").strip().strip('"').strip("'")
                if not new_token:
                    sys.exit(1)
                token = new_token
            else:
                log("ERROR", f"Failed to authenticate: {user_res.status_code}")
                sys.exit(1)
        except Exception as e:
            log("ERROR", f"Network error during verification: {e}")
            sys.exit(1)

    # Automatically scan for all servers where this token has Admin / Manage Server
    log("INFO", "Scanning for servers where you have Admin / Manage Server...")
    admin_guilds = find_admin_guilds(token)

    if not admin_guilds:
        log("ERROR", "No servers found where this account has 'Manage Server' or 'Administrator'!")
        print(f"{Fore.YELLOW}Tip: Ensure this account has the Administrator or Manage Server role in the target server.{Style.RESET_ALL}")
        sys.exit(1)

    # Check Server ID (Separate input: only Server ID is needed if Token is already saved)
    print(f"\n{Fore.CYAN}=== Target Server Setup ==={Style.RESET_ALL}")
    saved_valid = configured_guild_id and not configured_guild_id.startswith("PASTE_")

    if saved_valid:
        saved_name = next((g["name"] for g in admin_guilds if g["id"] == configured_guild_id), None)
        hint = f"{saved_name} [{configured_guild_id}]" if saved_name else configured_guild_id
        print(f"Configured Server: {Fore.GREEN}{hint}{Style.RESET_ALL}")
        user_gid = input(f"Enter Server ID (or press Enter to keep current): ").strip().strip('"').strip("'")
        if user_gid:
            configured_guild_id = user_gid
    else:
        tagged_guilds = [g for g in admin_guilds if any("TAG" in f or "CLAN" in f for f in g["features"])]
        display_guilds = tagged_guilds if tagged_guilds else admin_guilds

        print(f"Servers where you have Admin / Manage Server ({len(display_guilds)} found):")
        for idx, g in enumerate(display_guilds, 1):
            tag_flag = f" {Fore.GREEN}[CLAN TAG READY]{Style.RESET_ALL}" if any("TAG" in f or "CLAN" in f for f in g["features"]) else ""
            print(f"  {Fore.CYAN}{idx}.{Style.RESET_ALL} {Fore.WHITE}{g['name']}{Style.RESET_ALL} (ID: {Fore.YELLOW}{g['id']}{Style.RESET_ALL}){tag_flag}")

        user_gid = input(f"\nEnter Server ID (or choose 1-{len(display_guilds)}): ").strip().strip('"').strip("'")
        if user_gid.isdigit() and 1 <= int(user_gid) <= len(display_guilds):
            configured_guild_id = display_guilds[int(user_gid) - 1]["id"]
        elif user_gid:
            configured_guild_id = user_gid
        elif display_guilds:
            configured_guild_id = display_guilds[0]["id"]

    # Save Server ID choice to config.json automatically
    config["target_guild_id"] = configured_guild_id
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass

    target_guild = next((g for g in admin_guilds if g["id"] == configured_guild_id), None)
    if not target_guild:
        g_name = f"Server {configured_guild_id}"
        try:
            g_res = requests.get(f"{DISCORD_API_BASE}/guilds/{configured_guild_id}", headers={"Authorization": token}, timeout=5)
            if g_res.status_code == 200:
                g_name = g_res.json().get("name", g_name)
        except Exception:
            pass
        log("ERROR", f"Account '{username}' does not have 'Manage Server' permission in '{g_name}' (ID: {configured_guild_id})!")
        print(f"\n{Fore.YELLOW}[Why this happened]{Style.RESET_ALL}")
        print(f"Discord requires the {Fore.WHITE}'Manage Server'{Style.RESET_ALL} or {Fore.WHITE}'Administrator'{Style.RESET_ALL} permission to change the server's clan tag emoji/badge.")
        print(f"To fix this:")
        print(f" 1. Grant this account ({username}) the 'Manage Server' role in {g_name}.")
        print(f"    - OR -")
        print(f" 2. Paste the token of an account that HAS Manage Server into config.json under 'token' or 'admin_token'.\n")
        sys.exit(1)

    guild_id = target_guild["id"]
    guild_name = target_guild["name"]

    # Detect server boosts and unlocked badge packs
    log("INFO", f"Checking server boosts & badge packs for '{guild_name}'...")
    boost_count, tier, unlocked_packs, badges_to_rotate = get_guild_boost_badges(token, guild_id)

    log("SUCCESS", f"Target Server: {Fore.YELLOW}{guild_name}{Style.RESET_ALL} (ID: {guild_id})")
    log("INFO", f"Server Boosts: {Fore.GREEN}{boost_count} Boost(s){Style.RESET_ALL} (Level {tier})")
    if unlocked_packs:
        log("INFO", f"Unlocked Boost Packs: {Fore.GREEN}{', '.join(unlocked_packs)}{Style.RESET_ALL}")
    else:
        log("INFO", "Unlocked Boost Packs: Standard Base Badges")
    
    colors_to_rotate = list(DISCORD_COLOR_PALETTE)

    print(f"\n{Fore.CYAN}Rotating {len(badges_to_rotate)} badge(s) through ALL {len(colors_to_rotate)} colors (changing every 1 min):{Style.RESET_ALL}")
    for idx, (b_id, b_name) in enumerate(badges_to_rotate, 1):
        print(f"  {idx}. {b_name} (Badge #{b_id})")
    print(f"{Fore.MAGENTA}14 Color Sequence:{Style.RESET_ALL} {', '.join([c[2] for c in colors_to_rotate])}")
    print("-" * 60)

    try:
        while True:
            for badge_id, badge_name in list(badges_to_rotate):
                log("INFO", f"Now cycling 14 colors for badge: {Fore.YELLOW}{badge_name}{Style.RESET_ALL}")
                badge_skipped = False

                color_idx = 0
                while color_idx < len(colors_to_rotate):
                    primary_hex, secondary_hex, color_name = colors_to_rotate[color_idx]
                    result, wait_time = update_server_badge(token, guild_id, guild_name, badge_id, badge_name, primary_hex, secondary_hex, color_name)

                    if result == "SUCCESS":
                        color_idx += 1
                        countdown(interval, "Next color change in")
                    elif result == "COOLDOWN" or result == "RATE_LIMIT":
                        # Wait for Discord lock, then RETRY THE EXACT SAME COLOR (never skip!)
                        wait_seconds = int(wait_time or 60)
                        countdown(wait_seconds, "Discord server cooldown active. Retrying color in")
                    elif result == "BADGE_INVALID":
                        badges_to_rotate = [b for b in badges_to_rotate if b[0] != badge_id]
                        badge_skipped = True
                        break
                    elif result in ("PERMISSION_DENIED", "NOT_FOUND", "TAGS_NOT_SUPPORTED"):
                        sys.exit(1)
                    else:
                        countdown(10, "Network issue. Retrying color in")

                if badge_skipped:
                    continue

    except KeyboardInterrupt:
        print("\n")
        log("INFO", "Rotator stopped by user. Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
