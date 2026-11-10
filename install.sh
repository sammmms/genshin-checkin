#!/usr/bin/env bash
# ==============================================================================
# 🎮 HoYoLAB Check-In Hub One-Line Installer for macOS & Linux
# ==============================================================================
set -e

INSTALL_DIR="$HOME/.hoyolab-checkin"
BIN_DIR="$HOME/.local/bin"
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/checkin.py"
FALLBACK_URL="https://raw.githubusercontent.com/sammmms/hoyolab-checkin/main/checkin.py"

echo "======================================================="
echo "🎮 Installing HoYoLAB Daily Check-In Hub (hoyolab-checkin)..."
echo "======================================================="

# 1. Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

# 2. Copy checkin.py or download if running remotely
if [ -f "$SCRIPT_PATH" ]; then
    cp "$SCRIPT_PATH" "$INSTALL_DIR/checkin.py"
elif [ -f "checkin.py" ]; then
    cp checkin.py "$INSTALL_DIR/checkin.py"
else
    echo "⬇️  Mengunduh checkin.py..."
    curl -sSL "$FALLBACK_URL" -o "$INSTALL_DIR/checkin.py"
fi
chmod +x "$INSTALL_DIR/checkin.py"

# 3. Setup Shared Python Virtual Environment in ~/.automation-hub/venv
SHARED_HUB="$HOME/.automation-hub"
VENV_DIR="$SHARED_HUB/venv"
mkdir -p "$SHARED_HUB"

if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Membuat shared virtual environment di $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    echo "⬇️  Memasang pustaka pendukung (Playwright, Requests, Questionary, Pillow)..."
    "$VENV_DIR/bin/pip" install --upgrade pip >/dev/null 2>&1 || true
    "$VENV_DIR/bin/pip" install playwright requests questionary pillow >/dev/null 2>&1 || true
    echo "🌐 Mengunduh browser Chromium untuk Playwright..."
    "$VENV_DIR/bin/playwright" install chromium >/dev/null 2>&1 || true
fi

# Link to app dir for backward compatibility
ln -sfn "$VENV_DIR" "$INSTALL_DIR/venv"

# 4. Create executable wrapper in ~/.local/bin/hoyolab-checkin
WRAPPER_FILE="$BIN_DIR/hoyolab-checkin"
rm -f "$WRAPPER_FILE"
cat <<EOF > "$WRAPPER_FILE"
#!/usr/bin/env bash
exec "$VENV_DIR/bin/python" "$INSTALL_DIR/checkin.py" "\$@"
EOF
chmod +x "$WRAPPER_FILE"

# Clean up any old aliases if present
rm -f "$BIN_DIR/hoyolab" "$BIN_DIR/genshin-checkin"

# 5. Ensure ~/.local/bin is in PATH
CURRENT_SHELL="$(basename "$SHELL")"
PROFILE_FILE="$HOME/.zshrc"
[ "$CURRENT_SHELL" = "bash" ] && PROFILE_FILE="$HOME/.bashrc"

if ! grep -q "$BIN_DIR" "$PROFILE_FILE" 2>/dev/null; then
    echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$PROFILE_FILE"
    echo "ℹ️  Menambahkan $BIN_DIR ke $PROFILE_FILE"
fi

# 6. Setup macOS LaunchAgent with multi-interval wake-up catch-up
if [ "$(uname)" = "Darwin" ]; then
    PLIST_PATH="$HOME/Library/LaunchAgents/com.user.hoyolab-checkin.plist"
    cat <<EOF > "$PLIST_PATH"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.hoyolab-checkin</string>
    <key>ProgramArguments</key>
    <array>
        <string>$WRAPPER_FILE</string>
        <string>--silent</string>
    </array>
    <key>StartCalendarInterval</key>
    <array>
        <dict><key>Hour</key><integer>8</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Hour</key><integer>10</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Hour</key><integer>11</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Hour</key><integer>12</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Hour</key><integer>13</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Hour</key><integer>14</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Hour</key><integer>15</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Hour</key><integer>16</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Hour</key><integer>17</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Hour</key><integer>18</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Hour</key><integer>19</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Hour</key><integer>20</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Hour</key><integer>21</integer><key>Minute</key><integer>0</integer></dict>
    </array>
    <key>StandardOutPath</key>
    <string>$INSTALL_DIR/checkin.log</string>
    <key>StandardErrorPath</key>
    <string>$INSTALL_DIR/checkin.log</string>
</dict>
</plist>
EOF
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    launchctl load "$PLIST_PATH"
    echo "⏰ Jadwal harian otomatis terdaftar jam 08:00 pagi (dengan macOS wake-up catch-up)!"
fi

echo ""
echo "======================================================="
echo "✅ Instalasi Selesai!"
echo "👉 Sekarang Anda cukup ketik perintah ini di terminal:"
echo "   hoyolab-checkin"
echo "======================================================="
