Installation Guide
Prerequisites

    Python 3.6+
    Linux desktop environment (GNOME, KDE, XFCE, Cinnamon, MATE)
    Internet connection (for prayer times API)

Dependencies
sudo apt update
sudo apt install python3-gi python3-requests gir1.2-gtk-3.0 gir1.2-notify-0.7 gir1.2-appindicator3-0.1 pulseaudio-utils
Quick Install (Recommended)

    Download the latest .deb package from Releases
    Install:
sudo dpkg -i prayer-times_1.0.0_all.deb
sudo apt install -f
Enable background service:
systemctl --user daemon-reload
systemctl --user enable --now prayer-times-daemon.service
Launch the app:
prayer-times-gui
Install from Source

    Clone the repository:
git clone https://github.com/YOUR_USERNAME/prayer-times.git
cd prayer-times
Install dependencies (see above)
Run the app:
python3 prayer_times.py
Post-Installation

    Add Adhan Audio:
        Download an Adhan MP3 file
        Save it as ~/.config/prayer-times/adhan.mp3
    Auto-start on Login:
        The desktop entry is automatically created
        Or manually add to Startup Applications: prayer-times-gui
    Test Notifications:
        Open the app
        Click "🧪 اختبار" (Test)
        You should see a notification and hear Adhan

Troubleshooting
Daemon not starting:
systemctl --user status prayer-times-daemon.service
journalctl --user -u prayer-times-daemon.service -f
No sound:
# Test audio playback
paplay ~/.config/prayer-times/adhan.mp3

# Install audio utilities
sudo apt install pulseaudio-utils alsa-utils
Notifications not showing:
# Check if notification daemon is running
ps aux | grep notification-daemon
Uninstallation
# Remove package
sudo apt remove prayer-times

# Remove config files
rm -rf ~/.config/prayer-times

# Remove desktop entries
rm -f ~/.local/share/applications/prayer-times.desktop
rm -f ~/Desktop/prayer-times.desktop














