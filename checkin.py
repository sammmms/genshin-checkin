#!/usr/bin/env python3
"""
HoYoLAB Easy Check-In & Helper Hub
Supports: Windows, macOS, Linux
Games: Honkai: Star Rail (HSR), Genshin Impact, and Zenless Zone Zero (ZZZ)
Zero external dependencies for core functionality.
Bilingual Support: English (Default) & Bahasa Indonesia
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
APP_NAME = "hoyolab-checkin"
APP_VERSION = "1.4.0"
SCRIPT_PATH = Path(__file__).resolve()

# ==============================================================================
# Internationalization (i18n): EN (Default) & ID
# ==============================================================================

DEFAULT_LANG = "en"
CURRENT_LANG = "en"

TRANSLATIONS = {
    "en": {
        "sigint_exit": "\n\n👋 Operation cancelled by user (Exit). Goodbye!\n",
        "checking_updates": "Checking for updates",
        "update_offline": "[*] Checking for updates... [Skip / Offline]",
        "update_latest": "[*] Checking for updates... [Latest Version: v{ver} ✓]",
        "update_already_latest": "\n[✓] You are already on the latest version (v{ver}).\n",
        "press_enter_continue": "Press Enter to continue...",
        "press_enter_return": "\nPress Enter to return to menu...",
        "update_available": "🚀 UPDATE AVAILABLE! (v{current} ➔ v{latest})",
        "release_date": "📅 Release: {date}",
        "changelog": "📋 Changelog:",
        "install_update_prompt": "Install update v{ver} now? [Y/n]: ",
        "downloading_update": "\n⬇️  Downloading update v{ver}...",
        "update_no_url": "[!] Download URL not available.",
        "update_success": "✅ Successfully updated to v{ver}!",
        "restarting_app": "🔄 Restarting application...",
        "update_failed": "[x] Failed to install update: {err}",
        "update_skipped": "[*] Update skipped.\n",
        "cookie_saved": "💾 Cookie saved to: {path}",
        "found_browser_session": "✨ Found active HoYoLAB session in {browser}!",
        "account_id_label": "   👤 Account ID: {uid}",
        "launch_login_window": "\n🌐 Launching interactive login window...",
        "login_instructions_1": "👉 Please log in to HoYoLAB in the window that appears.",
        "login_instructions_2": "👉 (Google, Apple, or Email + Password login are all supported).\n",
        "installing_playwright": "📦 Installing Playwright automation engine...",
        "waiting_user_login": "⏳ Waiting for you to log in...",
        "login_detected": "\n🎉 Login detected for Account ID: {uid}!",
        "login_timeout": "❌ Login timed out or cancelled.",
        "status_active": "Active",
        "status_loaded": "Loaded",
        "status_not_configured": "Not Configured",
        "status_unsupported": "Unsupported OS",
        "wait_internet": "Waiting for active internet connection",
        "internet_active": "Internet connection is active! ({elapsed:.1f}s)",
        "internet_failed": "Failed to connect to internet after {timeout} seconds.",
        "internet_wake_failed": "❌ [HoYoLAB] Internet connection not available after {timeout}s wake-up wait.",
        "scheduler_macos_installed": "✅ Daily auto check-in registered at 08:00 AM via macOS LaunchAgent!\nℹ️ Catches up automatically whenever MacBook wakes up during the day.",
        "scheduler_win_installed": "✅ Daily auto check-in registered at 08:00 AM in Windows Task Scheduler!",
        "scheduler_linux_installed": "✅ Daily auto check-in registered at 08:00 AM in Linux Crontab!",
        "scheduler_macos_removed": "🗑️ Removed macOS LaunchAgent schedule.",
        "scheduler_win_removed": "🗑️ Removed Windows Task Scheduler entry.",
        "scheduler_linux_removed": "🗑️ Removed Linux Crontab schedule.",
        "checkin_start": "Checking in to {name}...",
        "auth_expired": "Session cookie expired or invalid. Please re-login.",
        "checkin_err": "Error (code {code}): {err}",
        "already_checked_in": "Already checked in today! (Day {day}{award})",
        "streak_status": "📅 Streak: {days} day(s) this month (Missed: {missed})",
        "dry_run_ready": "Not checked in yet today. Ready to claim Day {day}.",
        "dry_run_streak": "📅 Current streak: {days} day(s)",
        "checkin_success": "Check-in successful! Total days: {days}{award}",
        "checkin_failed": "Check-in failed (code {code}): {err}",
        "community_ready": "Ready to attend HoYoLAB Community.",
        "community_success": "HoYoLAB Community attended successfully!",
        "community_already": "Already attended HoYoLAB Community today.",
        "community_failed": "Attendance failed: {err}",
        "toggle_games_title": "🎮 Toggle Games for Daily Check-In",
        "toggle_options_header": "💡 Options:",
        "toggle_opt_1": " - Enter number [1-{count}] to toggle game ON / OFF",
        "toggle_opt_2": " - Type 'all' to enable all games",
        "toggle_opt_3": " - Type 'none' to disable all games",
        "toggle_opt_4": " - Press [0] or ENTER to save & return",
        "prompt_choice": "Choice: ",
        "all_games_enabled": "✅ All games enabled!",
        "all_games_disabled": "⚪ All games disabled!",
        "game_disabled": "⚪ {name} DISABLED.",
        "game_enabled": "✅ {name} ENABLED!",
        "invalid_input": "Invalid input.",
        "sched_menu_title": "⏰ Daily Auto Check-In Manager [{os}]",
        "sched_status": "Status: {icon} {desc}",
        "sched_opt_install": " [1] ⏰ Enable / Install Daily Auto Check-In (Runs at 08:00 AM)",
        "sched_opt_remove": " [2] 🗑️  Disable / Remove Auto Check-In",
        "sched_opt_back": " [0] 🔙 Back to Main Menu",
        "sched_prompt": "Select an option [0-2]: ",
        "login_menu_title": "🔑 Login to HoYoLAB",
        "login_opt_auto": " [1] ✨ Auto-Import from Browser (Zen / Firefox) [Instant]",
        "login_opt_browser": " [2] 🌐 Open Browser Window (Google / Apple / Email Login)",
        "login_opt_manual": " [3] ⌨️  Enter Cookie Manually",
        "login_opt_cancel": " [0] 🔙 Cancel",
        "login_prompt": "Select option [0-3]: ",
        "login_auto_success": "\n✅ Successfully imported and saved login credentials!",
        "login_auto_none": "[-] No active browser session found. Try option 2.",
        "paste_cookie": "\nPaste your cookie string (ltoken_v2=...; ltuid_v2=...): ",
        "cookie_saved_success": "✅ Cookie saved.",
        "lang_menu_title": "🌐 Select Language / Pilih Bahasa",
        "lang_opt_en": " [1] 🇬🇧 English (Default)",
        "lang_opt_id": " [2] 🇮🇩 Bahasa Indonesia",
        "lang_opt_back": " [0] 🔙 Back to Main Menu",
        "lang_prompt": "Select an option [0-2]: ",
        "lang_saved": "✅ Language changed to: {lang}",
        "hub_title": "🎮  HoYoLAB Easy Check-In Hub (All Games)",
        "hub_account_logged": "👤 Account ID:    {uid}",
        "hub_token_valid": "🔑 Token Status:  🟢 VALID (Active)",
        "hub_token_expired": "🔑 Token Status:  🔴 EXPIRED or INVALID",
        "hub_account_not_logged": "👤 Account:       ⚪ Not Logged In",
        "hub_no_credentials": "🔑 Token Status:  ⚪ No Credentials Found",
        "hub_today_status": "📅 Today's Status:",
        "hub_auto_checkin": "⏰ Auto Check-in:  {icon} {desc}",
        "hub_warning_title": "⚠️  ACCOUNT STATUS: NOT LOGGED IN / EMPTY HOYOLAB SESSION",
        "hub_warning_desc1": "Daily check-in cannot run without an account!",
        "hub_warning_desc2": "👉 Choose option [1] below to log in or import your session!",
        "hub_no_login_opt_1": " [1] 🔑 [REQUIRED] LOGIN NOW (Auto-import Zen/Firefox / Browser)",
        "hub_no_login_opt_2": " [2] ⏰ Manage Auto Check-In Schedule",
        "hub_no_login_opt_3": " [3] 🎮 Toggle Active Games",
        "hub_no_login_opt_4": " [4] 🔄 Check for Updates",
        "hub_no_login_opt_5": " [5] 🌐 Language / Bahasa (Current: English)",
        "hub_no_login_opt_0": " [0] 🚪 Exit",
        "hub_no_login_prompt": "Select an option [0-5]: ",
        "hub_logged_opt_1": " [1] 🚀 Check-in Now (Claim Today's Rewards)",
        "hub_logged_opt_2": " [2] 🔍 View Streak & Rewards Catalog (Dry Run)",
        "hub_logged_opt_3": " [3] 🎮 Toggle Active Games ({games})",
        "hub_logged_opt_4": " [4] ⏰ Manage Daily Auto Check-In ({os})",
        "hub_logged_opt_5": " [5] 🔄 Re-login / Switch Account",
        "hub_logged_opt_6": " [6] 🔄 Check for Updates",
        "hub_logged_opt_7": " [7] 🌐 Language / Bahasa (Current: English)",
        "hub_logged_opt_0": " [0] 🚪 Exit",
        "hub_login_prompt": "Select an option [0-7]: ",
        "goodbye": "Goodbye! 👋",
        "cli_no_cred": "❌ Error: No HoYoLAB credentials found! Run 'hoyolab-checkin' to log in.",
        "cli_starting": "🚀 HoYoLAB Check-In [{time}]",
        "checking_session_progress": "Checking HoYoLAB session status & rewards",
        "checked_in_badge": "Checked In (Day {day})",
        "ready_to_claim_badge": "Ready to Claim!",
        "ready_badge": "Ready",
    },
    "id": {
        "sigint_exit": "\n\n👋 Operasi dibatalkan oleh pengguna (Keluar). Sampai jumpa!\n",
        "checking_updates": "Memeriksa pembaruan",
        "update_offline": "[*] Memeriksa pembaruan... [Lewati / Offline]",
        "update_latest": "[*] Memeriksa pembaruan... [Versi Terbaru: v{ver} ✓]",
        "update_already_latest": "\n[✓] Anda sudah menggunakan versi terbaru (v{ver}).\n",
        "press_enter_continue": "Tekan Enter untuk melanjutkan...",
        "press_enter_return": "\nTekan Enter untuk kembali ke menu...",
        "update_available": "🚀 PEMBARUAN TERSEDIA! (v{current} ➔ v{latest})",
        "release_date": "📅 Rilis: {date}",
        "changelog": "📋 Catatan Perubahan:",
        "install_update_prompt": "Pasang pembaruan v{ver} sekarang? [Y/n]: ",
        "downloading_update": "\n⬇️  Mengunduh pembaruan v{ver}...",
        "update_no_url": "[!] URL unduhan tidak tersedia.",
        "update_success": "✅ Berhasil memperbarui ke v{ver}!",
        "restarting_app": "🔄 Memulai ulang aplikasi...",
        "update_failed": "[x] Gagal memasang pembaruan: {err}",
        "update_skipped": "[*] Pembaruan dilewati.\n",
        "cookie_saved": "💾 Cookie disimpan ke: {path}",
        "found_browser_session": "✨ Menemukan sesi aktif HoYoLAB di {browser}!",
        "account_id_label": "   👤 ID Akun: {uid}",
        "launch_login_window": "\n🌐 Membuka jendela login browser interaktif...",
        "login_instructions_1": "👉 Silakan login ke akun HoYoLAB pada jendela browser yang muncul.",
        "login_instructions_2": "👉 (Mendukung login dengan Google, Apple, atau Email + Sandi).\n",
        "installing_playwright": "📦 Memasang mesin automasi Playwright...",
        "waiting_user_login": "⏳ Menunggu Anda login di browser...",
        "login_detected": "\n🎉 Login terdeteksi untuk ID Akun: {uid}!",
        "login_timeout": "❌ Waktu login habis atau dibatalkan.",
        "status_active": "Aktif",
        "status_loaded": "Dimuat",
        "status_not_configured": "Belum Dikonfigurasi",
        "status_unsupported": "OS Tidak Didukung",
        "wait_internet": "Menunggu koneksi internet aktif",
        "internet_active": "Koneksi internet telah aktif! ({elapsed:.1f}s)",
        "internet_failed": "Gagal terhubung ke internet setelah {timeout} detik.",
        "internet_wake_failed": "❌ [HoYoLAB] Koneksi internet tidak tersedia setelah menunggu {timeout} detik.",
        "scheduler_macos_installed": "✅ Auto check-in harian berhasil didaftarkan pukul 08:00 via macOS LaunchAgent!\nℹ️ Akan mengejar otomatis kapan pun MacBook menyala di siang hari.",
        "scheduler_win_installed": "✅ Auto check-in harian berhasil didaftarkan pukul 08:00 di Windows Task Scheduler!",
        "scheduler_linux_installed": "✅ Auto check-in harian berhasil didaftarkan pukul 08:00 di Linux Crontab!",
        "scheduler_macos_removed": "🗑️ Jadwal macOS LaunchAgent telah dihapus.",
        "scheduler_win_removed": "🗑️ Entri Windows Task Scheduler telah dihapus.",
        "scheduler_linux_removed": "🗑️ Entri Linux Crontab telah dihapus.",
        "checkin_start": "Memproses check-in untuk {name}...",
        "auth_expired": "Cookie sesi kedaluwarsa atau tidak valid. Silakan login ulang.",
        "checkin_err": "Error (kode {code}): {err}",
        "already_checked_in": "Sudah check-in hari ini! (Hari ke-{day}{award})",
        "streak_status": "📅 Streak: {days} hari bulan ini (Terlewat: {missed})",
        "dry_run_ready": "Belum check-in hari ini. Siap klaim Hari ke-{day}.",
        "dry_run_streak": "📅 Streak saat ini: {days} hari",
        "checkin_success": "Check-in berhasil! Total hari: {days}{award}",
        "checkin_failed": "Check-in gagal (kode {code}): {err}",
        "community_ready": "Siap absen di Komunitas HoYoLAB.",
        "community_success": "Absen Komunitas HoYoLAB berhasil!",
        "community_already": "Sudah absen di Komunitas HoYoLAB hari ini.",
        "community_failed": "Absen Komunitas gagal: {err}",
        "toggle_games_title": "🎮 Atur Game untuk Daily Check-In",
        "toggle_options_header": "💡 Pilihan:",
        "toggle_opt_1": " - Masukkan nomor [1-{count}] untuk mengubah status game ON / OFF",
        "toggle_opt_2": " - Ketik 'all' untuk mengaktifkan semua game",
        "toggle_opt_3": " - Ketik 'none' untuk menonaktifkan semua game",
        "toggle_opt_4": " - Tekan [0] atau ENTER untuk simpan & kembali",
        "prompt_choice": "Pilihan: ",
        "all_games_enabled": "✅ Semua game diaktifkan!",
        "all_games_disabled": "⚪ Semua game dinonaktifkan!",
        "game_disabled": "⚪ {name} DINONAKTIFKAN.",
        "game_enabled": "✅ {name} DIAKTIFKAN!",
        "invalid_input": "Pilihan tidak valid.",
        "sched_menu_title": "⏰ Manajer Auto Check-In Harian [{os}]",
        "sched_status": "Status: {icon} {desc}",
        "sched_opt_install": " [1] ⏰ Pasang / Aktifkan Auto Check-In Harian (Pukul 08:00)",
        "sched_opt_remove": " [2] 🗑️  Nonaktifkan / Hapus Auto Check-In",
        "sched_opt_back": " [0] 🔙 Kembali ke Menu Utama",
        "sched_prompt": "Pilih opsi [0-2]: ",
        "login_menu_title": "🔑 Login ke HoYoLAB",
        "login_opt_auto": " [1] ✨ Impor Otomatis dari Browser (Zen / Firefox) [Instan]",
        "login_opt_browser": " [2] 🌐 Buka Jendela Browser (Login Google / Apple / Email)",
        "login_opt_manual": " [3] ⌨️  Masukkan Cookie Manual",
        "login_opt_cancel": " [0] 🔙 Batal",
        "login_prompt": "Pilih opsi [0-3]: ",
        "login_auto_success": "\n✅ Berhasil mengimpor dan menyimpan kredensial login!",
        "login_auto_none": "[-] Tidak ditemukan sesi browser aktif. Coba pilihan 2.",
        "paste_cookie": "\nTempel string cookie Anda (ltoken_v2=...; ltuid_v2=...): ",
        "cookie_saved_success": "✅ Cookie berhasil disimpan.",
        "lang_menu_title": "🌐 Pilih Bahasa / Select Language",
        "lang_opt_en": " [1] 🇬🇧 English (Default)",
        "lang_opt_id": " [2] 🇮🇩 Bahasa Indonesia",
        "lang_opt_back": " [0] 🔙 Kembali ke Menu Utama",
        "lang_prompt": "Pilih opsi [0-2]: ",
        "lang_saved": "✅ Bahasa berhasil diubah ke: {lang}",
        "hub_title": "🎮  HoYoLAB Easy Check-In Hub (Semua Game)",
        "hub_account_logged": "👤 ID Akun:       {uid}",
        "hub_token_valid": "🔑 Status Token:  🟢 VALID (Aktif)",
        "hub_token_expired": "🔑 Status Token:  🔴 KEDALUWARSA atau TIDAK VALID",
        "hub_account_not_logged": "👤 Akun:          ⚪ Belum Login",
        "hub_no_credentials": "🔑 Status Token:  ⚪ Kredensial Tidak Ditemukan",
        "hub_today_status": "📅 Status Hari Ini:",
        "hub_auto_checkin": "⏰ Auto Check-in:  {icon} {desc}",
        "hub_warning_title": "⚠️  STATUS AKUN: BELUM LOGIN / SESI HOYOLAB KOSONG",
        "hub_warning_desc1": "Check-in harian tidak dapat berjalan tanpa akun!",
        "hub_warning_desc2": "👉 Pilih opsi [1] di bawah untuk login / impor sesi!",
        "hub_no_login_opt_1": " [1] 🔑 [WAJIB] LOGIN SEKARANG (Auto-import Zen/Firefox / Browser)",
        "hub_no_login_opt_2": " [2] ⏰ Kelola Jadwal Auto Check-In",
        "hub_no_login_opt_3": " [3] 🎮 Atur Game Aktif",
        "hub_no_login_opt_4": " [4] 🔄 Cek Pembaruan",
        "hub_no_login_opt_5": " [5] 🌐 Bahasa / Language (Saat ini: Bahasa Indonesia)",
        "hub_no_login_opt_0": " [0] 🚪 Keluar",
        "hub_no_login_prompt": "Pilih opsi [0-5]: ",
        "hub_logged_opt_1": " [1] 🚀 Check-in Sekarang (Klaim Hadiah Hari Ini)",
        "hub_logged_opt_2": " [2] 🔍 Lihat Streak & Katalog Hadiah (Dry Run)",
        "hub_logged_opt_3": " [3] 🎮 Atur Game Aktif ({games})",
        "hub_logged_opt_4": " [4] ⏰ Kelola Auto Check-In Harian ({os})",
        "hub_logged_opt_5": " [5] 🔄 Login Ulang / Ganti Akun",
        "hub_logged_opt_6": " [6] 🔄 Cek Pembaruan",
        "hub_logged_opt_7": " [7] 🌐 Bahasa / Language (Saat ini: Bahasa Indonesia)",
        "hub_logged_opt_0": " [0] 🚪 Keluar",
        "hub_login_prompt": "Pilih opsi [0-7]: ",
        "goodbye": "Sampai jumpa! 👋",
        "cli_no_cred": "❌ Error: Kredensial HoYoLAB tidak ditemukan! Jalankan 'hoyolab-checkin' untuk login.",
        "cli_starting": "🚀 HoYoLAB Check-In [{time}]",
        "checking_session_progress": "Memeriksa status sesi & hadiah HoYoLAB",
        "checked_in_badge": "Sudah Check-In (Hari ke-{day})",
        "ready_to_claim_badge": "Siap Diklaim!",
        "ready_badge": "Siap",
    }
}

def t(key: str, default: str = None, **kwargs) -> str:
    lang = CURRENT_LANG if CURRENT_LANG in TRANSLATIONS else DEFAULT_LANG
    s = TRANSLATIONS.get(lang, {}).get(key)
    if s is None:
        s = TRANSLATIONS.get(DEFAULT_LANG, {}).get(key, default if default is not None else key)
    if kwargs:
        try:
            return s.format(**kwargs)
        except Exception:
            return s
    return s

def set_language(lang_code: str):
    global CURRENT_LANG
    if str(lang_code).lower() in ("id", "in", "indonesia", "indonesian"):
        CURRENT_LANG = "id"
    else:
        CURRENT_LANG = "en"

def handle_sigint(sig=None, frame=None):
    print(t("sigint_exit"))
    sys.exit(0)

signal.signal(signal.SIGINT, handle_sigint)

# ==============================================================================
# Configuration & State Management
# ==============================================================================

def load_hoyo_config() -> dict:
    """Load configuration including enabled games and language."""
    default = {
        "enabled_games": ["genshin", "starrail", "zzz", "honkai3rd", "themis", "hoyolab"],
        "language": "en"
    }
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

    t_thread = threading.Thread(target=target, daemon=True)
    t_thread.start()

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
    Checks latest update from https://script.wsnsam.my.id/api/updates?app=hoyolab-checkin
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

    update_data, _ = run_with_progress(t("checking_updates"), fetch_remote, timeout=3.5)

    if not update_data or "version" not in update_data:
        print(t("update_offline"))
        time.sleep(0.2)
        return

    latest_ver = update_data["version"]
    if parse_semver(latest_ver) <= parse_semver(APP_VERSION):
        print(t("update_latest", ver=APP_VERSION))
        time.sleep(0.3)
        if prompt_if_latest:
            print(t("update_already_latest", ver=APP_VERSION))
            input(t("press_enter_continue"))
        return

    sys.stdout.write("\r" + " " * 80 + "\r")
    sys.stdout.flush()

    print("\n" + "=" * 62)
    print(t("update_available", current=APP_VERSION, latest=latest_ver))
    print(t("release_date", date=update_data.get('release_date', 'New')))
    print("=" * 62)
    print(t("changelog"))
    for change in update_data.get("changelog", []):
        print(f"  • {change}")
    print("=" * 62 + "\n")

    action = input(t("install_update_prompt", ver=latest_ver)).strip().lower()
    if action in ("", "y", "yes"):
        print(t("downloading_update", ver=latest_ver))
        download_url = update_data.get("download_url")
        if not download_url:
            print(t("update_no_url"))
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

            print(t("update_success", ver=latest_ver))
            print(t("restarting_app"))
            time.sleep(1)
            os.execv(sys.executable, [sys.executable, str(SCRIPT_PATH)] + sys.argv[1:])
        except Exception as e:
            print(t("update_failed", err=e))
            input(t("press_enter_continue"))
    else:
        print(t("update_skipped"))

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
    print(t("cookie_saved", path=target_path))

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
                print(t("found_browser_session", browser=browser_name))
                print(t("account_id_label", uid=ltuid))
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
    print(t("launch_login_window"))
    print(t("login_instructions_1"))
    print(t("login_instructions_2"))

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(t("installing_playwright"))
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
        print(t("waiting_user_login"))

        captured_cookie = None
        start_time = time.time()
        while time.time() - start_time < 300:
            cookies = context.cookies(["https://act.hoyolab.com", "https://hoyolab.com", "https://hoyoverse.com"])
            cookie_dict = {c["name"]: c["value"] for c in cookies}

            ltoken = cookie_dict.get("ltoken_v2")
            ltuid = cookie_dict.get("ltuid_v2") or cookie_dict.get("account_id_v2")

            if ltoken and ltuid:
                captured_cookie = f"ltuid_v2={ltuid}; ltoken_v2={ltoken};"
                print(t("login_detected", uid=ltuid))
                break
            time.sleep(2)

        browser.close()
        if captured_cookie:
            save_cookie_to_env(captured_cookie)
            return captured_cookie
        else:
            print(t("login_timeout"))
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
                return True, f"macOS LaunchAgent ({t('status_active')})"
            return True, f"macOS LaunchAgent ({t('status_loaded')})"
        return False, t("status_not_configured")

    elif OS_NAME == "Windows":
        res = subprocess.run(["schtasks", "/Query", "/TN", "HoYoLAB_Daily_Checkin"], capture_output=True, text=True)
        if res.returncode == 0:
            return True, f"Windows Task Scheduler ({t('status_active')})"
        return False, t("status_not_configured")

    elif OS_NAME == "Linux":
        res = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        if "genshin-checkin" in res.stdout or "hoyolab-checkin" in res.stdout:
            return True, f"Linux Crontab ({t('status_active')})"
        return False, t("status_not_configured")

    return False, t("status_unsupported")

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
            sys.stdout.write(f"\r[*] {t('wait_internet')}... {spinner[step % len(spinner)]} [{bar}] {elapsed:.1f}s/{timeout}s")
            sys.stdout.flush()
            step += 1

        try:
            s = socket.create_connection(("1.1.1.1", 53), timeout=2)
            s.close()
            req = urllib.request.Request("https://www.google.com", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status in (200, 204, 301, 302):
                    if verbose:
                        sys.stdout.write(f"\r{' ' * 75}\r[✓] {t('internet_active', elapsed=elapsed)}\n")
                        sys.stdout.flush()
                    return True
        except Exception:
            pass
        time.sleep(check_interval)

    if verbose:
        sys.stdout.write(f"\r{' ' * 75}\r[!] {t('internet_failed', timeout=timeout)}\n")
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
        print(t("scheduler_macos_installed"))
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
            print(t("scheduler_win_installed"))
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
        print(t("scheduler_linux_installed"))
        return True

    return False

def remove_scheduler():
    """Remove background daily task."""
    if OS_NAME == "Darwin":
        plist_path = Path.home() / "Library/LaunchAgents/com.user.hoyolab-checkin.plist"
        if plist_path.exists():
            subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
            plist_path.unlink()
        print(t("scheduler_macos_removed"))
        return True

    elif OS_NAME == "Windows":
        res = subprocess.run(["schtasks", "/Delete", "/TN", "HoYoLAB_Daily_Checkin", "/F"], capture_output=True, text=True)
        print(t("scheduler_win_removed"))
        return True

    elif OS_NAME == "Linux":
        res = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        if res.returncode == 0:
            filtered = [l for l in res.stdout.splitlines() if "hoyolab-checkin" not in l and "genshin-checkin" not in l]
            new_cron = "\n".join(filtered) + "\n"
            p = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
            p.communicate(input=new_cron)
        print(t("scheduler_linux_removed"))
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
        print(f"\n{cfg['emoji']} {t('checkin_start', name=cfg['name'])}")

    # Community Check-in logic
    if cfg.get("is_community"):
        if dry_run:
            msg = t("community_ready")
            if verbose:
                print(f"  ℹ️  [Dry Run] {msg}")
            return {"game": cfg["name"], "success": True, "status": "DRY_RUN", "message": msg}
        sign_res = request_json(cfg["sign_url"], method="POST", headers=headers, body={})
        code = sign_res.get("retcode", -1)
        if code == 0:
            msg = t("community_success")
            if verbose:
                print(f"  🎉 {msg}")
            return {"game": cfg["name"], "success": True, "status": "SUCCESS", "message": msg}
        elif code in (-5003, 1008):
            msg = t("community_already")
            if verbose:
                print(f"  ✅ {msg}")
            return {"game": cfg["name"], "success": True, "status": "ALREADY_CHECKED_IN", "message": msg}
        else:
            err = sign_res.get("message", "Unknown error")
            msg = t("community_failed", err=err)
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
        msg = t("auth_expired")
        if verbose:
            print(f"  ❌ {msg}")
        return {"game": cfg["name"], "success": False, "status": "AUTH_ERROR", "message": msg}

    if retcode != 0:
        err = info_res.get("message", "Unknown error")
        if verbose:
            print(f"  ❌ {t('checkin_err', code=retcode, err=err)}")
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
        msg = t("already_checked_in", day=total_days, award=award_text)
        if verbose:
            print(f"  {t('streak_status', days=total_days, missed=missed_days)}")
            print(f"  ✅ {msg}")
        return {
            "game": cfg["name"],
            "success": True,
            "status": "ALREADY_CHECKED_IN",
            "days": total_days,
            "message": msg,
        }

    if dry_run:
        msg = t("dry_run_ready", day=total_days + 1)
        if verbose:
            print(f"  {t('dry_run_streak', days=total_days)}")
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
        msg = t("checkin_success", days=new_day, award=award_text)
        if verbose:
            print(f"  🎉 {msg}")
        return {"game": cfg["name"], "success": True, "status": "SUCCESS", "days": new_day, "message": msg}

    if sign_code == -5003:
        msg = t("already_checked_in", day=total_days, award="")
        if verbose:
            print(f"  ✅ {msg}")
        return {"game": cfg["name"], "success": True, "status": "ALREADY_CHECKED_IN", "days": total_days, "message": msg}

    err_msg = sign_res.get("message", "Unknown failure")
    msg = t("checkin_failed", code=sign_code, err=err_msg)
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
        print(t("toggle_games_title"))
        print("-" * 55)
        game_keys = list(GAMES.keys())
        for idx, gk in enumerate(game_keys, 1):
            g = GAMES[gk]
            status_box = "🟢 [ON] " if gk in enabled else "⚪ [OFF]"
            print(f" [{idx}] {status_box} {g['emoji']} {g['name']}")
        print("-" * 55)
        print(t("toggle_options_header"))
        print(t("toggle_opt_1", count=len(game_keys)))
        print(t("toggle_opt_2"))
        print(t("toggle_opt_3"))
        print(t("toggle_opt_4"))
        print("-" * 55)

        val = input(t("prompt_choice")).strip().lower()
        if val in ("0", ""):
            break
        elif val == "all":
            cfg["enabled_games"] = list(GAMES.keys())
            save_hoyo_config(cfg)
            print(t("all_games_enabled"))
        elif val == "none":
            cfg["enabled_games"] = []
            save_hoyo_config(cfg)
            print(t("all_games_disabled"))
        elif val.isdigit() and 1 <= int(val) <= len(game_keys):
            target_key = game_keys[int(val) - 1]
            if target_key in enabled:
                enabled.remove(target_key)
                print(t("game_disabled", name=GAMES[target_key]['name']))
            else:
                enabled.add(target_key)
                print(t("game_enabled", name=GAMES[target_key]['name']))
            cfg["enabled_games"] = [gk for gk in game_keys if gk in enabled]
            save_hoyo_config(cfg)
        else:
            print(t("invalid_input"))

def menu_manage_scheduler():
    """Interactive submenu to install or remove auto check-in."""
    while True:
        is_active, desc = get_scheduler_status()
        print("\n" + "-" * 55)
        print(t("sched_menu_title", os=OS_NAME))
        print("-" * 55)
        print(t("sched_status", icon='🟢' if is_active else '⚪', desc=desc))
        print("\nOptions:")
        print(t("sched_opt_install"))
        print(t("sched_opt_remove"))
        print(t("sched_opt_back"))
        print("-" * 55)

        choice = input(t("sched_prompt")).strip()
        if choice == "1":
            install_scheduler()
        elif choice == "2":
            remove_scheduler()
        elif choice == "0":
            break
        else:
            print(t("invalid_input"))

def menu_login_options():
    """Interactive submenu for login."""
    print("\n" + "-" * 55)
    print(t("login_menu_title"))
    print("-" * 55)
    print(t("login_opt_auto"))
    print(t("login_opt_browser"))
    print(t("login_opt_manual"))
    print(t("login_opt_cancel"))
    print("-" * 55)

    choice = input(t("login_prompt")).strip()
    if choice == "1":
        cookie = auto_import_from_browser(save=True)
        if cookie:
            print(t("login_auto_success"))
            return cookie
        else:
            print(t("login_auto_none"))
    elif choice == "2":
        return interactive_browser_login()
    elif choice == "3":
        manual = input(t("paste_cookie")).strip()
        if manual:
            save_cookie_to_env(manual)
            print(t("cookie_saved_success"))
            return manual
    return None

def menu_language():
    """Interactive menu to select language (EN or ID)."""
    cfg = load_hoyo_config()
    current = cfg.get("language", "en")
    print("\n" + "-" * 55)
    print(t("lang_menu_title"))
    print("-" * 55)
    print(f"{t('lang_opt_en')}{'  👈' if current == 'en' else ''}")
    print(f"{t('lang_opt_id')}{'  👈' if current == 'id' else ''}")
    print(t("lang_opt_back"))
    print("-" * 55)

    choice = input(t("lang_prompt")).strip()
    if choice == "1":
        cfg["language"] = "en"
        save_hoyo_config(cfg)
        set_language("en")
        print(t("lang_saved", lang="English"))
    elif choice == "2":
        cfg["language"] = "id"
        save_hoyo_config(cfg)
        set_language("id")
        print(t("lang_saved", lang="Bahasa Indonesia"))

def interactive_hub():
    """Main interactive hub when running without arguments."""
    while True:
        cfg = load_hoyo_config()
        set_language(cfg.get("language", "en"))

        cookies, _ = get_cookies_from_env_or_config()
        cookie = cookies[0] if cookies else None

        print("\n" + "=" * 58)
        print(t("hub_title"))
        print("=" * 58)

        account_info = None
        if cookie:
            account_info, _ = run_with_progress(
                t("checking_session_progress"),
                lambda: check_account_status(cookie),
                timeout=6.0
            )
            if not account_info:
                account_info = {"valid": False, "uid": "Unknown", "games": {}}

            if account_info["valid"]:
                print(t("hub_account_logged", uid=account_info['uid']))
                print(t("hub_token_valid"))
                print(t("hub_today_status"))
                for gk, gres in account_info["games"].items():
                    name = GAMES[gk]["name"]
                    emoji = GAMES[gk]["emoji"]
                    if gres.get("status") == "ALREADY_CHECKED_IN":
                        badge = t("checked_in_badge", day=gres.get('days', 0))
                        print(f"   {emoji} {name:<21}: ✅ {badge}")
                    elif gres.get("status") == "DRY_RUN":
                        print(f"   {emoji} {name:<21}: 🟡 {t('ready_to_claim_badge')}")
                    else:
                        print(f"   {emoji} {name:<21}: ⚪ {gres.get('message', t('ready_badge'))}")
            else:
                print(t("hub_account_logged", uid=account_info['uid']))
                print(t("hub_token_expired"))
        else:
            print(t("hub_account_not_logged"))
            print(t("hub_no_credentials"))

        is_sched, sched_desc = get_scheduler_status()
        print(t("hub_auto_checkin", icon='🟢' if is_sched else '⚪', desc=sched_desc))
        print("=" * 58)

        # Dynamic Menu Options
        if not cookie or (account_info and not account_info["valid"]):
            print("╭" + "─" * 56 + "╮")
            print(f"│  {t('hub_warning_title'):<52} │")
            print(f"│  {t('hub_warning_desc1'):<52} │")
            print(f"│  {t('hub_warning_desc2'):<52} │")
            print("╰" + "─" * 56 + "╯\n")

            print(t("hub_no_login_opt_1"))
            print(t("hub_no_login_opt_2"))
            print(t("hub_no_login_opt_3"))
            print(t("hub_no_login_opt_4"))
            lang_label = "English" if CURRENT_LANG == "en" else "Bahasa Indonesia"
            print(f" [5] 🌐 Language / Bahasa (Current: {lang_label})")
            print(t("hub_no_login_opt_0"))
            print("=" * 58)

            choice = input(t("hub_no_login_prompt")).strip()
            if choice == "1":
                menu_login_options()
            elif choice == "2":
                menu_manage_scheduler()
            elif choice == "3":
                menu_toggle_games()
            elif choice == "4":
                check_for_updates(prompt_if_latest=True)
            elif choice == "5":
                menu_language()
            elif choice == "0":
                print(t("goodbye"))
                sys.exit(0)
        else:
            enabled_games = cfg.get("enabled_games", ["genshin", "starrail", "zzz", "honkai3rd", "themis", "hoyolab"])
            enabled_str = f"{len(enabled_games)}/{len(GAMES)} Active"

            print(t("hub_logged_opt_1"))
            print(t("hub_logged_opt_2"))
            print(t("hub_logged_opt_3", games=enabled_str))
            print(t("hub_logged_opt_4", os=OS_NAME))
            print(t("hub_logged_opt_5"))
            print(t("hub_logged_opt_6"))
            lang_label = "English" if CURRENT_LANG == "en" else "Bahasa Indonesia"
            print(f" [7] 🌐 Language / Bahasa (Current: {lang_label})")
            print(t("hub_logged_opt_0"))
            print("=" * 58)

            choice = input(t("hub_login_prompt")).strip()
            if choice == "1":
                run_checkin_batch([cookie], enabled_games, dry_run=False, verbose=True)
                input(t("press_enter_return"))
            elif choice == "2":
                run_checkin_batch([cookie], enabled_games, dry_run=True, verbose=True)
                input(t("press_enter_return"))
            elif choice == "3":
                menu_toggle_games()
            elif choice == "4":
                menu_manage_scheduler()
            elif choice == "5":
                menu_login_options()
            elif choice == "6":
                check_for_updates(prompt_if_latest=True)
            elif choice == "7":
                menu_language()
            elif choice == "0":
                print(t("goodbye"))
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
    parser.add_argument("--lang", "--language", choices=["en", "id"], help="Set UI language (en/id)")

    args = parser.parse_args()

    cfg = load_hoyo_config()
    if args.lang:
        set_language(args.lang)
    else:
        set_language(cfg.get("language", "en"))

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
            print(t("cli_no_cred"))
            sys.exit(1)

    games_to_run = cfg.get("enabled_games", ["genshin", "starrail", "zzz", "honkai3rd", "themis", "hoyolab"]) if args.game == "all" else [args.game]

    verbose = not (args.silent or args.cron)
    if verbose:
        print(t("cli_starting", time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    else:
        if not wait_for_internet(timeout=180, verbose=False):
            print(t("internet_wake_failed", timeout=180))
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
