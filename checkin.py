#!/usr/bin/env python3
"""
HoYoLAB Easy Check-In & Helper Hub
Supports: Windows, macOS, Linux
Games: Honkai: Star Rail (HSR), Genshin Impact, and Zenless Zone Zero (ZZZ)
Zero external dependencies for core functionality.
"""

import sys
import os
import json
import time
import random
import shutil
import sqlite3
import platform
import argparse
import subprocess
import signal
import urllib.request

def handle_sigint(sig=None, frame=None):
    print("\n\n👋 Operasi dibatalkan oleh pengguna (Keluar). Sampai jumpa!\n")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_sigint)
import urllib.error
import urllib.parse
from datetime import datetime
from pathlib import Path

# --- Game Definitions ---
GAMES = {
    "genshin": {
        "name": "Genshin Impact",
        "emoji": "✨",
        "act_id": "e202102251931481",
        "info_url": "https://sg-hk4e-api.hoyolab.com/event/sol/info",
        "sign_url": "https://sg-hk4e-api.hoyolab.com/event/sol/sign",
        "home_url": "https://sg-hk4e-api.hoyolab.com/event/sol/home",
        "referer": "https://act.hoyolab.com/ys/event/signin-sea-v3/index.html?act_id=e202102251931481",
    },
    "starrail": {
        "name": "Honkai: Star Rail",
        "emoji": "🚂",
        "act_id": "e202303301540311",
        "info_url": "https://sg-public-api.hoyolab.com/event/luna/os/info",
        "sign_url": "https://sg-public-api.hoyolab.com/event/luna/os/sign",
        "home_url": "https://sg-public-api.hoyolab.com/event/luna/os/home",
        "referer": "https://act.hoyolab.com/bbs/event/signin/hkrpg/e202303301540311.html?act_id=e202303301540311",
    },
    "zzz": {
        "name": "Zenless Zone Zero",
        "emoji": "🎬",
        "act_id": "e202406031448091",
        "info_url": "https://sg-act-nap-api.hoyolab.com/event/luna/zzz/os/info",
        "sign_url": "https://sg-act-nap-api.hoyolab.com/event/luna/zzz/os/sign",
        "home_url": "https://sg-act-nap-api.hoyolab.com/event/luna/zzz/os/home",
        "referer": "https://act.hoyolab.com/bbs/event/signin/zzz/e202406031448091.html?act_id=e202406031448091",
    },
    "honkai3rd": {
        "name": "Honkai Impact 3rd",
        "emoji": "⚔️",
        "act_id": "e202110291205111",
        "info_url": "https://sg-public-api.hoyolab.com/event/mani/info",
        "sign_url": "https://sg-public-api.hoyolab.com/event/mani/sign",
        "home_url": "https://sg-public-api.hoyolab.com/event/mani/home",
        "referer": "https://act.hoyolab.com/bbs/event/signin-bh3/index.html?act_id=e202110291205111",
    },
    "themis": {
        "name": "Tears of Themis",
        "emoji": "⚖️",
        "act_id": "e202202281857121",
        "info_url": "https://sg-public-api.hoyolab.com/event/luna/os/info",
        "sign_url": "https://sg-public-api.hoyolab.com/event/luna/os/sign",
        "home_url": "https://sg-public-api.hoyolab.com/event/luna/os/home",
        "referer": "https://act.hoyolab.com/bbs/event/signin/nxx/index.html?act_id=e202202281857121",
    },
    "hoyolab": {
        "name": "HoYoLAB Community",
        "emoji": "💬",
        "act_id": "community",
        "info_url": "https://bbs-api-os.hoyolab.com/community/painter/wapi/task/attend",
        "sign_url": "https://bbs-api-os.hoyolab.com/community/painter/wapi/task/attend",
        "home_url": "https://www.hoyolab.com",
        "referer": "https://www.hoyolab.com/",
        "is_community": True,
    },
}

BASE_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://act.hoyolab.com",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "x-rpc-app_version": "2.34.1",
    "x-rpc-client_type": "4",
}

AWARDS_CACHE = {}
ENV_PATH = Path.home() / ".hoyolab-checkin" / ".env"
CONFIG_PATH = Path.home() / ".hoyolab-checkin" / "config.json"
OS_NAME = platform.system()  # 'Darwin', 'Windows', 'Linux'


def load_hoyo_config() -> dict:
    """Load configuration including enabled games."""
    default = {"enabled_games": ["genshin", "starrail", "zzz", "honkai3rd", "themis", "hoyolab"]}
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {**default, **data}
        except Exception:
            pass
    return default


