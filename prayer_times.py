#!/usr/bin/env python3
# مواقيت الصلاة — Linux Mint Desktop App
# Requirements: python3-gi, python3-requests, gir1.2-appindicator3-0.1
# sudo apt install python3-gi python3-requests gir1.2-gtk-3.0 gir1.2-notify-0.7 gir1.2-appindicator3-0.1

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')

AppIndicator3 = None
try:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3
except ValueError:
    try:
        gi.require_version('AyatanaAppIndicator3', '0.1')
        from gi.repository import AyatanaAppIndicator3 as AppIndicator3
    except ValueError:
        print("⚠️  Tray library not found. Install: sudo apt install gir1.2-appindicator3-0.1")

from gi.repository import Gtk, GLib, Gdk, Notify
import requests, threading, json, os, subprocess
from datetime import datetime, date

# ── Config & Constants ──────────────────────────────────────────────────────
APP_NAME   = "مواقيت الصلاة"
CONFIG_DIR = os.path.expanduser("~/.config/prayer-times")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
ADHAN_PATH = os.path.join(CONFIG_DIR, "adhan.mp3")

PRAYERS = [
    {"key": "Fajr",    "ar": "الفجر",   "emoji": "🌙"},
    {"key": "Sunrise", "ar": "الشروق",  "emoji": "🌅"},
    {"key": "Dhuhr",   "ar": "الظهر",   "emoji": "☀️"},
    {"key": "Asr",     "ar": "العصر",   "emoji": "🌤"},
    {"key": "Maghrib", "ar": "المغرب",  "emoji": "🌆"},
    {"key": "Isha",    "ar": "العشاء",  "emoji": "🌃"},
]
NOTIFIABLE = {"Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"}

# 🟢 PERMANENT 4-STAGE SCHEDULE
NOTIF_TRIGGERS = [
    {"id": "10_before", "offset_min": -10, "label": "⏳ تبقى 10 دقائق"},
    {"id": "now",       "offset_min": 0,   "label": "🕌 حان وقت الصلاة"},
    {"id": "5_after",   "offset_min": 5,   "label": "✅ مرت 5 دقائق منذ الأذان"},
    {"id": "15_after",  "offset_min": 15,  "label": "✅ انتهت الصلاة (مرت 15 دقيقة)"},
]

METHODS = [
    (21, "وزارة الأوقاف المغربية 🇲🇦"), (3, "رابطة العالم الإسلامي"),
    (4, "أم القرى — مكة المكرمة"), (5, "مصلحة الأفلاك المصرية"),
    (2, "ISNA — أمريكا الشمالية"), (16, "حكومة دولة الكويت"),
]

GOLD, DARK, TEXT, MUTED, GREEN, RED, PANEL = "#c9a84c", "#0d1b2a", "#f5ead0", "#8899aa", "#4caf82", "#e24b4a", "#112233"

