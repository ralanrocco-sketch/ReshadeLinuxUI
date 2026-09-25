"""KDE-friendly, lightweight game picker and installer window."""
from pathlib import Path
from PySide6.QtCore import Qt,QProcess
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QComboBox,QFormLayout,QHBoxLayout,QInputDialog,QLabel,QListWidget,QListWidgetItem,QMainWindow,QMessageBox,QPushButton,QSplitter,QTextEdit,QVBoxLayout,QWidget
from proton.prefix import is_valid_prefix
from reshade.backup import restore_game_backups
from reshade.detector import MAIN_PATH,inspect_game
from reshade.installer import InstallerError,restore_backups,start_installer
from steam.detector import SteamGame,discover_games,steam_roots
from steam.games import find_executables,pe_architecture
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("ReShade Linux GUI"); self.resize(1000,690); self.setMinimumSize(760,520)
        self.games=[]; self.selected_game=None; self.reshade_dir=None; self.backups=[]; self.pending_action=None; self.pending_game_dir=None; self.pending_app_id=None; self.process=QProcess(self); self._build_ui()
        self.process.started.connect(self._send_script_input); self.process.readyReadStandardOutput.connect(self._read_output); self.process.readyReadStandardError.connect(self._read_error); self.process.finished.connect(self._finished); self.process.errorOccurred.connect(self._process_error); self.refresh_games()
    def _build_ui(self):
        root=QWidget(); outer=QVBoxLayout(root); outer.setContentsMargins(24,18,24,20); outer.setSpacing(14)
        top=QHBoxLayout(); title=QLabel("ReShade / Linux"); title.setFont(QFont("Noto Sans",19,QFont.DemiBold)); top.addWidget(title); top.addStretch(1)
        self.refresh_button=QPushButton("Rescan Steam"); self.refresh_button.clicked.connect(self.refresh_games); top.addWidget(self.refresh_button); outer.addLayout(top)
        intro=QLabel("Choose a Steam game. This app finds its install folder and Proton prefix for you."); intro.setObjectName("muted"); outer.addWidget(intro)
        splitter=QSplitter(Qt.Horizontal); self.game_list=QListWidget(); self.game_list.currentRowChanged.connect(self._select_game); self.game_list.setMinimumWidth(230); splitter.addWidget(self.game_list)
        detail=QWidget(); layout=QVBoxLayout(detail); layout.setContentsMargins(18,8,4,4); layout.setSpacing(12)
        self.game_title=QLabel("Select a game"); self.game_title.setFont(QFont("Noto Sans",16,QFont.DemiBold)); layout.addWidget(self.game_title)
        self.status=QLabel("Steam games will appear here."); self.status.setObjectName("status"); layout.addWidget(self.status)
        self.paths=QLabel(""); self.paths.setWordWrap(True); self.paths.setTextInteractionFlags(Qt.TextSelectableByMouse); self.paths.setObjectName("paths"); layout.addWidget(self.paths)
        form=QFormLayout(); self.dll_choice=QComboBox(); self.dll_choice.addItems(["dxgi (DirectX 10/11/12)","d3d9 (DirectX 9)","d3d11","ddraw","dinput8","opengl32 (OpenGL)","d3d8"]); form.addRow("DLL override",self.dll_choice); layout.addLayout(form)
        actions=QHBoxLayout(); self.install_button=QPushButton("Install ReShade"); self.install_button.setObjectName("primary"); self.install_button.clicked.connect(lambda:self._prepare_action("install"))
        self.uninstall_button=QPushButton("Uninstall"); self.uninstall_button.clicked.connect(lambda:self._prepare_action("uninstall")); actions.addWidget(self.install_button); actions.addWidget(self.uninstall_button); actions.addStretch(1); layout.addLayout(actions)
        layout.addWidget(QLabel("Activity")); self.log=QTextEdit(); self.log.setReadOnly(True); self.log.setMinimumHeight(145); self.log.setPlaceholderText("Installer progress and useful errors will appear here."); layout.addWidget(self.log,1)
        splitter.addWidget(detail); splitter.setStretchFactor(1,1); outer.addWidget(splitter,1); self.setCentralWidget(root)
        self.setStyleSheet("""QListWidget,QTextEdit{border:1px solid palette(mid);border-radius:6px;padding:6px} QListWidget::item{padding:9px 7px;border-radius:4px} QListWidget::item:selected{background:palette(highlight);color:palette(highlighted-text)} QPushButton,QComboBox{border:1px solid palette(mid);border-radius:5px;padding:7px 11px} QPushButton:hover{border-color:#83b94e} QPushButton#primary{background:#7ebf42;color:#10170d;border:0;font-weight:600} QLabel#muted,QLabel#paths{color:palette(mid)} QLabel#status{font-size:14px;font-weight:600;padding:8px 0}""")
    def refresh_games(self):
        self.refresh_button.setEnabled(False); self.game_list.clear(); self.paths.setText("Scanning Steam libraries…"); self.games=discover_games(); self.refresh_button.setEnabled(True)
        for game in self.games:
            item=QListWidgetItem(game.name); item.setData(Qt.UserRole,game.app_id); self.game_list.addItem(item)
        roots=steam_roots()
        if not self.games:
            self.game_title.setText("No installed Steam games found"); self.status.setText("Steam library not found" if not roots else "No installed games found in detected libraries"); self.paths.setText("Looked in standard Steam user locations. Rescan after Steam installs a game."); self.install_button.setEnabled(False); self.uninstall_button.setEnabled(False); return
        self.log.append(f"Found {len(self.games)} installed games in {len(roots)} Steam installation(s)."); self.game_list.setCurrentRow(0)
    def _select_game(self,row):
        if row<0 or row>=len(self.games): return
        game=self.games[row]; self.selected_game=game; self.reshade_dir=game.install_dir; status=inspect_game(game.install_dir)
        if status.state=="Not installed":
            for exe in find_executables(game.install_dir):
                candidate=inspect_game(exe.parent)
                if candidate.state!="Not installed": status=candidate; self.reshade_dir=exe.parent; break
        prefix_ok=is_valid_prefix(game.prefix); prefix=str(game.prefix) if game.prefix else "No Proton prefix found"
        self.game_title.setText(game.name); self.status.setText(f"ReShade: {status.state} — {status.detail}")
        self.paths.setText(f"Install folder: {game.install_dir}\nExecutable folder: {self.reshade_dir}\nProton prefix ({'Found' if prefix_ok else 'Not found'}): {prefix}\nSteam App ID: {game.app_id}")
        self.uninstall_button.setEnabled(status.state=="Installed" and bool(status.links)); self.install_button.setEnabled(prefix_ok)
    def _prepare_action(self,action):
        game=self.selected_game
        if not game: return
        executable=None; architecture=None; game_dir=self.reshade_dir or game.install_dir; dll=self.dll_choice.currentText().split(" ",1)[0]
        if action=="install":
            self.log.append(f"Finding Windows executables under {game.install_dir}…"); candidates=find_executables(game.install_dir)
            if not candidates: QMessageBox.warning(self,"No Windows executable found","This Steam install has no .exe files. The first version supports DirectX/OpenGL games using Proton."); return
            if len(candidates)==1: executable=candidates[0]
            else:
                labels=[str(p.relative_to(game.install_dir)) for p in candidates]; selection,ok=QInputDialog.getItem(self,"Choose game executable","Select the executable ReShade should be installed beside:",labels,0,False)
                if not ok: return
                executable=game.install_dir/selection
            game_dir=executable.parent; architecture=pe_architecture(executable)
            if architecture not in (32,64): QMessageBox.warning(self,"Unsupported executable","Could not read the selected executable's Windows architecture. No files were changed."); return
        inventory=self._inventory(game_dir,action,dll)
        message=(f"Game: {game.name}\nAction: {action.title()} ReShade\nSteam App ID: {game.app_id}\n\nExecutable folder:\n{game_dir}\n\nProton prefix (never deleted):\n{game.prefix or 'Not detected'}\n\nShared ReShade data directory:\n{MAIN_PATH}\n\nPaths and files that may change:\n{inventory}")
        if action=="install":
            backup_dir=Path(os.environ.get("XDG_DATA_HOME",Path.home()/".local/share"))/"reshade-linux-gui/backups"/game.app_id
            message+=f"\n\nSelected executable: {executable.name} ({architecture}-bit)\nDLL override: {dll}\nExisting conflicts will be backed up under:\n{backup_dir}\nThe upstream script may download or update shared ReShade and shader files."
        if QMessageBox.question(self,"Confirm ReShade changes",message,QMessageBox.Yes|QMessageBox.Cancel,QMessageBox.Cancel)!=QMessageBox.Yes: return
        try: self.backups=start_installer(self.process,game_dir,action,game.app_id,architecture,dll)
        except InstallerError as error: QMessageBox.critical(self,"Cannot start installer",str(error)); return
        self.pending_action=action; self.pending_game_dir=game_dir; self.pending_app_id=game.app_id
        self.install_button.setEnabled(False); self.uninstall_button.setEnabled(False); self.refresh_button.setEnabled(False); self.log.append(f"Starting upstream installer for {game.name}…")
    def _inventory(self,game_dir,action,dll):
        from reshade.detector import MANAGED_LINKS
        names=[f"{dll}.dll","d3dcompiler_47.dll","ReShade_shaders","ReShade.ini"] if action=="install" else list(MANAGED_LINKS)
        rows=[]
        for name in names:
            path=game_dir/name
            if path.is_symlink(): rows.append(f"• {name} symlink to {path.resolve(strict=False)}")
            elif path.exists(): rows.append(f"• {name} existing file/folder")
            else: rows.append(f"• {name} new link")
        if action=="uninstall": rows.append("• ReShade.log and ReShadePreset.ini are preserved")
        return "\n".join(rows)
    def _send_script_input(self):
        answers=self.process.property("reshade_input")
        if answers: self.process.write(str(answers).encode()); self.process.closeWriteChannel(); self.process.setProperty("reshade_input","")
    def _read_output(self): self._append_lines(bytes(self.process.readAllStandardOutput()).decode(errors="replace"))
    def _read_error(self): self._append_lines(bytes(self.process.readAllStandardError()).decode(errors="replace"))
    def _append_lines(self,raw):
        import re
        raw=re.sub(r"\x1b\[[0-9;]*[A-Za-z]","",raw)
        for line in raw.splitlines():
            text=line.strip()
            if not text: continue
            if "Downloading ReShade" in text or "Updating ReShade" in text: text="Downloading or updating ReShade files…"
            elif "Checking for ReShade Shader updates" in text: text="Checking shader repositories…"
            elif "Linking ReShade files" in text: text="Linking ReShade into the game folder…"
            elif "Could not download" in text or "Failed to" in text or "Error:" in text: text="Installer reported: "+text
            self.log.append(text)
    def _finished(self,code,_status):
        if code==0:
            self.log.append("Installer finished successfully.")
            if self.pending_action=="uninstall" and self.pending_app_id and self.pending_game_dir:
                restored=restore_game_backups(self.pending_app_id,self.pending_game_dir)
                if restored: self.log.append(f"Restored {len(restored)} original game file(s) from backup.")
            if self.backups: self.log.append(f"Conflicting original files are backed up under {self.backups[0][1].parent}")
        else:
            self.log.append(f"Installer exited with code {code}; see the messages above."); restore_backups(self.backups)
            if self.backups: self.log.append("Original files were restored where the destination was clear.")
        self.backups=[]; self.pending_action=None; self.refresh_button.setEnabled(True)
        if self.game_list.currentRow()>=0: self._select_game(self.game_list.currentRow())
    def _process_error(self,_error):
        restore_backups(self.backups); self.backups=[]; self.pending_action=None; self.log.append("Could not start installer. Restored original files from backup where possible."); self.refresh_button.setEnabled(True)
        if self.game_list.currentRow()>=0: self._select_game(self.game_list.currentRow())
