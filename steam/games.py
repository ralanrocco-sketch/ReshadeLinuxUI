"""Find Windows executables and read their PE architecture."""
import os,struct
from pathlib import Path
SKIP_DIRS={"_commonredist","redist","redistributables","easyanticheat","battleye","crashreports"}
def find_executables(game_dir: Path) -> list[Path]:
    results=[]
    for current,dirs,files in os.walk(game_dir,followlinks=False):
        dirs[:]=[n for n in dirs if n.casefold() not in SKIP_DIRS and not n.startswith(".")]
        results.extend(Path(current)/name for name in files if name.casefold().endswith(".exe"))
    return sorted(results,key=lambda p:(p.name.casefold(),len(p.parts),str(p).casefold()))
def pe_architecture(executable: Path) -> int | None:
    try:
        with executable.open("rb") as f:
            if f.read(2)!=b"MZ": return None
            f.seek(0x3c); offset=struct.unpack("<I",f.read(4))[0]; f.seek(offset)
            if f.read(4)!=b"PE\0\0": return None
            machine=struct.unpack("<H",f.read(2))[0]
        return {0x014c:32,0x8664:64,0xaa64:64}.get(machine)
    except (OSError,struct.error): return None