CSS = f"""
* {{ font-family: 'Cairo', 'DejaVu Sans', sans-serif; }}
window {{ background-color: {DARK}; }}
#main-box {{ background-color: {DARK}; padding: 0px; }}
#header-box {{ background-color: {PANEL}; border-bottom: 1px solid rgba(201,168,76,0.25); padding: 18px 24px 14px 24px; }}
#app-title {{ color: {GOLD}; font-size: 24px; font-weight: bold; }}
#date-label {{ color: {MUTED}; font-size: 12px; }}
#city-entry {{ background-color: {PANEL}; color: {TEXT}; border: 1px solid rgba(201,168,76,0.3); border-radius: 10px; padding: 8px 14px; font-size: 14px; caret-color: {GOLD}; }}
#city-entry:focus {{ border-color: {GOLD}; }}
#search-btn {{ background-color: {GOLD}; color: {DARK}; border: none; border-radius: 10px; padding: 8px 18px; font-weight: bold; font-size: 13px; }}
#search-btn:hover {{ background-color: #f0d080; }}
#method-combo {{ background-color: {PANEL}; color: {TEXT}; border: 1px solid rgba(201,168,76,0.2); border-radius: 8px; font-size: 12px; }}
#next-box {{ background-color: rgba(201,168,76,0.08); border: 1px solid rgba(201,168,76,0.3); border-radius: 14px; padding: 16px; margin: 0px 16px 8px 16px; }}
#next-label-title {{ color: {MUTED}; font-size: 11px; }}
#next-prayer-name {{ color: {GOLD}; font-size: 22px; font-weight: bold; }}
#countdown-label {{ color: {TEXT}; font-size: 28px; font-weight: bold; font-family: monospace; }}
.prayer-row {{ background-color: {PANEL}; border-radius: 12px; border: 1px solid rgba(201,168,76,0.12); margin: 3px 16px; padding: 10px 16px; }}
.prayer-row-active {{ background-color: rgba(201,168,76,0.1); border-radius: 12px; border: 1px solid rgba(201,168,76,0.4); margin: 3px 16px; padding: 10px 16px; }}
.prayer-row-passed {{ background-color: rgba(17,34,51,0.5); border-radius: 12px; border: 1px solid rgba(201,168,76,0.05); margin: 3px 16px; padding: 10px 16px; opacity: 0.45; }}
#prayer-name-label {{ color: {TEXT}; font-size: 16px; font-weight: bold; }}
#prayer-time-label {{ color: {GOLD}; font-size: 17px; font-weight: bold; font-family: monospace; }}
#next-badge {{ background-color: {GOLD}; color: {DARK}; border-radius: 20px; padding: 1px 10px; font-size: 10px; font-weight: bold; }}
#status-label {{ color: {MUTED}; font-size: 14px; padding: 30px; }}
#error-label {{ color: {RED}; font-size: 13px; padding: 10px 16px; }}
#footer-label {{ color: rgba(136,153,170,0.5); font-size: 10px; padding: 8px; }}
#notif-toggle {{ background-color: transparent; color: {GOLD}; border: 1px solid {GOLD}; border-radius: 8px; padding: 4px 12px; font-size: 11px; }}
#stop-adhan-btn {{ background-color: {RED}; color: {DARK}; border: none; border-radius: 8px; padding: 4px 12px; font-size: 11px; font-weight: bold; }}
"""

# ── Helpers ──────────────────────────────────────────────────────────────────
def load_config():
    try:
        with open(CONFIG_FILE) as f: return json.load(f)
    except: return {"city": "Fes", "method": 21, "notifications": True}

def save_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f: json.dump(cfg, f)

def parse_time(s):
    s = s.split(" ")[0]; h, m = map(int, s.split(":"))
    return datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)

def format_time(dt):
    h, m = dt.hour, dt.minute
    return f"{h%12 or 12}:{m:02d} {'م' if h>=12 else 'ص'}"

def fetch_times(city, method):
    d = date.today()
    url = f"https://api.aladhan.com/v1/timingsByCity/{d.day:02d}-{d.month:02d}-{d.year}?city={city}&country=&method={method}"
    r = requests.get(url, timeout=10); r.raise_for_status()
    data = r.json()
    if data.get("code") != 200: raise ValueError(data.get("status", "خطأ"))
    return data["data"]["timings"]

