#!/bin/sh
set -eu
cd "$(dirname "$0")"
VERSION=3.1.34
rm -rf build dist
mkdir -p build/pkg/DEBIAN build/pkg/usr/share/lunatresor build/pkg/usr/share/doc/lunatresor build/pkg/usr/share/applications build/pkg/usr/bin dist
chmod 0755 build/pkg/DEBIAN
chmod g-s build/pkg/DEBIAN
cp main.py build/pkg/usr/share/lunatresor/main.py
cp README.md CHANGELOG.md LICENSE VERSION build/pkg/usr/share/doc/lunatresor/
cat > build/pkg/DEBIAN/control <<CONTROL
Package: lunatresor
Version: $VERSION
Section: utils
Priority: optional
Architecture: all
Depends: python3 (>= 3.11), python3-pyside6.qtwidgets, python3-pykeepass, python3-cryptography
Maintainer: LunaGPT <noreply@example.invalid>
Description: Local KeePass-compatible Qt password vault
 Local GUI for creating, opening and managing KDBX password vaults.
CONTROL
cat > build/pkg/usr/bin/lunatresor <<'LAUNCHER'
#!/bin/sh
exec python3 /usr/share/lunatresor/main.py "$@"
LAUNCHER
chmod 0755 build/pkg/usr/bin/lunatresor
chmod 0644 build/pkg/usr/share/lunatresor/main.py
cat > build/pkg/usr/share/applications/lunatresor.desktop <<'DESKTOP'
[Desktop Entry]
Version=1.0
Type=Application
Name=LunaTresor
Name[de]=LunaTresor
GenericName=Password Manager
GenericName[de]=Passwortmanager
Comment=KeePass-compatible password vault
Comment[de]=KeePass-kompatiblen Passworttresor verwalten
Exec=lunatresor
Icon=dialog-password
Terminal=false
Categories=Utility;Security;
StartupNotify=true
DESKTOP
chmod 0644 build/pkg/usr/share/applications/lunatresor.desktop
dpkg-deb --build --root-owner-group build/pkg "dist/lunatresor_${VERSION}_all.deb"