def save_hoyo_config(data: dict):
    """Save configuration."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


APP_NAME = "hoyolab-checkin"
APP_VERSION = "1.2.0"
SCRIPT_PATH = Path(__file__).resolve()


def parse_semver(ver: str) -> tuple:
    parts = []
    for x in ver.lstrip("v").split("."):
        if x.isdigit():
            parts.append(int(x))
    return tuple(parts)


def run_with_progress(title: str, worker_fn, timeout: float = 5.0):
    """Executes worker_fn in a daemon thread while rendering an animated progress bar and spinner."""
    import threading
    res = {"done": False, "result": None, "error": None}

    def target():
        try:
            res["result"] = worker_fn()
        except Exception as e:
            res["error"] = e
        finally:
            res["done"] = True

    t = threading.Thread(target=target, daemon=True)
    t.start()

    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    start_t = time.time()
    i = 0

    while not res["done"] and (time.time() - start_t < timeout):
        elapsed = time.time() - start_t
        pct = min(int((elapsed / timeout) * 100), 99)
        filled = pct // 10
        bar = "█" * filled + "░" * (10 - filled)
        sys.stdout.write(f"\r[*] {title}... {frames[i % len(frames)]} [{bar}] {pct}% ({elapsed:.1f}s)")
        sys.stdout.flush()
        time.sleep(0.08)
        i += 1

    sys.stdout.write("\r" + " " * 80 + "\r")
    sys.stdout.flush()
    return res["result"], res["error"]


def check_for_updates(prompt_if_latest: bool = False):
    """
    Checks latest update from https://wsnsam.my.id/api/updates?app=hoyolab-checkin
    with fallback to raw.githubusercontent.com/sammmms/hoyolab-checkin/main/version.json.
    """
    primary_url = f"https://script.wsnsam.my.id/api/updates?app={APP_NAME}"
    fallback_url = "https://raw.githubusercontent.com/sammmms/hoyolab-checkin/main/version.json"

    def fetch_remote():
        for url in [primary_url, fallback_url]:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (AutoUpdater)"})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    if resp.status == 200:
                        return json.loads(resp.read().decode("utf-8"))
            except Exception:
                continue
        return None

    update_data, _ = run_with_progress("Checking for updates", fetch_remote, timeout=3.5)

    if not update_data or "version" not in update_data:
        print("[*] Checking for updates... [Skip / Offline]")
        time.sleep(0.2)
        return

    latest_ver = update_data["version"]
    if parse_semver(latest_ver) <= parse_semver(APP_VERSION):
        print(f"[*] Checking for updates... [Latest Version: v{APP_VERSION} ✓]")
        time.sleep(0.3)
        if prompt_if_latest:
            print(f"\n[✓] You are already on the latest version (v{APP_VERSION}).\n")
            input("Press Enter to continue...")
        return

    sys.stdout.write("\r" + " " * 80 + "\r")
    sys.stdout.flush()

    print("\n" + "=" * 62)
    print(f"🚀 UPDATE AVAILABLE! (v{APP_VERSION} ➔ v{latest_ver})")
    print(f"📅 Release: {update_data.get('release_date', 'New')}")
    print("=" * 62)
    print("📋 Changelog:")
    for change in update_data.get("changelog", []):
        print(f"  • {change}")
    print("=" * 62 + "\n")

    action = input(f"Install update v{latest_ver} now? [Y/n]: ").strip().lower()
    if action in ("", "y", "yes"):
        print(f"\n⬇️  Downloading update v{latest_ver}...")
        download_url = update_data.get("download_url")
        if not download_url:
            print("[!] Download URL not available.")
            return

        try:
            req = urllib.request.Request(download_url, headers={"User-Agent": "Mozilla/5.0 (AutoUpdater)"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                new_code = resp.read().decode("utf-8")

            # Update current script
            with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
                f.write(new_code)
            os.chmod(SCRIPT_PATH, 0o755)

            target_installed = Path.home() / ".hoyolab-checkin" / "checkin.py"
            if target_installed.exists() and target_installed != SCRIPT_PATH:
                with open(target_installed, "w", encoding="utf-8") as f:
                    f.write(new_code)
                os.chmod(target_installed, 0o755)

            print(f"✅ Successfully updated to v{latest_ver}!")
            print("🔄 Restarting application...")
            time.sleep(1)
            os.execv(sys.executable, [sys.executable, str(SCRIPT_PATH)] + sys.argv[1:])
        except Exception as e:
            print(f"[x] Failed to install update: {e}")
            input("Press Enter to continue...")
    else:
        print("[*] Update skipped.\n")


# ==============================================================================
# Configuration & Cookie Management
# ==============================================================================

def load_env_file(filepath: Path) -> dict:
    """Parse key=value pairs from .env without external libraries."""
    env = {}
    if not filepath.is_file():
        return env
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    env[key.strip()] = val.strip().strip("'\"")
    except Exception as e:
        print(f"[!] Warning reading {filepath}: {e}")
    return env


def save_cookie_to_env(cookie_string: str, config_path: Path = None):
    """Save cookie securely to .env file."""
    target_path = config_path or ENV_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    found = False

    if target_path.exists():
        with open(target_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("HOYO_COOKIE="):
                    lines.append(f'HOYO_COOKIE="{cookie_string}"\n')
                    found = True
                else:
                    lines.append(line)

    if not found:
        lines.append(f'HOYO_COOKIE="{cookie_string}"\n')

    with open(target_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    if OS_NAME != "Windows":
        os.chmod(target_path, 0o600)
    print(f"💾 Cookie saved to: {target_path}")


def get_cookies_from_env_or_config(config_path: Path = None) -> tuple:
    """Extract cookies from environment or config file."""
    cookies = []
    search_paths = [ENV_PATH, Path.home() / ".hoyolab" / "config.env", Path(".env")]
    if config_path:
        search_paths.insert(0, config_path)

    loaded_vars = {}
    for p in search_paths:
        if p.is_file():
            loaded_vars.update(load_env_file(p))
            break

    for k, v in os.environ.items():
        if k.startswith("HOYO_") or k in ("COOKIE", "COOKIES", "LTOKEN_V2", "LTUID_V2"):
            loaded_vars[k] = v

    if "HOYO_COOKIE" in loaded_vars and loaded_vars["HOYO_COOKIE"]:
        cookies.append(loaded_vars["HOYO_COOKIE"])
    elif "COOKIE" in loaded_vars and loaded_vars["COOKIE"]:
        cookies.append(loaded_vars["COOKIE"])

    if not cookies and "LTOKEN_V2" in loaded_vars and "LTUID_V2" in loaded_vars:
        token = loaded_vars["LTOKEN_V2"]
        uid = loaded_vars["LTUID_V2"]
        if token and uid:
            cookies.append(f"ltuid_v2={uid}; ltoken_v2={token};")

    for i in range(1, 10):
        key = f"HOYO_COOKIE_{i}"
        if key in loaded_vars and loaded_vars[key]:
            if loaded_vars[key] not in cookies:
                cookies.append(loaded_vars[key])

    return cookies, loaded_vars


# ==============================================================================
# Cross-Platform Browser Auto-Import (Zen, Firefox, Floorp)
# ==============================================================================

def find_browser_cookie_db():
    """Locate SQLite cookie databases from browsers across Windows, macOS, and Linux."""
    candidates = []
    home = Path.home()

    if OS_NAME == "Darwin":
        app_sup = home / "Library/Application Support"
        candidates.extend([
            ("Zen Browser", app_sup / "zen/Profiles"),
            ("Mozilla Firefox", app_sup / "Firefox/Profiles"),
            ("Floorp", app_sup / "Floorp/Profiles"),
        ])
    elif OS_NAME == "Windows":
        appdata = Path(os.environ.get("APPDATA", ""))
        candidates.extend([
            ("Zen Browser", appdata / "zen/Profiles"),
            ("Mozilla Firefox", appdata / "Mozilla/Firefox/Profiles"),
            ("Floorp", appdata / "Floorp/Profiles"),
        ])
    elif OS_NAME == "Linux":
        candidates.extend([
            ("Zen Browser", home / ".zen"),
            ("Mozilla Firefox", home / ".mozilla/firefox"),
            ("Floorp", home / ".floorp"),
        ])

    found = []
    for name, base_dir in candidates:
        if base_dir.exists():
            for db in base_dir.glob("*/cookies.sqlite"):
                found.append((name, db))
    return found


def auto_import_from_browser(save: bool = True) -> str:
    """Extract valid session cookies from user's active browser."""
    databases = find_browser_cookie_db()
    if not databases:
        return None

    for browser_name, db_path in databases:
        if not db_path.exists():
            continue

        tmp_path = Path.home() / f".hoyo_import_tmp_{os.getpid()}.sqlite"
        try:
            shutil.copy2(db_path, tmp_path)
            conn = sqlite3.connect(tmp_path)
            cur = conn.cursor()
            cur.execute("""
                SELECT name, value FROM moz_cookies 
                WHERE (host LIKE '%hoyolab.com' OR host LIKE '%hoyoverse.com')
                AND name IN ('ltoken_v2', 'ltuid_v2', 'account_id_v2', 'cookie_token_v2')
            """)
            cookies = dict(cur.fetchall())
            conn.close()

            ltoken = cookies.get("ltoken_v2")
            ltuid = cookies.get("ltuid_v2") or cookies.get("account_id_v2")

            if ltoken and ltuid:
                cookie_str = f"ltuid_v2={ltuid}; ltoken_v2={ltoken};"
                print(f"✨ Found active HoYoLAB session in {browser_name}!")
                print(f"   👤 Account ID: {ltuid}")
                if save:
                    save_cookie_to_env(cookie_str)
                return cookie_str
        except Exception:
            pass
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass
    return None