# ── Main App ─────────────────────────────────────────────────────────────────
class PrayerApp(Gtk.Window):
    def __init__(self):
        super().__init__(title=APP_NAME)
        self.set_default_size(420, 680); self.set_resizable(True); self.set_border_width(0)
        
        self.cfg = load_config()
        self.prayer_times = {}
        self.notif_enabled = self.cfg.get("notifications", True)
        self.adhan_process = None
        self.hidden_to_tray = False
        
        # 🟢 4-Stage State
        self.notif_state = {}
        for p in PRAYERS:
            if p["key"] in NOTIFIABLE:
                self.notif_state[p["key"]] = {t["id"]: False for t in NOTIF_TRIGGERS}
                self.notif_state[p["key"]]["dismissed"] = False
                
        Notify.init(APP_NAME)
        provider = Gtk.CssProvider(); provider.load_from_data(CSS.encode())
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        self._build_ui()
        self._fetch(self.cfg.get("city", "Fes"), self.cfg.get("method", 21))
        GLib.timeout_add(1000, self._tick)
        self._schedule_midnight_refresh()
        self._setup_tray_icon()
        self.connect("delete-event", self._on_close_requested)

    def _build_ui(self):
        main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0); main.set_name("main-box"); self.add(main)
        self.daemon_running = os.path.exists("/tmp/prayer_daemon.pid")
        
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4); header.set_name("header-box"); header.set_halign(Gtk.Align.CENTER)
        header.pack_start(Gtk.Label(label="🕌"), False, False, 0)
        title = Gtk.Label(label="مواقيت الصلاة"); title.set_name("app-title"); header.pack_start(title, False, False, 0)
        self.date_lbl = Gtk.Label(label=self._get_date_str()); self.date_lbl.set_name("date-label"); header.pack_start(self.date_lbl, False, False, 2)
        main.pack_start(header, False, False, 0)

        ctrl = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        ctrl.set_margin_top(14); ctrl.set_margin_start(16); ctrl.set_margin_end(16); ctrl.set_margin_bottom(6)

        city_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.city_entry = Gtk.Entry(); self.city_entry.set_name("city-entry"); self.city_entry.set_placeholder_text("أدخل اسم المدينة...")
        self.city_entry.set_text(self.cfg.get("city", "Fes")); self.city_entry.connect("activate", self._on_search); self.city_entry.set_hexpand(True)
        search_btn = Gtk.Button(label="بحث"); search_btn.set_name("search-btn"); search_btn.connect("clicked", self._on_search)
        city_row.pack_start(self.city_entry, True, True, 0); city_row.pack_start(search_btn, False, False, 0)
        ctrl.pack_start(city_row, False, False, 0)

        bottom_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        method_store = Gtk.ListStore(int, str)
        for mid, mname in METHODS: method_store.append([mid, mname])
        self.method_combo = Gtk.ComboBox.new_with_model(method_store); self.method_combo.set_name("method-combo")
        renderer = Gtk.CellRendererText(); self.method_combo.pack_start(renderer, True); self.method_combo.add_attribute(renderer, "text", 1)
        for i, (mid, _) in enumerate(METHODS):
            if mid == self.cfg.get("method", 21): self.method_combo.set_active(i); break
        self.method_combo.connect("changed", self._on_method_changed); self.method_combo.set_hexpand(True)
        
        self.notif_btn = Gtk.Button(label="🔔 إشعارات" if self.notif_enabled else "🔕 إشعارات")
        self.notif_btn.set_name("notif-toggle"); self.notif_btn.connect("clicked", self._toggle_notif)
        
        # 🛑 STOP ADHAN BUTTON (Hidden by default, shows when playing)
        self.stop_adhan_btn = Gtk.Button(label="🛑 إيقاف الأذان")
        self.stop_adhan_btn.set_name("stop-adhan-btn")
        self.stop_adhan_btn.connect("clicked", self._stop_adhan)
        self.stop_adhan_btn.hide()
        
        bottom_row.pack_start(self.method_combo, True, True, 0)
        bottom_row.pack_start(self.notif_btn, False, False, 0)
        bottom_row.pack_start(self.stop_adhan_btn, False, False, 0)
        ctrl.pack_start(bottom_row, False, False, 0)

        # 🧪 TEST BUTTON
        self.test_btn = Gtk.Button(label="🧪 اختبار")
        self.test_btn.set_name("notif-toggle"); self.test_btn.connect("clicked", self._on_test)
        ctrl.pack_start(self.test_btn, False, False, 0)
        main.pack_start(ctrl, False, False, 0)

        self.error_lbl = Gtk.Label(label=""); self.error_lbl.set_name("error-label"); self.error_lbl.set_line_wrap(True); self.error_lbl.hide(); main.pack_start(self.error_lbl, False, False, 0)

        self.next_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4); self.next_box.set_name("next-box")
        self.next_box.pack_start(Gtk.Label(label="الصلاة القادمة"), False, False, 0)
        self.next_name_lbl = Gtk.Label(label="—"); self.next_name_lbl.set_name("next-prayer-name"); self.next_box.pack_start(self.next_name_lbl, False, False, 0)
        self.next_time_lbl = Gtk.Label(label=""); self.next_time_lbl.set_name("date-label"); self.next_box.pack_start(self.next_time_lbl, False, False, 2)
        self.countdown_lbl = Gtk.Label(label="--:--:--"); self.countdown_lbl.set_name("countdown-label"); self.next_box.pack_start(self.countdown_lbl, False, False, 0)
        self.next_box.hide(); main.pack_start(self.next_box, False, False, 8)

        scroll = Gtk.ScrolledWindow(); scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC); scroll.set_vexpand(True)
        self.prayers_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.status_lbl = Gtk.Label(label="🕋\nابحث عن مدينتك لعرض أوقات الصلاة"); self.status_lbl.set_name("status-label")
        self.prayers_box.pack_start(self.status_lbl, True, True, 0); scroll.add(self.prayers_box); main.pack_start(scroll, True, True, 0)

        daemon_status = Gtk.Label(label="الإشعارات تستمر حتى لو أغلقت التطبيق" if self.daemon_running else "لا توجد خدمة خلفية")
        daemon_status.set_name("footer-label"); main.pack_start(daemon_status, False, False, 0)
        footer = Gtk.Label(label="البيانات من AlAdhan API"); footer.set_name("footer-label"); main.pack_start(footer, False, False, 0)

    # 🖼️ Tray & Close Logic
    def _setup_tray_icon(self):
        if not AppIndicator3: return
        self.indicator = AppIndicator3.Indicator.new("prayer-times", "dialog-information", AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE); self.indicator.set_title(APP_NAME)
        menu = Gtk.Menu()
        self.show_item = Gtk.MenuItem(label="إظهار النافذة"); self.show_item.connect("activate", self._toggle_window_visibility); menu.append(self.show_item)
        menu.append(Gtk.SeparatorMenuItem())
        quit_item = Gtk.MenuItem(label="خروج كامل"); quit_item.connect("activate", self._quit_app); menu.append(quit_item)
        menu.show_all(); self.indicator.set_menu(menu)
        try: self.indicator.connect("activate", self._toggle_window_visibility)
        except: pass

    def _on_close_requested(self, widget, event):
        self.hide(); self.hidden_to_tray = True; self.show_item.set_label("إظهار النافذة"); return True

    def _toggle_window_visibility(self, *args):
        if self.get_visible(): self.hide(); self.hidden_to_tray = True; self.show_item.set_label("إظهار النافذة")
        else: self.show_all(); self.present(); self.hidden_to_tray = False; self.next_box.hide(); self.show_item.set_label("إخفاء النافذة")

    def _quit_app(self, *args): Gtk.main_quit()

    # 🎵 Adhan Playback & Stop Logic
    def _play_adhan(self):
        if not os.path.exists(ADHAN_PATH): return
        self._stop_adhan() # Kill previous if running
        try:
            self.adhan_process = subprocess.Popen(["paplay", "--volume=65536", ADHAN_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.stop_adhan_btn.show() # 🟢 Show stop button while playing
            GLib.timeout_add(500, self._check_adhan_finished)
        except Exception as e:
            try: self.adhan_process = subprocess.Popen(["aplay", ADHAN_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except: pass

    def _stop_adhan(self, *_):
        if self.adhan_process and self.adhan_process.poll() is None:
            self.adhan_process.terminate()
        self.adhan_process = None
        self.stop_adhan_btn.hide() # 🟢 Hide button when stopped

    def _check_adhan_finished(self):
        if self.adhan_process and self.adhan_process.poll() is not None:
            self.stop_adhan_btn.hide()
            return False
        return True

    def _on_test(self, *_):
        self._send_notification("وضع الاختبار", "✅ الصوت والإشعار يعملان", "الآن")
        self._play_adhan()

    # ── Date, Search & Fetch ────────────────────────────────────────────────
    def _get_date_str(self):
        now = datetime.now()
        return f"{['الاثنين','الثلاثاء','الأربعاء','الخميس','الجمعة','السبت','الأحد'][now.weekday()]} {now.day} {['يناير','فبراير','مارس','أبريل','ماي','يونيو','يوليوز','غشت','شتنبر','أكتوبر','نونبر','دجنبر'][now.month-1]} {now.year}"

    def _on_search(self, *_):
        city = self.city_entry.get_text().strip()
        if not city: return
        self._fetch(city, self._get_selected_method())
        if self.daemon_running: subprocess.run(["systemctl", "--user", "restart", "prayer-times-daemon"], capture_output=True)

    def _on_method_changed(self, *_):
        if self.city_entry.get_text().strip() and self.prayer_times: self._fetch(self.city_entry.get_text().strip(), self._get_selected_method())

    def _get_selected_method(self):
        idx = self.method_combo.get_active(); return METHODS[idx][0] if idx >= 0 else 21

    def _fetch(self, city, method):
        self._clear_prayers(); self.status_lbl.set_text("⏳  جاري التحميل..."); self.status_lbl.show(); self.error_lbl.hide(); self.next_box.hide()
        def worker():
            try: timings = fetch_times(city, method); GLib.idle_add(self._on_fetch_success, city, method, timings)
            except Exception as e: GLib.idle_add(self._on_fetch_error, str(e))
        threading.Thread(target=worker, daemon=True).start()

    def _on_fetch_success(self, city, method, timings):
        self.prayer_times = {}
        for p in PRAYERS:
            raw = timings.get(p["key"])
            if raw: self.prayer_times[p["key"]] = parse_time(raw)
        self.cfg.update({"city": city, "method": method}); save_config(self.cfg)
        # Reset 4-stage state
        for key in self.notif_state:
            for t_id in NOTIF_TRIGGERS: self.notif_state[key][t_id["id"]] = False
            self.notif_state[key]["dismissed"] = False
        self._render_prayers(); self.next_box.show(); self.status_lbl.hide(); return False

    def _on_fetch_error(self, msg):
        self.status_lbl.hide(); self.error_lbl.set_text("تعذّر الاتصال بالإنترنت" if "Connection" in msg or "timeout" in msg.lower() else f"⚠️  {msg}"); self.error_lbl.show(); return False

    # ── Render, Countdown & 4-Stage Notifications ────────────────────────────
    def _clear_prayers(self):
        for child in self.prayers_box.get_children():
            if child != self.status_lbl: self.prayers_box.remove(child)

    def _render_prayers(self):
        self._clear_prayers()
        now = datetime.now(); next_p = self._get_next_prayer()
        for p in PRAYERS:
            t = self.prayer_times.get(p["key"])
            if not t: continue
            is_next = next_p and next_p["key"] == p["key"]; is_passed = t < now
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
            if is_next: row.set_name("prayer-row-active"); row.get_style_context().add_class("prayer-row-active")
            elif is_passed: row.set_name("prayer-row-passed"); row.get_style_context().add_class("prayer-row-passed")
            else: row.set_name("prayer-row"); row.get_style_context().add_class("prayer-row")
            row.pack_start(Gtk.Label(label=p["emoji"] + "  "), False, False, 0)
            name_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            name_box.pack_start(Gtk.Label(label=p["ar"]), False, False, 0)
            if is_next: name_box.pack_start(Gtk.Label(label=" التالية "), False, False, 2)
            time_lbl = Gtk.Label(label=format_time(t)); time_lbl.set_name("prayer-time-label"); time_lbl.set_halign(Gtk.Align.END); time_lbl.set_hexpand(True)
            row.pack_start(name_box, False, False, 4); row.pack_start(time_lbl, True, True, 8)
            self.prayers_box.pack_start(row, False, False, 0)
        self.prayers_box.show_all() # ✅ Ensures prayer list is visible
        self._update_countdown()

    def _get_next_prayer(self):
        now = datetime.now()
        for p in PRAYERS:
            if p["key"] not in NOTIFIABLE: continue
            t = self.prayer_times.get(p["key"])
            if t and t > now: return {**p, "time": t}
        return None

    def _tick(self):
        if self.prayer_times: self._update_countdown(); self._check_notifications()
        return True

    def _update_countdown(self):
        next_p = self._get_next_prayer()
        if not next_p: self.next_name_lbl.set_text("انتهت صلوات اليوم"); self.countdown_lbl.set_text("—"); self.next_time_lbl.set_text(""); return
        now = datetime.now(); diff = int((next_p["time"] - now).total_seconds())
        if diff < 0: self._render_prayers(); return
        h, m, s = diff//3600, (diff%3600)//60, diff%60
        self.next_name_lbl.set_text(next_p["ar"]); self.next_time_lbl.set_text(f"الوقت: {format_time(next_p['time'])}"); self.countdown_lbl.set_text(f"{h:02d}:{m:02d}:{s:02d}")
        if diff == 0: self._render_prayers()

    def _check_notifications(self):
        if not self.notif_enabled: return
        now = datetime.now()
        for p in PRAYERS:
            if p["key"] not in NOTIFIABLE: continue
            if self.notif_state[p["key"]]["dismissed"]: continue
            t = self.prayer_times.get(p["key"]); 
            if not t: continue
            diff_min = (t - now).total_seconds() / 60.0
            for trigger in NOTIF_TRIGGERS:
                if self.notif_state[p["key"]][trigger["id"]]: continue
                if abs(diff_min - trigger["offset_min"]) <= 0.5:
                    self._send_notification(p["ar"], trigger["label"], format_time(t))
                    self._play_adhan()
                    self.notif_state[p["key"]][trigger["id"]] = True
                    break

    def _send_notification(self, prayer_name, trigger_label, time_str):
        city = self.cfg.get("city", "")
        n = Notify.Notification.new(f"🕌 {prayer_name} - {trigger_label}", f"الوقت: {time_str}" + (f" — {city}" if city else ""), "dialog-information")
        n.set_urgency(Notify.Urgency.NORMAL)
        n.add_action("dismiss_rest", "❌ إلغاء المتبقي", self._on_notif_action, prayer_name)
        n.connect("closed", self._on_notif_closed, prayer_name)
        try: n.show()
        except: pass

    def _on_notif_action(self, notification, action_id, prayer_key):
        self.notif_state[prayer_key]["dismissed"] = True; notification.close()

    def _on_notif_closed(self, notification, prayer_key):
        self.notif_state[prayer_key]["dismissed"] = True

    def _toggle_notif(self, *_):
        self.notif_enabled = not self.notif_enabled; self.cfg["notifications"] = self.notif_enabled; save_config(self.cfg)
        if self.daemon_running: subprocess.run(["systemctl", "--user", "restart", "prayer-times-daemon"], capture_output=True)
        self.notif_btn.set_label("🔔 إشعارات" if self.notif_enabled else "🔕 إشعارات")

    def _schedule_midnight_refresh(self):
        now = datetime.now(); tomorrow = now.replace(hour=0, minute=0, second=5, microsecond=0)
        from datetime import timedelta; tomorrow += timedelta(days=1)
        GLib.timeout_add(int((tomorrow - now).total_seconds() * 1000), self._midnight_refresh)

    def _midnight_refresh(self):
        self.date_lbl.set_text(self._get_date_str())
        for key in self.notif_state:
            self.notif_state[key]["dismissed"] = False
            for t_id in NOTIF_TRIGGERS: self.notif_state[key][t_id["id"]] = False
        self._fetch(self.city_entry.get_text().strip() or self.cfg.get("city", "Fes"), self._get_selected_method())
        self._schedule_midnight_refresh(); return False

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = PrayerApp(); app.connect("destroy", Gtk.main_quit); app.show_all(); app.next_box.hide(); Gtk.main()