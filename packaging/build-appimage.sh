#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

: "${LINUXDEPLOY:-}"
if [[ -z "${LINUXDEPLOY:-}" || ! -x "$LINUXDEPLOY" ]]; then
    echo "Set LINUXDEPLOY to an executable linuxdeploy AppImage (with --output appimage support)." >&2
    exit 2
fi
for command in python3 pip; do
    command -v "$command" >/dev/null || { echo "Missing build command: $command" >&2; exit 2; }
done
for command in bash 7z curl git grep file; do
    command -v "$command" >/dev/null || { echo "Missing runtime helper to bundle: $command" >&2; exit 2; }
done

python3 -m pip install -r requirements.txt pyinstaller
python3 -m PyInstaller --noconfirm --clean ReShadeLinuxGUI.spec

APPDIR="$ROOT/AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/lib/reshade-linux-gui" "$APPDIR/usr/bin" "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/scalable/apps"
cp -a dist/ReShadeLinuxGUI/. "$APPDIR/usr/lib/reshade-linux-gui/"
for command in bash 7z curl git grep file; do
    cp -L "$(command -v "$command")" "$APPDIR/usr/bin/$command"
done
install -m 755 packaging/which "$APPDIR/usr/bin/which"
install -m 755 packaging/AppRun "$APPDIR/AppRun"
install -m 644 packaging/reshade-linux-gui.desktop "$APPDIR/usr/share/applications/reshade-linux-gui.desktop"
install -m 644 packaging/reshade-linux-gui.svg "$APPDIR/usr/share/icons/hicolor/scalable/apps/reshade-linux-gui.svg"
ln -sf usr/share/applications/reshade-linux-gui.desktop "$APPDIR/reshade-linux-gui.desktop"
ln -sf usr/share/icons/hicolor/scalable/apps/reshade-linux-gui.svg "$APPDIR/reshade-linux-gui.svg"
ARCH=x86_64 "$LINUXDEPLOY" --appdir "$APPDIR" --desktop-file "$APPDIR/usr/share/applications/reshade-linux-gui.desktop" --icon-file "$APPDIR/usr/share/icons/hicolor/scalable/apps/reshade-linux-gui.svg" --output appimage

shopt -s nullglob
images=("$ROOT"/*.AppImage)
output=""
for image in "${images[@]}"; do
    [[ "$(readlink -f "$image")" == "$(readlink -f "$LINUXDEPLOY")" ]] && continue
    output="$image"
done
if [[ -z "$output" ]]; then
    echo "linuxdeploy completed but did not create an AppImage in $ROOT." >&2
    exit 1
fi
mv -f "$output" "$ROOT/ReShade-Linux-GUI-x86_64.AppImage"
