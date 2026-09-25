"""Create reversible user-space backups before an installer replaces paths."""
import json,os,shutil,uuid
from datetime import datetime
from pathlib import Path

def _backup_root(app_id:str)->Path:
    data_home=Path(os.environ.get("XDG_DATA_HOME",Path.home()/".local/share"))
    return data_home/"reshade-linux-gui/backups"/app_id

def backup_regular_files(paths:list[Path],app_id:str)->list[tuple[Path,Path]]:
    existing=[p for p in paths if p.exists() and not p.is_symlink()]
    if not existing: return []
    root=_backup_root(app_id)/(datetime.now().strftime("%Y%m%d-%H%M%S-%f")+"-"+uuid.uuid4().hex[:6]); moved=[]
    try:
        for source in existing:
            target=root/source.name; target.parent.mkdir(parents=True,exist_ok=True); shutil.move(str(source),str(target)); moved.append((source,target))
        (root/"manifest.json").write_text(json.dumps([{"original":str(a),"backup":str(b)} for a,b in moved],indent=2),encoding="utf-8")
        return moved
    except OSError:
        restore_backups(moved)
        raise

def restore_backups(items:list[tuple[Path,Path]])->None:
    for original,backup in reversed(items):
        if backup.exists() and not original.exists() and not original.is_symlink():
            original.parent.mkdir(parents=True,exist_ok=True); shutil.move(str(backup),str(original))

def restore_game_backups(app_id:str,game_dir:Path)->list[Path]:
    restored=[]; root=_backup_root(app_id)
    if not root.is_dir(): return restored
    for manifest in sorted(root.glob("*/manifest.json")):
        try: records=json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError,json.JSONDecodeError): continue
        for record in records:
            original=Path(record["original"]); backup=Path(record["backup"])
            try: original.relative_to(game_dir)
            except ValueError: continue
            try: backup.relative_to(root)
            except ValueError: continue
            if backup.exists() and not original.exists() and not original.is_symlink():
                original.parent.mkdir(parents=True,exist_ok=True); shutil.move(str(backup),str(original)); restored.append(original)
    return restored
