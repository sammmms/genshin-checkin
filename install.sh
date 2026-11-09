#!/usr/bin/env bash
# ==============================================================================
# HoYoLAB Check-In One-Line Installer for macOS & Linux
# ==============================================================================
set -e

INSTALL_DIR="$HOME/.hoyolab-checkin"
BIN_DIR="$HOME/.local/bin"
SCRIPT_URL="https://raw.githubusercontent.com/sammmms/genshin-checkin/main/checkin.py"

echo "======================================================="
echo "🚀 Installing HoYoLAB Daily Check-In..."
echo "======================================================="

# 1. Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

# 2. Download or copy checkin.py
if [ -f "checkin.py" ]; then
    cp checkin.py "$INSTALL_DIR/checkin.py"
else
    echo "⬇️ Downloading script..."
    curl -sSL "$SCRIPT_URL" -o "$INSTALL_DIR/checkin.py"
fi

chmod +x "$INSTALL_DIR/checkin.py"
ln -sf "$INSTALL_DIR/checkin.py" "$BIN_DIR/hoyolab"
ln -sf "$INSTALL_DIR/checkin.py" "$BIN_DIR/genshin-checkin"
ln -sf "$INSTALL_DIR/checkin.py" "$BIN_DIR/hoyolab-checkin"

# 3. Add ~/.local/bin to PATH in shell profile if not present
CURRENT_SHELL="$(basename "$SHELL")"
PROFILE_FILE="$HOME/.zshrc"
[ "$CURRENT_SHELL" = "bash" ] && PROFILE_FILE="$HOME/.bashrc"

if ! grep -q "$BIN_DIR" "$PROFILE_FILE" 2>/dev/null; then
    echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$PROFILE_FILE"
    echo "ℹ️ Added ~/.local/bin to $PROFILE_FILE"
fi

# 4. Setup LaunchAgent on macOS
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
        <string>$BIN_DIR/hoyolab-checkin</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>$INSTALL_DIR/checkin.log</string>
    <key>StandardErrorPath</key>
    <string>$INSTALL_DIR/checkin.log</string>
</dict>
</plist>
EOF
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    launchctl load "$PLIST_PATH"
    echo "⏰ Daily schedule registered at 08:00 AM via macOS launchd!"
fi

echo ""
echo "======================================================="
echo "✅ Installation complete!"
echo "👉 Run login setup: hoyolab-checkin --login"
echo "======================================================="