def interactive_browser_login():
    """Launch interactive browser window for logging in."""
    print("\n🌐 Launching interactive login window...")
    print("👉 Please log in to HoYoLAB in the window that appears.")
    print("👉 (Google, Apple, or Email + Password login are all supported).\n")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("📦 Installing Playwright automation engine...")
        cmd = [sys.executable, "-m", "pip", "install", "playwright"]
        if OS_NAME != "Windows":
            cmd.append("--break-system-packages")
        subprocess.run(cmd, check=True)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://act.hoyolab.com/ys/event/signin-sea-v3/index.html?act_id=e202102251931481")
        print("⏳ Waiting for you to log in...")

        captured_cookie = None
        start_time = time.time()
        while time.time() - start_time < 300:
            cookies = context.cookies(["https://act.hoyolab.com", "https://hoyolab.com", "https://hoyoverse.com"])
            cookie_dict = {c["name"]: c["value"] for c in cookies}

            ltoken = cookie_dict.get("ltoken_v2")
            ltuid = cookie_dict.get("ltuid_v2") or cookie_dict.get("account_id_v2")

            if ltoken and ltuid:
                captured_cookie = f"ltuid_v2={ltuid}; ltoken_v2={ltoken};"
                print(f"\n🎉 Login detected for Account ID: {ltuid}!")
                break
            time.sleep(2)

        browser.close()
        if captured_cookie:
            save_cookie_to_env(captured_cookie)
            return captured_cookie
        else:
            print("❌ Login timed out or cancelled.")
            return None


