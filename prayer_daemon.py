#!/usr/bin/env python3
# prayer_daemon.py - Background notification daemon for prayer times
import os, sys, json, time, signal, requests, subprocess
from datetime import datetime, date
import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify

CONFIG_DIR = os.path.expanduser("~/.config/prayer-times")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
PID_FILE = "/tmp/prayer_daemon.pid"
NOTIFIABLE = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
PRAYER_NAMES_AR = {"Fajr": "الفجر", "Dhuhr": "الظهر", "Asr": "العصر", "Maghrib": "المغرب", "Isha": "العشاء"}

def load_config():
    try:
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
            cfg.setdefault("adhan_enabled", True)
            cfg.setdefault("adhan_volume", 0.8)
            return cfg
    except:
        return {"city": "Fes", "method": 21, "notifications": True, "adhan_enabled": True, "adhan_volume": 0.8}

def parse_time(s):
    s = s.split(" ")[0]; h, m = map(int, s.split(":"))
    return datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)

def fetch_times(city, method):
    d = date.today()
    url = f"https://api.aladhan.com/v1/timingsByCity/{d.day:02d}-{d.month:02d}-{d.year}?city={city}&country=&method={method}"
    r = requests.get(url, timeout=10); r.raise_for_status()
    data = r.json()
    if data.get("code") != 200: raise ValueError(data.get("status", "خطأ API"))
    return data["data"]["timings"]

def format_time(dt):
    h, m = dt.hour, dt.minute
    return f"{h%12 or 12}:{m:02d} {'م' if h>=12 else 'ص'}"

def send_notification(prayer_key, time_str, city):
    try:
        n = Notify.Notification.new(f"🕌 حان وقت صلاة {PRAYER_NAMES_AR[prayer_key]}", f"الوقت: {time_str}" + (f" — {city}" if city else ""), "dialog-information")
        n.set_urgency(Notify.Urgency.NORMAL); n.show()
    except Exception as e: print(f"[daemon] Notification failed: {e}", file=sys.stderr)

def play_adhan(volume):
    adhan_path = os.path.join(CONFIG_DIR, "adhan.mp3")
    if not os.path.exists(adhan_path): return
    
    # Stop any currently playing instance to prevent overlap
    subprocess.run(["pkill", "-f", "paplay"], capture_output=True)
    
    vol_int = int(volume * 65536)
    subprocess.Popen(["paplay", "--volume", str(vol_int), adhan_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def run():
    try: Notify.init("مواقيت الصلاة (Daemon)")
    except Exception as e: print(f"[daemon] Notify init failed: {e}", file=sys.stderr); sys.exit(1)
    
    with open(PID_FILE, "w") as f: f.write(str(os.getpid()))
    def cleanup(signum, frame):
        if os.path.exists(PID_FILE): os.remove(PID_FILE)
        sys.exit(0)
    signal.signal(signal.SIGTERM, cleanup); signal.signal(signal.SIGINT, cleanup)
    
    cfg = load_config(); prayer_times = {}; notified_today = set(); last_date = date.today()
    def fetch_and_update():
        nonlocal prayer_times, notified_today, cfg
        try:
            timings = fetch_times(cfg["city"], cfg["method"])
            prayer_times = {k: parse_time(timings[k]) for k in NOTIFIABLE if k in timings}
            notified_today = set()
        except Exception as e: print(f"[daemon] Fetch error: {e}", file=sys.stderr)
    fetch_and_update(); print(f"[daemon] Running for {cfg['city']} | Method {cfg['method']}")
    
    while True:
        now = datetime.now()
        if now.date() != last_date:
            last_date = now.date(); cfg = load_config(); fetch_and_update(); time.sleep(10); continue
            
        # Reload config before checking to respect GUI toggle/volume changes
        cfg = load_config()
        
        for key in NOTIFIABLE:
            t = prayer_times.get(key)
            if not t or key in notified_today: continue
            if abs((t - now).total_seconds()) < 30:
                send_notification(key, format_time(t), cfg.get("city", ""))
                if cfg.get("adhan_enabled", True):
                    play_adhan(cfg.get("adhan_volume", 0.8))
                notified_today.add(key)
        time.sleep(10)

if __name__ == "__main__": run()