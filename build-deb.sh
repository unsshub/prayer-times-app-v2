#!/usr/bin/env bash
set -e

# 📦 Package Configuration
PKG_NAME="prayer-times"
PKG_VERSION="1.0.0"
PKG_MAINTAINER="Your Name <your@email.com>"
BUILD_DIR="prayer-times-deb"

echo "📦 Building ${PKG_NAME}_${PKG_VERSION}_all.deb..."

# 1. Clean previous build
rm -rf "${BUILD_DIR}" "${PKG_NAME}_${PKG_VERSION}_all.deb"

# 2. Create directory structure
mkdir -p "${BUILD_DIR}"/{DEBIAN,usr/bin,usr/share/applications,usr/lib/systemd/user,usr/share/icons/hicolor/256x256/apps}

# 3. Check for source files
if [[ ! -f "prayer_times.py" || ! -f "prayer_daemon.py" ]]; then
    echo "❌ Error: prayer_times.py and prayer_daemon.py must be in the current directory."
    exit 1
fi

# 4. Copy scripts
cp prayer_times.py "${BUILD_DIR}/usr/bin/prayer-times-gui"
cp prayer_daemon.py "${BUILD_DIR}/usr/bin/prayer-times-daemon"
chmod +x "${BUILD_DIR}/usr/bin/"*

# 5. Download a default icon (or use your own)
echo "🎨 Downloading default icon..."
wget -q -O "${BUILD_DIR}/usr/share/icons/hicolor/256x256/apps/prayer-times.png" \
    "https://cdn-icons-png.flaticon.com/256/2316/2316795.png" || \
    echo "⚠️  Failed to download icon. Using fallback."

# 6. Create Desktop Entry
cat > "${BUILD_DIR}/usr/share/applications/prayer-times.desktop" << 'EOF'
[Desktop Entry]
Name=مواقيت الصلاة
Comment=Islamic Prayer Times, Countdown & Adhan Notifications
Exec=/usr/bin/prayer-times-gui
Icon=prayer-times
Terminal=false
Type=Application
Categories=Utility;Clock;Religion;
Keywords=Prayer;Islam;Adhan;Times;Notification;
EOF

# 7. Create Systemd User Service
cat > "${BUILD_DIR}/usr/lib/systemd/user/prayer-times-daemon.service" << 'EOF'
[Unit]
Description=Islamic Prayer Times Notification Daemon
After=default.target

[Service]
Type=simple
ExecStart=/usr/bin/prayer-times-daemon
Restart=on-failure
RestartSec=15
Environment=XDG_RUNTIME_DIR=%t

[Install]
WantedBy=default.target
EOF

# 8. Create DEBIAN Control File
cat > "${BUILD_DIR}/DEBIAN/control" << EOF
Package: ${PKG_NAME}
Version: ${PKG_VERSION}
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-gi, python3-requests, gir1.2-gtk-3.0, gir1.2-notify-0.7, gir1.2-appindicator3-0.1 | gir1.2-ayatanaappindicator3-0.1
Maintainer: ${PKG_MAINTAINER}
Description: Islamic Prayer Times Desktop App
 A fully-featured GTK3 app for daily prayer times, live countdown,
 4-stage smart notifications, Adhan audio with stop control,
 Hijri calendar, system tray integration, and a background
 systemd daemon for persistent alerts.
EOF

# 9. Create Post-Install Script (FIXED)
cat > "${BUILD_DIR}/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

# Reload systemd manager configuration
systemctl daemon-reload

# Enable the daemon for ALL users (Standard way for .deb packages)
systemctl --global enable prayer-times-daemon.service 2>/dev/null || true

# Refresh icon cache and desktop database
update-icon-caches /usr/share/icons/hicolor
update-desktop-database

echo ""
echo "✅ Installed successfully!"
echo "🚀 Launch from your app menu or run: prayer-times-gui"
echo "📜 The background daemon is enabled for all users."
echo ""
EOF

# 10. Create Pre-Removal Script
cat > "${BUILD_DIR}/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e
# Disable the daemon globally
systemctl --global disable prayer-times-daemon.service 2>/dev/null || true
systemctl daemon-reload
EOF

# Set permissions for DEBIAN scripts
chmod 0755 "${BUILD_DIR}/DEBIAN/"{postinst,prerm}

# 11. Build the package
dpkg-deb --build "${BUILD_DIR}" "${PKG_NAME}_${PKG_VERSION}_all.deb"

# 12. Cleanup
rm -rf "${BUILD_DIR}"

echo "🎉 Done! Package ready: ${PKG_NAME}_${PKG_VERSION}_all.deb"