# ==============================================================================
# Cross-Platform Auto Check-In Scheduler (Windows / macOS / Linux)
# ==============================================================================

def get_scheduler_status():
    """Check if automatic daily check-in is scheduled on the current OS."""
    if OS_NAME == "Darwin":
        agents_dir = Path.home() / "Library/LaunchAgents"
        matched = list(agents_dir.glob("*hoyolab*.plist")) + list(agents_dir.glob("*genshin*.plist"))
        if matched:
            res = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
            if "hoyolab" in res.stdout or "genshin" in res.stdout:
                return True, "macOS LaunchAgent (Active)"
            return True, "macOS LaunchAgent (Loaded)"
        return False, "Not Configured"

    elif OS_NAME == "Windows":
        res = subprocess.run(["schtasks", "/Query", "/TN", "HoYoLAB_Daily_Checkin"], capture_output=True, text=True)
        if res.returncode == 0:
            return True, "Windows Task Scheduler (Active)"
        return False, "Not Configured"

    elif OS_NAME == "Linux":
        res = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        if "genshin-checkin" in res.stdout or "hoyolab-checkin" in res.stdout:
            return True, "Linux Crontab (Active)"
        return False, "Not Configured"

    return False, "Unsupported OS"


def wait_for_internet(timeout: int = 180, check_interval: int = 3, verbose: bool = False) -> bool:
    """
    Wait for active internet connectivity with DNS resolution.
    Essential on macOS wake-up because launchd fires before Wi-Fi reconnects.
    """
    import socket

    start_time = time.time()
    spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    step = 0

    while time.time() - start_time < timeout:
        elapsed = time.time() - start_time
        pct = min(int((elapsed / timeout) * 100), 99)
        bar = "█" * (pct // 10) + "░" * (10 - (pct // 10))
        if verbose:
            sys.stdout.write(f"\r[*] Waiting for active internet connection... {spinner[step % len(spinner)]} [{bar}] {elapsed:.1f}s/{timeout}s")
            sys.stdout.flush()
            step += 1

        try:
            s = socket.create_connection(("1.1.1.1", 53), timeout=2)
            s.close()
            req = urllib.request.Request("https://www.google.com", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status in (200, 204, 301, 302):
                    if verbose:
                        sys.stdout.write(f"\r{' ' * 75}\r[✓] Internet connection is active! ({elapsed:.1f}s)\n")
                        sys.stdout.flush()
                    return True
        except Exception:
            pass
        time.sleep(check_interval)

    if verbose:
        sys.stdout.write(f"\r{' ' * 75}\r[!] Failed to connect to internet after {timeout} seconds.\n")
        sys.stdout.flush()
    return False


def install_scheduler():
    """Install daily background check-in task at 08:00 AM with hourly catch-ups."""
    script_path = Path(__file__).resolve()
    python_bin = sys.executable

    if OS_NAME == "Darwin":
        plist_path = Path.home() / "Library/LaunchAgents/com.user.hoyolab-checkin.plist"
        plist_path.parent.mkdir(parents=True, exist_ok=True)
        log_path = Path.home() / ".hoyolab-checkin/checkin.log"

        # Build StartCalendarInterval array: 08:00 + hourly catch-ups until 23:00
        intervals = []
        for h in range(8, 24):
            intervals.append(f"""        <dict>
            <key>Hour</key>
            <integer>{h}</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>""")
        intervals_xml = "\n".join(intervals)

        content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.hoyolab-checkin</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_bin}</string>
        <string>{script_path}</string>
        <string>--silent</string>
    </array>
    <key>StartCalendarInterval</key>
    <array>
{intervals_xml}
    </array>
    <key>StandardOutPath</key>
    <string>{log_path}</string>
    <key>StandardErrorPath</key>
    <string>{log_path}</string>
</dict>
</plist>
"""
        with open(plist_path, "w", encoding="utf-8") as f:
            f.write(content)

        subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
        subprocess.run(["launchctl", "load", str(plist_path)], check=True)
        print("✅ Daily auto check-in registered at 08:00 AM via macOS LaunchAgent!")
        print("ℹ️ Catches up automatically whenever MacBook wakes up during the day.")
        return True

    elif OS_NAME == "Windows":
        cmd = [
            "schtasks", "/Create",
            "/SC", "DAILY",
            "/TN", "HoYoLAB_Daily_Checkin",
            "/TR", f'"{python_bin}" "{script_path}" --silent',
            "/ST", "08:00",
            "/F"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print("✅ Daily auto check-in registered at 08:00 AM in Windows Task Scheduler!")
            return True
        else:
            print(f"❌ Failed to create Windows task: {res.stderr}")
            return False

    elif OS_NAME == "Linux":
        res = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        existing = res.stdout if res.returncode == 0 else ""
        filtered = [l for l in existing.splitlines() if "hoyolab-checkin" not in l and "genshin-checkin" not in l]
        filtered.append(f"0 8 * * * {python_bin} {script_path} --silent >> ~/.hoyolab-checkin/checkin.log 2>&1")
        new_cron = "\n".join(filtered) + "\n"

        p = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
        p.communicate(input=new_cron)
        print("✅ Daily auto check-in registered at 08:00 AM in Linux Crontab!")
        return True

    return False


def remove_scheduler():
    """Remove background daily task."""
    if OS_NAME == "Darwin":
        plist_path = Path.home() / "Library/LaunchAgents/com.user.hoyolab-checkin.plist"
        if plist_path.exists():
            subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
            plist_path.unlink()
        print("🗑️ Removed macOS LaunchAgent schedule.")
        return True

    elif OS_NAME == "Windows":
        res = subprocess.run(["schtasks", "/Delete", "/TN", "HoYoLAB_Daily_Checkin", "/F"], capture_output=True, text=True)
        print("🗑️ Removed Windows Task Scheduler entry.")
        return True

    elif OS_NAME == "Linux":
        res = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        if res.returncode == 0:
            filtered = [l for l in res.stdout.splitlines() if "hoyolab-checkin" not in l and "genshin-checkin" not in l]
            new_cron = "\n".join(filtered) + "\n"
            p = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
            p.communicate(input=new_cron)
        print("🗑️ Removed Linux Crontab schedule.")
        return True

    return False


# ==============================================================================
# API Requests & Check-in Logic
# ==============================================================================

def request_json(url: str, method: str = "GET", headers: dict = None, body: dict = None, timeout: int = 15):
    """Execute HTTP request and return parsed JSON."""
    all_headers = dict(BASE_HEADERS)
    if headers:
        all_headers.update(headers)

    data_bytes = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data_bytes, headers=all_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="replace")
        try:
            return json.loads(err_msg)
        except Exception:
            return {"retcode": e.code, "message": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"retcode": -999, "message": str(e)}


def fetch_awards(game_key: str):
    """Fetch monthly awards catalog for the game."""
    if game_key in AWARDS_CACHE:
        return AWARDS_CACHE[game_key]

    cfg = GAMES[game_key]
    if cfg.get("is_community"):
        return []

    url = f"{cfg['home_url']}?lang=en-us&act_id={cfg['act_id']}"
    res = request_json(url, method="GET", headers={"Referer": cfg["referer"]})
    if res.get("retcode") == 0 and res.get("data") and "awards" in res["data"]:
        AWARDS_CACHE[game_key] = res["data"]["awards"]
        return AWARDS_CACHE[game_key]
    return []


def check_in_game(game_key: str, cookie: str, dry_run: bool = False, verbose: bool = True) -> dict:
    """Execute status check and daily sign-in."""
    cfg = GAMES[game_key]
    headers = {"Referer": cfg["referer"], "Cookie": cookie}

    if verbose:
        print(f"\n{cfg['emoji']} Checking {cfg['name']}...")

    # Community Check-in logic
    if cfg.get("is_community"):
        if dry_run:
            msg = "Ready to attend HoYoLAB Community."
            if verbose:
                print(f"  ℹ️  [Dry Run] {msg}")
            return {"game": cfg["name"], "success": True, "status": "DRY_RUN", "message": msg}
        sign_res = request_json(cfg["sign_url"], method="POST", headers=headers, body={})
        code = sign_res.get("retcode", -1)
        if code == 0:
            msg = "HoYoLAB Community attended successfully!"
            if verbose:
                print(f"  🎉 {msg}")
            return {"game": cfg["name"], "success": True, "status": "SUCCESS", "message": msg}
        elif code in (-5003, 1008):
            msg = "Already attended HoYoLAB Community today."
            if verbose:
                print(f"  ✅ {msg}")
            return {"game": cfg["name"], "success": True, "status": "ALREADY_CHECKED_IN", "message": msg}
        else:
            err = sign_res.get("message", "Unknown error")
            msg = f"Attendance failed: {err}"
            if verbose:
                print(f"  ❌ {msg}")
            return {"game": cfg["name"], "success": False, "status": "FAILED", "message": msg}

    act_id = cfg["act_id"]
    query = f"lang=en-us&act_id={act_id}"
    info_url = f"{cfg['info_url']}?{query}"
    sign_url = f"{cfg['sign_url']}?{query}"

    info_res = request_json(info_url, method="GET", headers=headers)
    retcode = info_res.get("retcode")

    if retcode == -100:
        msg = "Cookie is invalid or expired."
        if verbose:
            print(f"  ❌ {msg}")
        return {"game": cfg["name"], "success": False, "status": "AUTH_ERROR", "message": msg}

    if retcode != 0:
        err = info_res.get("message", "Unknown error")
        if verbose:
            print(f"  ❌ Error (code {retcode}): {err}")
        return {"game": cfg["name"], "success": False, "status": "ERROR", "message": err}

    data = info_res.get("data", {})
    total_days = data.get("total_sign_day", 0)
    is_signed = data.get("is_sign", False)
    missed_days = data.get("sign_cnt_missed", 0)

    awards = fetch_awards(game_key)

    if is_signed:
        award_text = ""
        if awards and 0 <= (total_days - 1) < len(awards):
            cur = awards[total_days - 1]
            award_text = f" -> {cur.get('name')} x{cur.get('cnt')}"
        msg = f"Already checked in today! (Day {total_days}{award_text})"
        if verbose:
            print(f"  📅 Streak: {total_days} day(s) this month (Missed: {missed_days})")
            print(f"  ✅ {msg}")
        return {
            "game": cfg["name"],
            "success": True,
            "status": "ALREADY_CHECKED_IN",
            "days": total_days,
            "message": msg,
        }

    if dry_run:
        msg = f"Not checked in yet today. Ready to claim Day {total_days + 1}."
        if verbose:
            print(f"  📅 Current streak: {total_days} day(s)")
            print(f"  ℹ️  [Dry Run] {msg}")
        return {"game": cfg["name"], "success": True, "status": "DRY_RUN", "message": msg}

    # Execute POST
    payload = {"act_id": act_id, "lang": "en-us"}
    sign_res = request_json(sign_url, method="POST", headers=headers, body=payload)
    sign_code = sign_res.get("retcode")

    if sign_code == 0:
        new_day = total_days + 1
        award_text = ""
        if awards and 0 <= (new_day - 1) < len(awards):
            aw = awards[new_day - 1]
            award_text = f" — Claimed: {aw.get('name')} x{aw.get('cnt')}"
        msg = f"Check-in successful! Total days: {new_day}{award_text}"
        if verbose:
            print(f"  🎉 {msg}")
        return {"game": cfg["name"], "success": True, "status": "SUCCESS", "days": new_day, "message": msg}

    if sign_code == -5003:
        msg = f"Already checked in today (Day {total_days})."
        if verbose:
            print(f"  ✅ {msg}")
        return {"game": cfg["name"], "success": True, "status": "ALREADY_CHECKED_IN", "days": total_days, "message": msg}

    err_msg = sign_res.get("message", "Unknown failure")
    msg = f"Check-in failed (code {sign_code}): {err_msg}"
    if verbose:
        print(f"  ❌ {msg}")
    return {"game": cfg["name"], "success": False, "status": "FAILED", "message": msg}


def run_checkin_batch(cookies: list, games: list, dry_run: bool = False, verbose: bool = True) -> list:
    """Run checkin across all accounts and games."""
    all_results = []
    for acc_idx, cookie in enumerate(cookies, 1):
        if len(cookies) > 1 and verbose:
            print(f"\n==================== Account #{acc_idx} ====================")
        for g_idx, game_key in enumerate(games):
            res = check_in_game(game_key, cookie, dry_run=dry_run, verbose=verbose)
            all_results.append(res)
            if g_idx < len(games) - 1:
                time.sleep(random.uniform(2.0, 3.5))
    return all_results


# ==============================================================================
# Interactive Terminal Hub (TUI)
# ==============================================================================

def check_account_status(cookie: str) -> dict:
    """Quickly check account validity and game states without printing noise."""
    status = {"valid": False, "uid": "Unknown", "games": {}}
    cfg = load_hoyo_config()
    enabled = cfg.get("enabled_games", ["genshin", "starrail", "zzz", "honkai3rd", "themis", "hoyolab"])
    for game_key in enabled:
        if game_key in GAMES:
            res = check_in_game(game_key, cookie, dry_run=True, verbose=False)
            status["games"][game_key] = res
            if res.get("status") != "AUTH_ERROR" and not status["valid"]:
                status["valid"] = True

    # Parse account uid from cookie string if possible
    for item in cookie.split(";"):
        if "=" in item:
            k, v = item.strip().split("=", 1)
            if k in ("ltuid_v2", "ltuid", "account_id_v2"):
                status["uid"] = v
                break
    return status


def menu_toggle_games():
    """Interactive toggle menu for active games."""
    while True:
        cfg = load_hoyo_config()
        enabled = set(cfg.get("enabled_games", ["genshin", "starrail", "zzz", "honkai3rd", "themis", "hoyolab"]))

        print("\n" + "-" * 55)
        print("🎮 Toggle Games for Daily Check-In")
        print("-" * 55)
        game_keys = list(GAMES.keys())
        for idx, gk in enumerate(game_keys, 1):
            g = GAMES[gk]
            status_box = "🟢 [ON] " if gk in enabled else "⚪ [OFF]"
            print(f" [{idx}] {status_box} {g['emoji']} {g['name']}")
        print("-" * 55)
        print("💡 Options:")
        print(" - Masukkan nomor [1-6] untuk toggle game ON / OFF")
        print(" - Ketik 'all' untuk aktifkan semua game")
        print(" - Ketik 'none' untuk nonaktifkan semua game")
        print(" - Tekan [0] atau ENTER untuk simpan & kembali")
        print("-" * 55)

        val = input("Pilihan: ").strip().lower()
        if val in ("0", ""):
            break
        elif val == "all":
            cfg["enabled_games"] = list(GAMES.keys())
            save_hoyo_config(cfg)
            print("✅ Semua game diaktifkan!")
        elif val == "none":
            cfg["enabled_games"] = []
            save_hoyo_config(cfg)
            print("⚪ Semua game dinonaktifkan!")
        elif val.isdigit() and 1 <= int(val) <= len(game_keys):
            target_key = game_keys[int(val) - 1]
            if target_key in enabled:
                enabled.remove(target_key)
                print(f"⚪ {GAMES[target_key]['name']} DINONAKTIFKAN.")
            else:
                enabled.add(target_key)
                print(f"✅ {GAMES[target_key]['name']} DIAKTIFKAN!")
            cfg["enabled_games"] = [gk for gk in game_keys if gk in enabled]
            save_hoyo_config(cfg)
        else:
            print("Input tidak valid.")


def menu_manage_scheduler():
    """Interactive submenu to install or remove auto check-in."""
    while True:
        is_active, desc = get_scheduler_status()
        print("\n" + "-" * 55)
        print(f"⏰ Daily Auto Check-In Manager [{OS_NAME}]")
        print("-" * 55)
        print(f"Status: {'🟢' if is_active else '⚪'} {desc}")
        print("\nOptions:")
        print(" [1] ⏰ Enable / Install Daily Auto Check-In (Runs at 08:00 AM)")
        print(" [2] 🗑️  Disable / Remove Auto Check-In")
        print(" [0] 🔙 Back to Main Menu")
        print("-" * 55)

        choice = input("Select an option [0-2]: ").strip()
        if choice == "1":
            install_scheduler()
        elif choice == "2":
            remove_scheduler()
        elif choice == "0":
            break
        else:
            print("Invalid selection.")


def menu_login_options():
    """Interactive submenu for login."""
    print("\n" + "-" * 55)
    print("🔑 Login to HoYoLAB")
    print("-" * 55)
    print(" [1] ✨ Auto-Import from Browser (Zen / Firefox) [Instant]")
    print(" [2] 🌐 Open Browser Window (Google / Apple / Email Login)")
    print(" [3] ⌨️  Enter Cookie Manually")
    print(" [0] 🔙 Cancel")
    print("-" * 55)

    choice = input("Select option [0-3]: ").strip()
    if choice == "1":
        cookie = auto_import_from_browser(save=True)
        if cookie:
            print("\n✅ Successfully imported and saved login credentials!")
            return cookie
        else:
            print("[-] No active browser session found. Try option 2.")
    elif choice == "2":
        return interactive_browser_login()
    elif choice == "3":
        manual = input("\nPaste your cookie string (ltoken_v2=...; ltuid_v2=...): ").strip()
        if manual:
            save_cookie_to_env(manual)
            print("✅ Cookie saved.")
            return manual
    return None


def interactive_hub():
    """Main interactive hub when running without arguments."""
    while True:
        cookies, _ = get_cookies_from_env_or_config()
        cookie = cookies[0] if cookies else None

        print("\n" + "=" * 58)
        print("🎮  HoYoLAB Easy Check-In Hub (All Games)")
        print("=" * 58)

        account_info = None
        if cookie:
            account_info, _ = run_with_progress(
                "Memeriksa status sesi & hadiah HoYoLAB",
                lambda: check_account_status(cookie),
                timeout=6.0
            )
            if not account_info:
                account_info = {"valid": False, "uid": "Unknown", "games": {}}

            if account_info["valid"]:
                print(f"👤 Account ID:    {account_info['uid']}")
                print("🔑 Token Status:  🟢 VALID (Active)")
                print("📅 Today's Status:")
                for gk, gres in account_info["games"].items():
                    name = GAMES[gk]["name"]
                    emoji = GAMES[gk]["emoji"]
                    if gres.get("status") == "ALREADY_CHECKED_IN":
                        print(f"   {emoji} {name:<21}: ✅ Checked In (Day {gres.get('days', 0)})")
                    elif gres.get("status") == "DRY_RUN":
                        print(f"   {emoji} {name:<21}: 🟡 Ready to Claim!")
                    else:
                        print(f"   {emoji} {name:<21}: ⚪ {gres.get('message', 'Ready')}")
            else:
                print(f"👤 Account ID:    {account_info['uid']}")
                print("🔑 Token Status:  🔴 EXPIRED or INVALID")
        else:
            print("👤 Account:       ⚪ Not Logged In")
            print("🔑 Token Status:  ⚪ No Credentials Found")

        is_sched, sched_desc = get_scheduler_status()
        print(f"⏰ Auto Check-in:  {'🟢' if is_sched else '⚪'} {sched_desc}")
        print("=" * 58)

        # Dynamic Menu Options
        if not cookie or (account_info and not account_info["valid"]):
            print("╭" + "─" * 56 + "╮")
            print("│  ⚠️  STATUS AKUN: BELUM LOGIN / SESI HOYOLAB KOSONG     │")
            print("│  Check-in harian tidak dapat berjalan tanpa akun!      │")
            print("│  👉 Pilih opsi [1] di bawah untuk login / impor sesi!  │")
            print("╰" + "─" * 56 + "╯\n")

            print(" [1] 🔑 [WAJIB] LOGIN SEKARANG (Auto-import Zen/Firefox / Browser)")
            print(" [2] ⏰ Manage Auto Check-In Schedule")
            print(" [3] 🎮 Toggle Active Games")
            print(" [4] 🔄 Check for Updates")
            print(" [0] 🚪 Exit")
            print("=" * 58)

            choice = input("Select an option [0-4]: ").strip()
            if choice == "1":
                menu_login_options()
            elif choice == "2":
                menu_manage_scheduler()
            elif choice == "3":
                menu_toggle_games()
            elif choice == "4":
                check_for_updates(prompt_if_latest=True)
            elif choice == "0":
                print("Goodbye! 👋")
                sys.exit(0)
        else:
            cfg = load_hoyo_config()
            enabled_games = cfg.get("enabled_games", ["genshin", "starrail", "zzz", "honkai3rd", "themis", "hoyolab"])
            enabled_str = f"{len(enabled_games)}/{len(GAMES)} Active"

            print(" [1] 🚀 Check-in Now (Claim Today's Rewards)")
            print(" [2] 🔍 View Streak & Rewards Catalog (Dry Run)")
            print(f" [3] 🎮 Toggle Active Games ({enabled_str})")
            print(" [4] ⏰ Manage Daily Auto Check-In (Windows / Mac / Linux)")
            print(" [5] 🔄 Re-login / Switch Account")
            print(" [6] 🔄 Check for Updates")
            print(" [0] 🚪 Exit")
            print("=" * 58)

            choice = input("Select an option [0-6]: ").strip()
            if choice == "1":
                run_checkin_batch([cookie], enabled_games, dry_run=False, verbose=True)
                input("\nPress Enter to return to menu...")
            elif choice == "2":
                run_checkin_batch([cookie], enabled_games, dry_run=True, verbose=True)
                input("\nPress Enter to return to menu...")
            elif choice == "3":
                menu_toggle_games()
            elif choice == "4":
                menu_manage_scheduler()
            elif choice == "5":
                menu_login_options()
            elif choice == "6":
                check_for_updates(prompt_if_latest=True)
            elif choice == "0":
                print("Goodbye! 👋")
                sys.exit(0)


# ==============================================================================
# CLI Entry Point
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="HoYoLAB Easy Check-In Hub")
    parser.add_argument("--game", choices=list(GAMES.keys()) + ["all"], default="all")
    parser.add_argument("--cookie", type=str, help="Direct cookie string override")
    parser.add_argument("--config", type=str, help="Custom .env path")
    parser.add_argument("--dry-run", action="store_true", help="Check status without claiming")
    parser.add_argument("--silent", action="store_true", help="Run check-in silently (for scheduler/cron)")
    parser.add_argument("--cron", action="store_true", help="Alias for --silent")
    parser.add_argument("--login", action="store_true", help="Open login menu")
    parser.add_argument("--import-browser", action="store_true", help="Auto-import from browser")
    parser.add_argument("--login-browser", action="store_true", help="Open browser GUI login")
    parser.add_argument("--install-schedule", action="store_true", help="Install auto daily check-in")
    parser.add_argument("--remove-schedule", action="store_true", help="Remove auto daily check-in")

    args = parser.parse_args()

    # Direct CLI actions
    if args.install_schedule:
        install_scheduler()
        sys.exit(0)

    if args.remove_schedule:
        remove_scheduler()
        sys.exit(0)

    if args.import_browser:
        auto_import_from_browser(save=True)
        sys.exit(0)

    if args.login_browser:
        interactive_browser_login()
        sys.exit(0)

    if args.login:
        menu_login_options()
        sys.exit(0)

    # If launched with no args and connected to a terminal (interactive TTY):
    if len(sys.argv) == 1 and sys.stdin.isatty():
        check_for_updates(prompt_if_latest=False)
        interactive_hub()
        return

    # Non-interactive / CLI mode (cron, scheduler, or explicit flags)
    config_path = Path(args.config) if args.config else None
    cookies, loaded_vars = get_cookies_from_env_or_config(config_path)
    if args.cookie:
        cookies = [args.cookie]

    if not cookies:
        imported = auto_import_from_browser(save=True)
        if imported:
            cookies = [imported]
        else:
            print("❌ Error: No HoYoLAB credentials found! Run 'hoyolab-checkin' to log in.")
            sys.exit(1)

    cfg = load_hoyo_config()
    games_to_run = cfg.get("enabled_games", ["genshin", "starrail", "zzz", "honkai3rd", "themis", "hoyolab"]) if args.game == "all" else [args.game]

    verbose = not (args.silent or args.cron)
    if verbose:
        print(f"🚀 HoYoLAB Check-In [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
    else:
        # Wait for active internet connection upon wake up
        if not wait_for_internet(timeout=180, verbose=False):
            print(f"❌ [HoYoLAB] Internet connection not available after 180s wake-up wait.")
            sys.exit(1)

    max_retries = 3 if (args.silent or args.cron) else 1
    success = False
    for attempt in range(1, max_retries + 1):
        results = run_checkin_batch(cookies, games_to_run, dry_run=args.dry_run, verbose=verbose)
        success = all(r.get("success") for r in results)
        if success or attempt == max_retries:
            break
        time.sleep(30)
        wait_for_internet(timeout=60, verbose=False)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        handle_sigint()
