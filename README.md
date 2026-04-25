# 🕌 مواقيت الصلاة - Prayer Times Desktop App
[200~A beautiful Islamic prayer times application for Linux with notifications, Adhan audio, and system tray integration.

## ✨ Features

- **Live Prayer Times**: Fajr, Dhuhr, Asr, Maghrib, Isha + Sunrise
- **4-Stage Smart Notifications**: 
  - ⏳ 10 minutes before
  - 🕌 At prayer time
  - ✅ 5 minutes after
  - ✅ 15 minutes after
- **Adhan Audio**: Plays at prayer time with stop button
- **System Tray**: Minimize to tray, runs in background
- **Hijri Calendar**: Displays Islamic date
- **Custom Icon Packs**: 4 built-in themes
- **Background Daemon**: Notifications work even when app is closed
- **Desktop Integration**: Auto-start, custom shortcuts

## 📥 Installation

### For Debian/Ubuntu/Linux Mint:

```bash
# Download the .deb package
wget https://github.com/YOUR_USERNAME/prayer-times/releases/download/v1.0.0/prayer-times_1.0.0_all.deb

# Install
sudo dpkg -i prayer-times_1.0.0_all.deb
sudo apt install -f~

# Clone the repository
git clone https://github.com/YOUR_USERNAME/prayer-times.git
cd prayer-times

# Install dependencies
sudo apt install python3-gi python3-requests gir1.2-gtk-3.0 gir1.2-notify-0.7 gir1.2-appindicator3-0.1

# Run the app
python3 prayer_times.py

# Or build .deb package
./build-deb.sh
sudo dpkg -i prayer-times_1.0.0_all.deb

Usage

    Launch from menu: مواقيت الصلاة or run prayer-times-gui
    Enter your city name and click بحث (Search)
    Select calculation method
    Toggle notifications and Adhan audio
    Click X to minimize to system tray
    Right-click tray icon to restore or quit

🎨 Custom Icon Packs
The app includes 4 built-in icon themes:

    Emoji (Default): 🌙 🌅 ️ 🌤 🌆 🌃
    Minimalist: 🕋  🕛 🕒  🕘
    Nature: 🌌 🌅 🌞 🌇  🌃
    Classic Islamic: 🕌 🌄 ☀️ 🌤 🌅

⚙️ Configuration
Config file location: ~/.config/prayer-times/config.json
Adhan audio file: ~/.config/prayer-times/adhan.mp3
🛠️ Background Service
The daemon runs as a systemd user service:
# Check status
systemctl --user status prayer-times-daemon.service

# View logs
journalctl --user -u prayer-times-daemon.service -f

# Restart
systemctl --user restart prayer-times-daemon.service

Build from Source
# Build .deb package
./build-deb.sh

# Install
sudo dpkg -i prayer-times_1.0.0_all.deb

📄 License
This project is licensed under the MIT License - see the LICENSE
 file for details.
💬 Support
If you encounter any issues, please open an issue on GitHub.
Made with ❤️ for the Muslim community



