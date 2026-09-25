"""Inspect a game folder for links created by reshade-steam-proton."""
import os
from dataclasses import dataclass
from pathlib import Path
MAIN_PATH=Path(os.environ.get("XDG_DATA_HOME",Path.home()/".local/share"))/"reshade"
OVERRIDE_DLLS=("d3d8.dll","d3d9.dll","d3d11.dll","ddraw.dll","dinput8.dll","dxgi.dll","opengl32.dll")
MANAGED_LINKS=(*OVERRIDE_DLLS,"d3dcompiler_47.dll","ReShade.ini","ReShade32.json","ReShade64.json","Shaders","Textures","ReShade_shaders")
@dataclass(frozen=True)
class InstallStatus:
    state:str
    detail:str
    links:tuple[Path,...]
def is_managed_link(path:Path,main_path:Path=MAIN_PATH)->bool:
    if not path.is_symlink(): return False
    try:
        target=path.resolve(strict=False); base=main_path.resolve()
        return target==base or base in target.parents
    except OSError: return False
def inspect_game(game_dir:Path,main_path:Path=MAIN_PATH)->InstallStatus:
    links=tuple(game_dir/name for name in MANAGED_LINKS if (game_dir/name).is_symlink())
    owned=[path for path in links if is_managed_link(path,main_path)]
    dll_links=[path for path in owned if path.name in OVERRIDE_DLLS]
    complete=(len(owned)==len(links) and len(dll_links)==1 and
              is_managed_link(game_dir/"d3dcompiler_47.dll",main_path) and
              is_managed_link(game_dir/"ReShade_shaders",main_path))
    if not links: return InstallStatus("Not installed","No ReShade links found in the selected executable folder.",())
    if complete: return InstallStatus("Installed",f"Found {dll_links[0].name} and managed ReShade links.",tuple(owned))
    return InstallStatus("Needs review","Some expected files are missing or links do not point to shared ReShade data.",tuple(links))
