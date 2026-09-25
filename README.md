# ReShade Linux GUI

A small Python/PySide6 desktop frontend for the [reshade-steam-proton](https://github.com/kevinlekiller/reshade-steam-proton) installer. It discovers Steam games and Proton prefixes, asks which game executable to target, reviews paths and files with the user, then runs the bundled upstream script.

## SteamOS / AppImage

The intended end-user format is an x86_64 AppImage. It bundles Python, PySide6, the upstream installer, and the helper commands used by that installer. No Python setup or system package installation is needed on the Deck. Download the AppImage, mark it executable, and launch it from Desktop Mode.

AppImage normally uses FUSE. If that is unavailable, try running it with `--appimage-extract-and-run`. AppImages still use the host's core system libraries, so the image is built on Ubuntu 22.04 as a compatibility baseline and should be checked on SteamOS before release.

## Build the AppImage

The build uses PyInstaller and linuxdeploy. On an Ubuntu 22.04 x86_64 build host, install Python 3, pip, 7-Zip, curl, git, grep, file, and which; download the x86_64 linuxdeploy AppImage; then run:

    LINUXDEPLOY="$PWD/linuxdeploy-x86_64.AppImage" bash packaging/build-appimage.sh

A GitHub Actions workflow can build the image on a version tag or via manual dispatch. The workflow artifact is the AppImage. This build environment doesn't currently have PySide6, PyInstaller, or linuxdeploy installed, so an AppImage cannot be emitted locally until those build tools are available.

## Development

Use Python 3.10 or newer. Install PySide6 in a virtual environment, then launch:

    python3 -m venv .venv
    . .venv/bin/activate
    pip install -r requirements.txt
    python app.py

The upstream script also requires `7z`, `curl`, `git`, `grep`, `file`, and `which`. The app checks for them before starting an operation; it does not install system packages or require root.

## Current scope

- Detect common native, Snap, and Flatpak Steam locations and additional Steam libraries from `libraryfolders.vdf`.
- Read installed-game metadata from Steam app manifests, and look for the game's Proton prefix under `steamapps/compatdata/<AppID>/pfx`.
- Find Windows executables and read their PE architecture. When a game has multiple executables, ask which one ReShade should sit beside.
- Support the upstream script's DirectX/OpenGL install and uninstall flow. Vulkan is omitted because the upstream script marks it experimental and currently nonfunctional under Wine.
- Show the target game folder and prospective changes before asking for confirmation.
- Refuse to uninstall or replace symlinks that do not point into the shared ReShade data directory.
- Move conflicting files or directories into `$XDG_DATA_HOME/reshade-linux-gui/backups/<AppID>/` and restore them after uninstall when their original paths are free. The Proton prefix is never deleted.

The app supplies the upstream script's interactive answers through a `QProcess`; the script remains responsible for downloading ReShade and shaders and creating the game-folder links. Installer output is shown in the Activity area.

## Upstream script

The script in `scripts/reshade-steam-proton.sh` is vendored from Kevin L. Kille's repository. See [scripts/UPSTREAM.md](scripts/UPSTREAM.md) for provenance. Its license header is retained.
