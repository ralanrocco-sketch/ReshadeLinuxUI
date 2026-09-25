"""Discover Steam installations, libraries, and installed game manifests."""
import os
from dataclasses import dataclass
from pathlib import Path
from steam.vdf import load
@dataclass(frozen=True)
class SteamGame:
    app_id: str
    name: str
    install_dir: Path
    library_dir: Path
    prefix: Path | None
def steam_roots() -> list[Path]:
    home=Path.home(); data=Path(os.environ.get("XDG_DATA_HOME",home/".local/share"))
    candidates=[data/"Steam",home/".steam/steam",home/".steam/root",home/".var/app/com.valvesoftware.Steam/data/Steam"]
    roots=[]; seen=set()
    for path in candidates:
        if path.is_dir() and path.resolve() not in seen:
            roots.append(path.resolve()); seen.add(path.resolve())
    return roots
def _library_paths(root: Path) -> list[Path]:
    paths=[root]
    for config in (root/"steamapps/libraryfolders.vdf",root/"config/libraryfolders.vdf"):
        if not config.is_file(): continue
        try: folders=load(config).get("libraryfolders",{})
        except (OSError,ValueError): continue
        if isinstance(folders,dict):
            for entry in folders.values():
                raw=entry.get("path") if isinstance(entry,dict) else entry
                if isinstance(raw,str) and Path(raw).expanduser().is_dir(): paths.append(Path(raw).expanduser().resolve())
    return list(dict.fromkeys(paths))
def discover_games() -> list[SteamGame]:
    games=[]; seen=set()
    for root in steam_roots():
        for library in _library_paths(root):
            apps=library/"steamapps"
            for manifest in apps.glob("appmanifest_*.acf"):
                try: data=load(manifest).get("AppState",{})
                except (OSError,ValueError): continue
                app_id=str(data.get("appid",manifest.stem.removeprefix("appmanifest_")))
                install_dir=apps/"common"/data.get("installdir","")
                if app_id in seen or not data.get("installdir") or not install_dir.is_dir(): continue
                seen.add(app_id)
                prefixes=(apps/"compatdata"/app_id/"pfx",root/"steamapps/compatdata"/app_id/"pfx")
                prefix=next((p.resolve() for p in prefixes if p.is_dir()),None)
                games.append(SteamGame(app_id,data.get("name","Unknown Steam game"),install_dir.resolve(),library,prefix))
    return sorted(games,key=lambda game:game.name.casefold())
