"""Preflight and run the upstream interactive installer without a terminal."""
import os
import shutil
import sys
from pathlib import Path
from PySide6.QtCore import QProcess, QProcessEnvironment
from reshade.backup import backup_regular_files, restore_backups
from reshade.detector import MAIN_PATH, MANAGED_LINKS, OVERRIDE_DLLS, is_managed_link


class InstallerError(RuntimeError):
    pass


def script_path() -> Path:
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return bundle_root / "scripts" / "reshade-steam-proton.sh"


def _prompt_path(path: Path) -> str:
    value = str(path)
    if "\n" in value or "\r" in value:
        raise InstallerError("Game paths containing newline characters are not supported by the upstream script.")
    escaped = "".join("\\" + char if char in ('\\', '"', '$') or ord(char) == 96 else char for char in value)
    return '"' + escaped + '"'


def _uninstall_version(game_dir: Path) -> str:
    for name in OVERRIDE_DLLS:
        link = game_dir / name
        if not link.is_symlink():
            continue
        parts = link.resolve(strict=False).parts
        for index in range(len(parts) - 3, -1, -1):
            if parts[index] == "reshade" and index + 2 < len(parts):
                version = parts[index + 1]
                version_dir = MAIN_PATH / "reshade" / version
                if not (version_dir / "ReShade32.dll").is_file() or not (version_dir / "ReShade64.dll").is_file():
                    raise InstallerError(f"The cached ReShade version {version} is incomplete. Uninstall was stopped to avoid changing shared files.")
                return version
    raise InstallerError("Could not identify the cached ReShade version from this game's DLL link. No changes were made.")


def preflight(game_dir: Path, action: str, app_id: str, dll_override: str = "dxgi"):
    if not game_dir.is_dir():
        raise InstallerError(f"Game executable folder does not exist: {game_dir}")
    if action not in ("install", "uninstall"):
        raise InstallerError("Unsupported action.")
    names = [f"{dll_override}.dll", "d3dcompiler_47.dll", "ReShade_shaders", "ReShade.ini"] if action == "install" else (*MANAGED_LINKS, "ReShadePreset.ini")
    targets = [game_dir / name for name in names]
    unsafe = [path for path in targets if path.is_symlink() and not is_managed_link(path)]
    if unsafe:
        found = "\n".join(f"• {path.name} → {os.readlink(path)}" for path in unsafe)
        raise InstallerError("The installer would remove or replace links outside ReShade's shared data. No changes were made:\n" + found)
    try:
        backups = backup_regular_files(targets, app_id) if action == "install" else []
    except OSError as error:
        raise InstallerError(f"Could not back up an existing target: {error}") from error
    return targets, backups


def start_installer(process: QProcess, game_dir: Path, action: str, app_id: str, architecture: int | None = None, dll_override: str = "dxgi"):
    script = script_path()
    if not script.is_file():
        raise InstallerError(f"Bundled installer script is missing: {script}")
    missing = [name for name in ("bash", "7z", "curl", "git", "grep", "file", "which") if shutil.which(name) is None]
    if missing:
        raise InstallerError("Missing required command line tools: " + ", ".join(missing))
    if action == "install":
        if architecture not in (32, 64):
            raise InstallerError("Could not determine the selected executable's architecture.")
        if dll_override not in {"d3d8", "d3d9", "d3d11", "ddraw", "dinput8", "dxgi", "opengl32"}:
            raise InstallerError("Choose a supported ReShade DLL override.")
    version = _uninstall_version(game_dir) if action == "uninstall" else None
    quoted_path = _prompt_path(game_dir)
    _, backups = preflight(game_dir, action, app_id, dll_override)
    env = QProcessEnvironment.systemEnvironment()
    env.insert("MAIN_PATH", str(MAIN_PATH))
    env.insert("VULKAN_SUPPORT", "0")
    env.insert("DELETE_RESHADE_FILES", "0")
    if action == "uninstall":
        env.insert("UPDATE_RESHADE", "0")
        env.insert("SHADER_REPOS", " ")
        env.insert("MERGE_SHADERS", "0")
        env.insert("GLOBAL_INI", "0")
        env.insert("RESHADE_VERSION", version)
    if action == "install":
        answers = f"i\n{quoted_path}\ny\nn\n{architecture}\n{dll_override}\ny\n"
    elif action == "uninstall":
        answers = f"u\n{quoted_path}\ny\n"
    else:
        restore_backups(backups)
        raise InstallerError("Unsupported action.")
    process.setProgram("bash")
    process.setArguments([str(script)])
    process.setProcessEnvironment(env)
    process.setProperty("reshade_input", answers)
    process.start()
    return backups


__all__ = ["InstallerError", "preflight", "restore_backups", "start_installer"]
