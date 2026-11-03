#!/usr/bin/env python3
"""LunaTresor 3.0.0 - Qt Edition. KeePass-compatible KDBX frontend."""
import sys, os, json, time, csv, secrets, string, re, base64, hashlib
from pathlib import Path

try:
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    Scrypt = AESGCM = None
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QDialog,QVBoxLayout,QHBoxLayout,
    QGridLayout,QLabel,QPushButton,QLineEdit,QTextEdit,QComboBox,QTableWidget,QTableWidgetItem,
    QFileDialog,QMessageBox,QInputDialog,QSpinBox,QHeaderView,QFrame,QSplitter,QStatusBar,QMenu,QTreeWidget,QTreeWidgetItem)

try:
    from pykeepass import PyKeePass, create_database
except ImportError:
    PyKeePass = create_database = None

APP='LunaTresor'; VERSION='3.1.34'
if os.name == 'nt':
    _appdata = Path(os.environ.get('APPDATA') or (Path.home()/'AppData'/'Roaming'))
    CFG = _appdata/'LunaTresor'/'settings.json'
else:
    _config_home = Path(os.environ.get('XDG_CONFIG_HOME') or (Path.home()/'.config'))
    CFG = _config_home/'lunatresor'/'settings.json'

DARK = """
QMainWindow,QDialog { background:#080b20; color:#f5f3ff; }
QWidget { color:#f5f3ff; font-family:'Noto Sans'; font-size:10pt; }
QFrame#panel { background:#111633; border:1px solid #5367c2; border-radius:14px; }
QFrame#metric { background:#19254d; border:1px solid #5367c2; border-radius:14px; }
QLabel#brand { color:#e9d5ff; font-size:25pt; font-weight:700; }
QLabel#muted { color:#b9c6e8; }
QPushButton { background:#202d5d; border:1px solid #5367c2; border-radius:12px; padding:10px 14px; font-weight:600; }
QPushButton:hover { background:#304477; border-color:#8b9cff; }
QPushButton:pressed { background:#3c2672; }
QPushButton#accent { background:#8428ec; border:1px solid #ed8bff; color:white; }
QPushButton#accent:hover { background:#a33df0; }
QPushButton#danger { background:#642449; border-color:#ff83bd; }
QLineEdit,QTextEdit,QComboBox,QSpinBox { background:#202d5d; border:1px solid #5367c2; border-radius:9px; padding:8px; selection-background-color:#6927b8; }
QTableWidget { background:#0e1735; alternate-background-color:#121d3d; gridline-color:#26365f; border:1px solid #5367c2; border-radius:10px; }
QHeaderView::section { background:#1a2852; color:#e8eaff; padding:10px 7px; border:0; font-weight:700; }
QTableWidget::item { padding:7px; }
QTableWidget::item:selected { background:#6927b8; }
QMenu { background:#111633; border:1px solid #5367c2; }
QMenu::item:selected { background:#6927b8; }
QStatusBar { color:#b9c6e8; }
"""
LIGHT = """
QMainWindow,QDialog { background:#f1f4fa; color:#26344f; }
QWidget { color:#26344f; font-family:'Noto Sans'; font-size:10pt; }
QFrame#panel { background:#f8faff; border:1px solid #9eacc5; border-radius:14px; }
QFrame#metric { background:#e8eef8; border:1px solid #9eacc5; border-radius:14px; }
QLabel#brand { color:#55318e; font-size:25pt; font-weight:700; }
QLabel#muted { color:#62718b; }
QPushButton { background:#e4eaf6; border:1px solid #9eacc5; border-radius:12px; padding:10px 14px; font-weight:600; }
QPushButton:hover { background:#d4def0; }
QPushButton#accent { background:#6d28d9; border:1px solid #8b5cf6; color:white; }
QPushButton#danger { background:#fce7f3; border-color:#d68aaa; color:#9d174d; }
QLineEdit,QTextEdit,QComboBox,QSpinBox { background:#f7f9fd; border:1px solid #9eacc5; border-radius:9px; padding:8px; selection-background-color:#dcd2f5; }
QTableWidget { background:#fbfcff; alternate-background-color:#f0f3fa; gridline-color:#d5deed; border:1px solid #9eacc5; border-radius:10px; }
QHeaderView::section { background:#e3e9f5; color:#263653; padding:10px 7px; border:0; font-weight:700; }
QTableWidget::item { padding:7px; }
QTableWidget::item:selected { background:#dcd2f5; color:#35245c; }
QMenuBar { background:#e3e9f5; color:#263653; border-bottom:1px solid #9eacc5; spacing:6px; padding:4px 6px; }
QMenuBar::item { background:transparent; color:#263653; padding:6px 10px; border-radius:5px; }
QMenuBar::item:selected { background:#d4def0; color:#17243d; }
QMenuBar::item:pressed { background:#c5d2e8; color:#17243d; }
QMenu { background:#f8faff; color:#263653; border:1px solid #9eacc5; }
QMenu::item { color:#263653; padding:6px 22px; }
QMenu::item:selected { background:#dcd2f5; color:#35245c; }
QStatusBar { color:#62718b; }
"""

class EntryDialog(QDialog):
    def __init__(self, parent, groups, entry=None, lang='de'):
        super().__init__(parent); self.setWindowTitle('Eintrag bearbeiten' if entry else 'Neuer Eintrag')
        self.resize(520,420); self.values={}
        de=lang=='de'; labels=['Titel','Benutzername','Passwort','Webseite','Gruppe','Notizen'] if de else ['Title','Username','Password','Website','Group','Notes']
        form=QGridLayout(self); defaults=[getattr(entry,'title','') or '',getattr(entry,'username','') or '',getattr(entry,'password','') or '',getattr(entry,'url','') or '',parent.group_path(entry.group) if entry else (groups[0] if groups else 'Allgemein'),getattr(entry,'notes','') or '']
        for i,(label,value) in enumerate(zip(labels,defaults)):
            row_index = i if i < 3 else i + 1  # reserve a visible row for live password quality
            form.addWidget(QLabel(label),row_index,0)
            if i==5: w=QTextEdit(); w.setPlainText(value); w.setMinimumHeight(90)
            elif i==4:
                w=QComboBox(); w.addItems(groups or ['Allgemein']); w.setCurrentText(value)
                add_group=QPushButton('+ Neue Gruppe' if de else '+ New group')
                add_group.clicked.connect(lambda _, combo=w: self.create_group(parent, combo, de))
                group_row=QHBoxLayout(); group_row.addWidget(w,1); group_row.addWidget(add_group)
                form.addLayout(group_row,row_index,1)
            else: w=QLineEdit(value)
            if i==2:
                w.setEchoMode(QLineEdit.Password)
                show=QPushButton('Anzeigen' if de else 'Show')
                show.clicked.connect(lambda _,x=w:x.setEchoMode(QLineEdit.Normal if x.echoMode()==QLineEdit.Password else QLineEdit.Password))
                gen=QPushButton('Generieren' if de else 'Generate'); gen.clicked.connect(lambda _,x=w,p=parent:x.setText(p.make_password()))
                password_row=QHBoxLayout(); password_row.addWidget(w,1); password_row.addWidget(show); password_row.addWidget(gen); form.addLayout(password_row,row_index,1)
                self.strength_label=QLabel('Passwortstärke: –' if de else 'Password strength: –')
                self.strength_label.setObjectName('muted')
                form.addWidget(self.strength_label,3,1)
                def update_strength(text):
                    if not text:
                        self.strength_label.setText(('Passwortstärke: –' if de else 'Password strength: –'))
                        return
                    level, quality = parent.strength(text)
                    prefix = 'Passwortstärke: ' if de else 'Password strength: '
                    self.strength_label.setText(prefix + quality)
                w.textChanged.connect(update_strength)
                update_strength(value)
            elif i!=4: form.addWidget(w,row_index,1)
            self.values[label]=w
        buttons=QHBoxLayout(); buttons.addStretch()
        cancel=QPushButton('Abbrechen' if de else 'Cancel'); save=QPushButton('Speichern' if de else 'Save'); save.setObjectName('accent')
        cancel.clicked.connect(self.reject); save.clicked.connect(self.accept); buttons.addWidget(cancel); buttons.addWidget(save); form.addLayout(buttons,7,0,1,2)
    def create_group(self, parent, combo, de):
        if not getattr(parent,'kp',None):
            QMessageBox.information(self,'LunaTresor','Bitte zuerst einen Tresor öffnen.' if de else 'Please open a vault first.')
            return
        name,ok=QInputDialog.getText(self,'LunaTresor','Name der neuen Gruppe:' if de else 'Name of new group:')
        name=name.strip()
        if not ok or not name:
            return
        if '/' in name or any(g.name.casefold()==name.casefold() for g in parent.kp.root_group.subgroups):
            QMessageBox.warning(self,'LunaTresor','Diese Gruppe existiert bereits oder der Name ist ungültig.' if de else 'This group already exists or the name is invalid.')
            return
        try:
            parent.kp.add_group(parent.kp.root_group,name)
            parent.kp.save()
            current=combo.currentText()
            combo.clear(); combo.addItems(parent.groups())
            combo.setCurrentText(name)
        except Exception as ex:
            QMessageBox.critical(self,'LunaTresor',str(ex))
    def data(self):
        vals=list(self.values.values())
        return [vals[0].text().strip(),vals[1].text().strip(),vals[2].text(),vals[3].text().strip(),vals[4].currentText(),vals[5].toPlainText() if isinstance(vals[5],QTextEdit) else vals[5].text()]

class Main(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle(f'{APP} {VERSION} – Qt Edition'); self.resize(1242,820); self.setMinimumSize(944,650)
        try: self.cfg=json.loads(CFG.read_text())
        except Exception: self.cfg={}
        self.lang=self.cfg.get('language','de'); self.theme=self.cfg.get('theme','dark'); self.folders=self.cfg.get('folders',[]); self.pin_blob=self.cfg.get('pin_blob'); self.idle_lock_minutes=int(self.cfg.get('idle_lock_minutes',10)); self.master_password=None; self.clip_value=None
        self.kp=None; self.path=None; self.show_pw=False; self.last_activity=time.monotonic()
        self.build_ui(); self.apply_theme(); self.scan_vaults()
        self.idle=QTimer(self); self.idle.timeout.connect(self.check_idle); self.idle.start(1000)
        QApplication.instance().installEventFilter(self)
    def tr(self,de,en): return de if self.lang=='de' else en
    def ask_yes_no(self, title, message, parent=None):
        box=QMessageBox(parent or self)
        box.setIcon(QMessageBox.Question)
        box.setWindowTitle(title)
        box.setText(message)
        yes=box.addButton(self.tr('Ja','Yes'),QMessageBox.YesRole)
        no=box.addButton(self.tr('Nein','No'),QMessageBox.NoRole)
        box.setDefaultButton(no)
        box.exec()
        return box.clickedButton() is yes

    def password_prompt(self, title, label):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout(dialog)
        field_label = QLabel(label)
        edit = QLineEdit()
        edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(field_label)
        layout.addWidget(edit)
        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton(self.tr('Abbrechen','Cancel'))
        accept = QPushButton(self.tr('OK','OK'))
        accept.setObjectName('accent')
        buttons.addWidget(cancel)
        buttons.addWidget(accept)
        layout.addLayout(buttons)
        cancel.clicked.connect(dialog.reject)
        accept.clicked.connect(dialog.accept)
        edit.returnPressed.connect(dialog.accept)
        edit.setFocus()
        if dialog.exec() == QDialog.Accepted:
            return edit.text(), True
        return '', False
    def save_cfg(self):
        data = dict(getattr(self, 'cfg', {}) or {})
        data.update({
            'language': self.lang,
            'theme': self.theme,
            'folders': self.folders,
            'idle_lock_minutes': self.idle_lock_minutes,
            'pin_blob': self.pin_blob,
        })
        CFG.parent.mkdir(parents=True, exist_ok=True)
        tmp = CFG.with_suffix('.json.tmp')
        tmp.write_text(json.dumps(data, indent=2), encoding='utf-8')
        if os.name != 'nt':
            os.chmod(tmp, 0o600)
        os.replace(tmp, CFG)
        # Verify the value actually reached the expected config file.
        check = json.loads(CFG.read_text(encoding='utf-8'))
        if check.get('pin_blob') != self.pin_blob:
            raise OSError('PIN-Datensatz konnte nicht verifiziert werden.')
        self.cfg = data

    def touch(self,*a): self.last_activity=time.monotonic()
    def eventFilter(self,obj,event):
        try:
            if event.type() in (QEvent.MouseButtonPress,QEvent.MouseButtonRelease,QEvent.MouseMove,QEvent.KeyPress,QEvent.KeyRelease,QEvent.Wheel):
                self.last_activity=time.monotonic()
        except Exception: pass
        return super().eventFilter(obj,event)
    def event(self,e):
        try:
            if e.type() in (2,3,5,6): self.last_activity=time.monotonic()
        except Exception: pass
        return super().event(e)
    def check_idle(self):
        limit=int(self.idle_lock_minutes)
        # Do not lock while a password prompt, editor, or other modal dialog is active.
        if QApplication.activeModalWidget() is not None: return
        if self.kp and limit>0 and time.monotonic()-self.last_activity>limit*60: self.lock()
    def build_ui(self):
        root=QWidget(); self.setCentralWidget(root); outer=QVBoxLayout(root); outer.setContentsMargins(16,14,16,10); outer.setSpacing(12)
        header=QFrame(); header.setObjectName('panel'); h=QHBoxLayout(header)
        title=QVBoxLayout(); brand=QLabel('◇ LunaTresor'); brand.setObjectName('brand'); sub=QLabel('KDBX-Passworttresor  •  Qt Edition'); sub.setObjectName('muted'); title.addWidget(brand); title.addWidget(sub); h.addLayout(title); h.addStretch()
        self.new_btn=QPushButton(self.tr('+ Neuen Tresor erstellen…','+ Create new vault…')); self.new_btn.setObjectName('accent'); self.new_btn.clicked.connect(self.new_vault); h.addWidget(self.new_btn)
        gen=QPushButton(self.tr('Passwortgenerator','Password generator')); gen.clicked.connect(self.generator); h.addWidget(gen); outer.addWidget(header)
        metrics=QHBoxLayout(); self.m_vault=self.metric(metrics,self.tr('Gefundene Tresore','Found vaults'),'0'); self.m_entries=self.metric(metrics,self.tr('Gespeicherte Einträge','Saved entries'),'0'); self.m_state=self.metric(metrics,self.tr('Tresorstatus','Vault status'),self.tr('Nicht geöffnet','Not open')); outer.addLayout(metrics)
        splitter=QSplitter(); left=QFrame(); left.setObjectName('panel'); lv=QVBoxLayout(left); lv.addWidget(QLabel(self.tr('Tresore','Vaults')))
        self.vault_list=QTableWidget(0,1); self.vault_list.setMinimumWidth(245); self.vault_list.horizontalHeader().hide(); self.vault_list.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch); self.vault_list.verticalHeader().hide(); self.vault_list.setSelectionBehavior(QTableWidget.SelectRows); self.vault_list.cellDoubleClicked.connect(lambda *_: self.open_selected()); lv.addWidget(self.vault_list,1)
        for text,fn in [(self.tr('Tresor öffnen','Open vault'),self.open_selected),(self.tr('Ordner hinzufügen','Add folder'),self.add_folder),(self.tr('Ordner entfernen','Remove folder'),self.remove_folder),(self.tr('Jetzt suchen','Scan now'),self.scan_vaults)]:
            b=QPushButton(text); b.clicked.connect(fn); lv.addWidget(b)
        right=QWidget(); rv=QVBoxLayout(right); top=QHBoxLayout(); top.addWidget(QLabel(self.tr('Einträge','Entries'))); top.addStretch(); self.search=QLineEdit(); self.search.setPlaceholderText(self.tr('Einträge durchsuchen…','Search entries…')); self.search.textChanged.connect(self.refresh); self.search.setMaximumWidth(380); top.addWidget(self.search); rv.addLayout(top)
        self.table=QTableWidget(0,9); self.table.setHorizontalHeaderLabels(['★',self.tr('Gruppe','Group'),self.tr('Titel','Title'),self.tr('Benutzername','Username'),self.tr('Passwort','Password'),self.tr('Qualität','Strength'),self.tr('Geändert','Changed'),self.tr('Webseite','Website'),self.tr('Notiz','Notes')]); self.table.setSelectionBehavior(QTableWidget.SelectRows); self.table.setEditTriggers(QTableWidget.NoEditTriggers); self.table.setAlternatingRowColors(True); self.table.verticalHeader().hide(); self.table.setWordWrap(False); self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded); self.table.horizontalHeader().setMinimumSectionSize(10); self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Fixed); self.table.setColumnWidth(0,23); self.table.horizontalHeader().setSectionResizeMode(3,QHeaderView.Fixed); self.table.setColumnWidth(3,118); self.table.horizontalHeader().setSectionResizeMode(4,QHeaderView.Fixed); self.table.setColumnWidth(4,84); self.table.horizontalHeader().setStretchLastSection(False); rv.addWidget(self.table,1)
        actions=QHBoxLayout()
        for text,fn,obj in [(self.tr('+ Neu','+ New'),self.add_entry,'accent'),(self.tr('Bearbeiten','Edit'),self.edit_entry,''),(self.tr('Löschen','Delete'),self.delete_entry,'danger'),(self.tr('Favorit umschalten','Toggle favorite'),self.favorite,''),(self.tr('Passwörter zeigen/verbergen','Show/hide passwords'),self.toggle_passwords,''),(self.tr('Passwort kopieren','Copy password'),self.copy_password,'')]:
            b=QPushButton(text); b.setObjectName(obj); b.clicked.connect(fn); actions.addWidget(b)
        rv.addLayout(actions); splitter.addWidget(left); splitter.addWidget(right); splitter.setSizes([285,940]); outer.addWidget(splitter,1)
        self.summary=QLabel(self.tr('Sicherheitsübersicht: Tresor öffnen','Security overview: open a vault')); self.summary.setObjectName('muted'); outer.addWidget(self.summary)
        self.statusBar().showMessage(f'LunaTresor {VERSION} • Qt Edition')
        bar=self.menuBar(); file=bar.addMenu(self.tr('Datei','File'))
        for text,fn in [(self.tr('Neuen Tresor anlegen…','Create new vault…'),self.new_vault),(self.tr('Tresor öffnen…','Open vault…'),self.open_vault),(self.tr('CSV importieren…','Import CSV…'),self.import_csv),(self.tr('CSV exportieren…','Export CSV…'),self.export_csv),(self.tr('Verschlüsselt exportieren…','Encrypted export…'),self.export_ltx),(self.tr('Verschlüsselten Export importieren…','Import encrypted export…'),self.import_ltx),(self.tr('Beenden','Exit'),self.close)]: a=QAction(text,self); a.triggered.connect(fn); file.addAction(a)
        appearance=bar.addMenu(self.tr('Darstellung','Appearance'))
        for label,theme in [('Dunkel','dark'),('Hell','light')]:
            a=QAction(self.tr(label,'Dark' if theme=='dark' else 'Light'),self); a.triggered.connect(lambda _,t=theme:self.set_theme(t)); appearance.addAction(a)
        settings=bar.addMenu(self.tr('Einstellungen','Settings')); sec=QAction(self.tr('Sicherheit…','Security…'),self); sec.triggered.connect(self.security_settings); settings.addAction(sec); lang=settings.addMenu(self.tr('Sprache','Language'))
        for label,code in [('Deutsch','de'),('English','en')]:
            a=QAction(label,self); a.triggered.connect(lambda _,c=code:self.set_language(c)); lang.addAction(a)
        lock=QAction(self.tr('Tresor sperren','Lock vault'),self); lock.triggered.connect(self.lock); settings.addAction(lock)
        info=QAction('ⓘ  '+self.tr('Info','About'),self)
        info.setToolTip(self.tr('Informationen über LunaTresor','About LunaTresor'))
        info.triggered.connect(self.show_about)
        bar.addAction(info)
    def show_about(self):
        title=self.tr('Über LunaTresor','About LunaTresor')
        body=(
            f'<h2>LunaTresor {VERSION}</h2>'
            f'<p>{self.tr("Sicherer, KeePass-kompatibler Passworttresor für KDBX-Dateien.", "Secure, KeePass-compatible password vault for KDBX files.")}</p>'
            f'<p><b>{self.tr("Version","Version")}:</b> {VERSION}<br>'
            f'<b>{self.tr("Oberfläche","Interface")}:</b> Qt / PySide6<br>'
            f'<b>{self.tr("Format","Format")}:</b> KeePass KDBX</p>'
            f'<p>{self.tr("© Goldisoft 2026","© Goldisoft 2026")}</p>'
        )
        QMessageBox.about(self,title,body)
    def metric(self,layout,label,value):
        f=QFrame(); f.setObjectName('metric'); v=QVBoxLayout(f); a=QLabel(value); a.setStyleSheet('font-size:22pt;font-weight:700'); b=QLabel(label); b.setObjectName('muted'); v.addWidget(a); v.addWidget(b); layout.addWidget(f,1); return a
    def apply_theme(self): self.setStyleSheet(DARK if self.theme=='dark' else LIGHT)
    def set_theme(self,t): self.theme=t; self.save_cfg(); self.apply_theme()
    def set_language(self,l):
        if l not in ('de','en') or l == self.lang:
            return
        # Rebuild translated widgets and menus immediately while retaining the
        # currently opened KeePass database and all in-memory application state.
        self.lang=l
        self.save_cfg()
        old_central=self.takeCentralWidget()
        if old_central is not None:
            old_central.deleteLater()
        self.menuBar().clear()
        self.build_ui()
        self.apply_theme()
        self.scan_vaults()
        if self.kp:
            self.refresh()
            self.m_state.setText(self.tr('Geöffnet','Open'))
        self.statusBar().showMessage(self.tr('Sprache sofort geändert.','Language changed immediately.'))
    def scan_vaults(self):
        self.vault_list.setRowCount(0)
        found=set()
        # Include the user's home directory by default; also include configured
        # folders and common removable/mounted locations. Avoid cache/build trees.
        roots=[Path.home(), *[Path(x).expanduser() for x in self.folders]]
        if os.name != 'nt':
            roots.extend([Path('/media')/Path.home().name, Path('/mnt')])
        excluded={'.cache','.local','.venv','venv','__pycache__','.git','node_modules'}
        for root in roots:
            if not root.exists() or not root.is_dir():
                continue
            try:
                for current, dirs, files in os.walk(root, onerror=lambda _e: None):
                    dirs[:] = [d for d in dirs if d not in excluded]
                    for name in files:
                        if name.lower().endswith('.kdbx'):
                            found.add(str(Path(current)/name))
            except (OSError, PermissionError):
                continue
        self.found=sorted(found,key=str.casefold)
        self.m_vault.setText(str(len(self.found)))
        for p in self.found:
            r=self.vault_list.rowCount()
            self.vault_list.insertRow(r)
            self.vault_list.setItem(r,0,QTableWidgetItem(Path(p).name))
            self.vault_list.item(r,0).setData(Qt.UserRole,p)
        if not self.kp:
            self.m_state.setText(self.tr('Nicht geöffnet','Not open'))
        self.statusBar().showMessage(self.tr('{n} Tresor(e) gefunden','{n} vault(s) found').format(n=len(self.found)))
    def add_folder(self):
        d=QFileDialog.getExistingDirectory(self,self.tr('Ordner auswählen','Choose folder'))
        if d and d not in self.folders: self.folders.append(d); self.save_cfg(); self.scan_vaults()
    def remove_folder(self):
        row=self.vault_list.currentRow()
        if row>=0 and self.found:
            parent=str(Path(self.found[row]).parent)
            if parent in self.folders: self.folders.remove(parent); self.save_cfg(); self.scan_vaults()
    def open_selected(self):
        row=self.vault_list.currentRow()
        if row>=0: self.open_path(self.vault_list.item(row,0).data(Qt.UserRole))
    def open_vault(self):
        p,_=QFileDialog.getOpenFileName(self,self.tr('Tresor öffnen','Open vault'),'','KeePass (*.kdbx)')
        if p:self.open_path(p)
    def open_path(self,p):
        if PyKeePass is None: QMessageBox.critical(self,APP,'PyKeePass fehlt. Installiere python3-pykeepass.'); return
        pw,ok=QInputDialog.getText(self,self.tr('Tresor öffnen','Open vault'),self.tr('Master-Passwort:','Master password:'),QLineEdit.Password)
        if not ok:return
        try:self.kp=PyKeePass(p,password=pw); self.path=p; self.master_password=pw; self.populate_groups(); self.refresh(); self.m_state.setText(self.tr('Geöffnet','Open')); self.statusBar().showMessage(self.tr('Geöffnet: ','Opened: ')+Path(p).name); self.last_activity=time.monotonic()
        except Exception as e: QMessageBox.critical(self,APP,self.tr('Tresor konnte nicht geöffnet werden: ','Could not open vault: ')+str(e))
    def new_vault(self):
        if create_database is None: QMessageBox.critical(self,APP,'PyKeePass fehlt.'); return
        p,_=QFileDialog.getSaveFileName(self,self.tr('Neuen Tresor anlegen','Create new vault'),'Neuer_Tresor.kdbx','KeePass (*.kdbx)')
        if not p:return
        if not p.lower().endswith('.kdbx'):p+='.kdbx'
        pw,ok=QInputDialog.getText(self,APP,self.tr('Neues Master-Passwort:','New master password:'),QLineEdit.Password)
        if not ok or not pw:return
        confirm,ok=QInputDialog.getText(self,APP,self.tr('Master-Passwort wiederholen:','Repeat master password:'),QLineEdit.Password)
        if not ok:return
        if pw!=confirm: QMessageBox.warning(self,APP,self.tr('Passwörter stimmen nicht überein.','Passwords do not match.')); return
        try:create_database(p,password=pw); self.kp=PyKeePass(p,password=pw); self.path=p; self.master_password=pw; self.populate_groups(); self.refresh(); self.m_state.setText(self.tr('Geöffnet','Open')); self.scan_vaults()
        except Exception as e:QMessageBox.critical(self,APP,str(e))
    def entries(self):
        if not self.kp:return []
        out=[]
        def walk(g,path='',is_root=False):
            here=path if is_root else (path+'/'+g.name).strip('/')
            for e in g.entries:
                shown_group=here or (self.tr('Allgemein','General'))
                out.append((e,shown_group))
            for sg in g.subgroups:walk(sg,here,False)
        walk(self.kp.root_group,'',True); return out
    def groups(self):
        out=[]
        def walk(g,path=''):
            for sg in g.subgroups:
                p=(path+'/'+sg.name).strip('/'); out.append(p); walk(sg,p)
        walk(self.kp.root_group); return out or ['General' if self.lang=='en' else 'Allgemein']
    def selected_group_path(self):
        # Group filtering is intentionally not embedded in the main window.
        return ''
    def populate_groups(self):
        # Kept as a refresh hook for vault open/close; groups live in a separate manager.
        return
    def manage_groups(self):
        if not self.kp:
            QMessageBox.information(self,APP,self.tr('Bitte zuerst einen Tresor öffnen.','Please open a vault first.')); return
        dlg=QDialog(self); dlg.setWindowTitle(self.tr('Gruppen verwalten','Manage groups')); dlg.resize(430,470)
        layout=QVBoxLayout(dlg); layout.addWidget(QLabel(self.tr('Gruppen und Untergruppen des geöffneten Tresors','Groups and subgroups in the open vault')))
        tree=QTreeWidget(); tree.setHeaderHidden(True); layout.addWidget(tree,1)
        def refill(select_path=''):
            tree.clear(); root=QTreeWidgetItem([self.tr('Hauptgruppe','Root')]); root.setData(0,Qt.UserRole,''); tree.addTopLevelItem(root)
            def add_children(parent_item,parent_group,prefix=''):
                for group in sorted(parent_group.subgroups,key=lambda x:x.name.casefold()):
                    path=(prefix+'/'+group.name).strip('/'); item=QTreeWidgetItem([group.name]); item.setData(0,Qt.UserRole,path); parent_item.addChild(item); add_children(item,group,path)
            add_children(root,self.kp.root_group); root.setExpanded(True)
            target=root
            if select_path:
                for i in range(tree.topLevelItemCount()):
                    stack=[tree.topLevelItem(i)]
                    while stack:
                        item=stack.pop()
                        if item.data(0,Qt.UserRole)==select_path: target=item; break
                        stack.extend(item.child(j) for j in range(item.childCount()))
            tree.setCurrentItem(target)
        def add():
            item=tree.currentItem(); parent_path=item.data(0,Qt.UserRole) if item else ''
            parent=self.kp.root_group
            if parent_path:
                for part in parent_path.split('/'):
                    parent=next((g for g in parent.subgroups if g.name==part),None)
                    if parent is None: break
            if parent is None: parent=self.kp.root_group; parent_path=''
            name,ok=QInputDialog.getText(dlg,APP,self.tr('Name der neuen Gruppe:','New group name:'))
            name=name.strip()
            if not ok or not name:return
            if '/' in name or any(g.name.casefold()==name.casefold() for g in parent.subgroups):
                QMessageBox.warning(dlg,APP,self.tr('Ungültiger oder bereits vorhandener Gruppenname.','Invalid or duplicate group name.')); return
            try:self.kp.add_group(parent,name); self.kp.save(); refill((parent_path+'/'+name).strip('/'))
            except Exception as ex: QMessageBox.critical(dlg,APP,str(ex))
        def delete():
            item=tree.currentItem(); path=item.data(0,Qt.UserRole) if item else ''
            if not path:
                QMessageBox.information(dlg,APP,self.tr('Bitte eine Gruppe auswählen.','Select a group first.')); return
            group=next((g for g in self.kp.groups if self.group_path(g)==path),None)
            if not group:return
            if group.entries or group.subgroups:
                QMessageBox.warning(dlg,APP,self.tr('Die Gruppe ist nicht leer. Verschiebe zuerst Einträge und Untergruppen.','Group is not empty. Move entries and subgroups first.')); return
            if not self.ask_yes_no(APP,self.tr(f'Gruppe „{path}“ löschen?','Delete group “{path}”?'),dlg):return
            try:self.kp.delete_group(group); self.kp.save(); refill()
            except Exception as ex: QMessageBox.critical(dlg,APP,str(ex))
        actions=QHBoxLayout(); add_btn=QPushButton(self.tr('+ Gruppe / Untergruppe','+ Group / subgroup')); add_btn.setObjectName('accent'); add_btn.clicked.connect(add); del_btn=QPushButton(self.tr('Gruppe löschen','Delete group')); del_btn.setObjectName('danger'); del_btn.clicked.connect(delete); close_btn=QPushButton(self.tr('Schließen','Close')); close_btn.clicked.connect(dlg.accept)
        actions.addWidget(add_btn); actions.addWidget(del_btn); actions.addStretch(); actions.addWidget(close_btn); layout.addLayout(actions)
        refill(); dlg.exec(); self.refresh()
    def add_group(self): self.manage_groups()
    def delete_group(self): self.manage_groups()
    def group_path(self,g):
        names=[]; cur=g
        # PyKeePass exposes the parent group as `parentgroup`, not `parent`.
        while cur and getattr(cur,'parentgroup',None) is not None:
            names.append(cur.name); cur=cur.parentgroup
        return '/'.join(reversed(names))
    def meta(self,e,k,default=''):
        try:return str(e.get_custom_property('LunaTresor_'+k) or default)
        except Exception:return default
    def setmeta(self,e,k,v): e.set_custom_property('LunaTresor_'+k,str(v))
    def favorite(self): 
        e=self.selected()
        if not e:return
        try:self.setmeta(e,'favorite','0' if self.meta(e,'favorite')=='1' else '1'); self.kp.save(); self.refresh()
        except Exception as ex:QMessageBox.critical(self,APP,str(ex))
    def selected(self):
        row=self.table.currentRow()
        if row<0 or not self.kp:return None
        ix=self.table.item(row,0).data(Qt.UserRole)
        es=self.visible_entries
        return es[ix][0] if 0<=ix<len(es) else None
    def strength(self,pw):
        if not pw or len(pw)<8 or len(set(pw))==1:return 0,'Sehr schwach' if self.lang=='de' else 'Very weak'
        low=pw.casefold(); score=(2 if len(pw)>=20 else 1 if len(pw)>=12 else 0)
        classes=sum(bool(re.search(p,pw)) for p in (r'[a-z]',r'[A-Z]',r'\d',r'[^A-Za-z0-9]')); score+=classes
        if re.search(r'(1234|abcd|qwer|asdf|password|passwort)',low):score-=2
        levels=[('Sehr schwach','Very weak'),('Schwach','Weak'),('Mittel','Fair'),('Stark','Strong'),('Sehr stark','Very strong')]
        idx=0 if score<=0 else 1 if score<=1 else 2 if score<=2 else 3 if score<=3 else 4
        return idx,levels[idx][0 if self.lang=='de' else 1]
    def changed(self,e):
        value=self.meta(e,'password_changed')
        return value or (self.tr('Unbekannt','Unknown'))
    def refresh(self,*args):
        self.table.setRowCount(0); self.visible_entries=[]; all_e=self.entries(); q=self.search.text().casefold() if hasattr(self,'search') else ''; selected_group=self.selected_group_path() if hasattr(self,'group_tree') else ''
        fav=weak=0
        for e,g in all_e:
            level,label=self.strength(e.password or ''); isfav=self.meta(e,'favorite')=='1'; fav+=isfav; weak+=level<=1
            if selected_group and not (g==selected_group or g.startswith(selected_group+'/')):continue
            if q and q not in ' '.join([g,e.title or '',e.username or '',e.url or '',e.notes or '',label]).casefold():continue
            ix=len(self.visible_entries); self.visible_entries.append((e,g)); r=self.table.rowCount(); self.table.insertRow(r)
            values=['★' if isfav else '',g,e.title or '',e.username or '',('•'*min(len(e.password or ''),14) if not self.show_pw else e.password or ''),label,self.changed(e),e.url or '',e.notes or '']
            for c,val in enumerate(values):
                it=QTableWidgetItem(str(val)); it.setToolTip(str(val)); it.setData(Qt.UserRole,ix) if c==0 else None; self.table.setItem(r,c,it)
        self.m_entries.setText(str(len(all_e))); self.summary.setText(self.tr('Gruppen: ','Groups: ')+str(len(self.groups()))+'   •   '+self.tr('Favoriten: ','Favorites: ')+str(fav)+'   •   '+self.tr('Schwache Passwörter: ','Weak passwords: ')+str(weak))
    def add_entry(self): self.edit(None)
    def edit_entry(self): self.edit(self.selected())
    def edit(self,e):
        if not self.kp: QMessageBox.information(self,APP,self.tr('Öffne zuerst einen Tresor.','Open a vault first.')); return
        dlg=EntryDialog(self,self.groups(),e,self.lang)
        if dlg.exec()!=QDialog.Accepted:return
        title,user,pw,url,group,notes=dlg.data()
        if not title: QMessageBox.warning(self,APP,self.tr('Titel ist erforderlich.','Title is required.')); return
        try:
            grp=next((g for g in self.kp.groups if self.group_path(g)==group),None)
            if not grp:
                parent=self.kp.root_group
                for part in group.split('/'):
                    nxt=next((x for x in parent.subgroups if x.name==part),None) or self.kp.add_group(parent,part); parent=nxt
                grp=parent
            if e:
                e.title=title; e.username=user; e.password=pw; e.url=url; e.notes=notes
                self.setmeta(e,'password_changed',time.strftime('%Y-%m-%d'))
            else:
                e=self.kp.add_entry(grp,title,user,pw,url,notes); self.setmeta(e,'password_changed',time.strftime('%Y-%m-%d'))
            self.kp.save(); self.refresh()
        except Exception as ex:QMessageBox.critical(self,APP,str(ex))
    def delete_entry(self):
        e=self.selected()
        if e and self.ask_yes_no(APP,self.tr('Eintrag löschen?','Delete entry?')):
            self.kp.delete_entry(e); self.kp.save(); self.refresh()
    def toggle_passwords(self):
        self.show_pw=not self.show_pw; self.refresh()
    def copy_password(self):
        e=self.selected()
        if not e:return
        QApplication.clipboard().setText(e.password or ''); QTimer.singleShot(30000,lambda:QApplication.clipboard().clear())
        self.statusBar().showMessage(self.tr('Passwort kopiert; Zwischenablage wird in 30 Sekunden geleert.','Password copied; clipboard clears in 30 seconds.'),5000)
    def make_password(self,n=24):
        alphabet=string.ascii_letters+string.digits+'!@#$%^&*()-_=+[]{}'
        while True:
            pw=''.join(secrets.choice(alphabet) for _ in range(n))
            if sum(bool(re.search(p,pw)) for p in (r'[a-z]',r'[A-Z]',r'\d',r'[^A-Za-z0-9]'))>=4:return pw
    def generator(self):
        dlg=QDialog(self)
        dlg.setWindowTitle(self.tr('Passwortgenerator','Password generator'))
        dlg.setMinimumWidth(520)
        layout=QVBoxLayout(dlg)
        row=QHBoxLayout()
        row.addWidget(QLabel(self.tr('Passwortlänge:','Password length:')))
        length=QSpinBox(); length.setRange(12,128); length.setValue(24); row.addWidget(length)
        layout.addLayout(row)
        value=QLineEdit(); value.setReadOnly(True); value.setEchoMode(QLineEdit.Password)
        layout.addWidget(value)
        controls=QHBoxLayout()
        show=QPushButton(self.tr('Anzeigen','Show'))
        def toggle():
            visible=value.echoMode()==QLineEdit.Password
            value.setEchoMode(QLineEdit.Normal if visible else QLineEdit.Password)
            show.setText(self.tr('Verbergen','Hide') if visible else self.tr('Anzeigen','Show'))
        show.clicked.connect(toggle); controls.addWidget(show)
        regen=QPushButton(self.tr('Neu generieren','Generate again')); controls.addWidget(regen)
        layout.addLayout(controls)
        buttons=QHBoxLayout(); buttons.addStretch()
        copy=QPushButton(self.tr('Kopieren','Copy')); copy.setObjectName('accent')
        close=QPushButton(self.tr('Schließen','Close'))
        buttons.addWidget(copy); buttons.addWidget(close); layout.addLayout(buttons)
        def make():
            value.setText(self.make_password(length.value()))
        def do_copy():
            if value.text():
                QApplication.clipboard().setText(value.text())
                QTimer.singleShot(30000,lambda: QApplication.clipboard().clear() if QApplication.clipboard().text()==value.text() else None)
                self.statusBar().showMessage(self.tr('Passwort kopiert; Zwischenablage wird nach 30 Sekunden geleert.','Password copied; clipboard clears after 30 seconds.'),5000)
        regen.clicked.connect(make); copy.clicked.connect(do_copy); close.clicked.connect(dlg.accept)
        make(); dlg.exec()
    def import_csv(self):
        if not self.kp:return
        p,_=QFileDialog.getOpenFileName(self,APP,'','CSV (*.csv)')
        if not p:return
        if QMessageBox.warning(self,APP,self.tr('CSV kann Passwörter im Klartext enthalten. Importieren?','CSV may contain plaintext passwords. Import?'),QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:return
        try:
            with open(p,newline='',encoding='utf-8-sig') as f:
                for r in csv.DictReader(f):
                    title=(r.get('title') or r.get('name') or '').strip()
                    if title:
                        name=(r.get('group') or 'Allgemein').strip(); g=next((x for x in self.kp.root_group.subgroups if x.name==name),None) or self.kp.add_group(self.kp.root_group,name)
                        self.kp.add_entry(g,title,r.get('username') or '',r.get('password') or '',r.get('url') or '',r.get('notes') or '')
            self.kp.save(); self.refresh()
        except Exception as e:QMessageBox.critical(self,APP,str(e))
    def export_csv(self):
        if not self.kp:return
        p,_=QFileDialog.getSaveFileName(self,APP,'export.csv','CSV (*.csv)')
        if not p:return
        if QMessageBox.warning(self,APP,self.tr('CSV enthält Passwörter im Klartext. Fortfahren?','CSV contains plaintext passwords. Continue?'),QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:return
        with open(p,'w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=['group','title','username','password','url','notes']); w.writeheader()
            for e,g in self.entries():w.writerow(dict(group=g,title=e.title or '',username=e.username or '',password=e.password or '',url=e.url or '',notes=e.notes or ''))
    def _pin_key(self,pin,salt):
        if Scrypt is None or AESGCM is None: raise RuntimeError('cryptography fehlt.')
        return Scrypt(salt=salt,length=32,n=2**15,r=8,p=1).derive(pin.encode('utf-8'))
    def _make_pin_blob(self,pin,master):
        salt=os.urandom(16); nonce=os.urandom(12)
        ct=AESGCM(self._pin_key(pin,salt)).encrypt(nonce,master.encode('utf-8'),b'LunaTresor PIN unlock v1')
        return {'version':1,'salt':base64.b64encode(salt).decode(),'nonce':base64.b64encode(nonce).decode(),'ciphertext':base64.b64encode(ct).decode()}
    def _master_from_pin(self,pin):
        b=self.pin_blob
        return AESGCM(self._pin_key(pin,base64.b64decode(b['salt']))).decrypt(base64.b64decode(b['nonce']),base64.b64decode(b['ciphertext']),b'LunaTresor PIN unlock v1').decode()
    def security_settings(self):
        d=QDialog(self); d.setWindowTitle(self.tr('Sicherheit','Security')); v=QVBoxLayout(d)
        v.addWidget(QLabel(self.tr('Automatische Sperre bei Inaktivität','Automatic inactivity lock')))
        combo=QComboBox(); opts=[(0,'Nie' if self.lang=='de' else 'Never'),(1,'1 Minute'),(2,'2 Minuten'),(5,'5 Minuten'),(10,'10 Minuten'),(15,'15 Minuten'),(30,'30 Minuten'),(60,'60 Minuten')]
        for n,label in opts: combo.addItem(label,n)
        ix=combo.findData(self.idle_lock_minutes); combo.setCurrentIndex(max(0,ix)); v.addWidget(combo)
        status=QLabel(self.tr('PIN: eingerichtet','PIN: configured') if self.pin_blob else self.tr('PIN: nicht eingerichtet','PIN: not configured')); v.addWidget(status)
        pinrow=QHBoxLayout(); setpin=QPushButton(self.tr('PIN festlegen/ändern','Set/change PIN')); rempin=QPushButton(self.tr('PIN entfernen','Remove PIN')); pinrow.addWidget(setpin); pinrow.addWidget(rempin); v.addLayout(pinrow)
        def set_pin():
            if not self.kp or not self.master_password:
                QMessageBox.information(d, APP, self.tr('Öffne zuerst einen Tresor.','Open a vault first.'))
                return
            a, ok = self.password_prompt(APP, self.tr('Neue PIN (mindestens 8 Ziffern):','New PIN (at least 8 digits):'))
            if not ok:
                return
            b, ok = self.password_prompt(APP, self.tr('PIN wiederholen:','Repeat PIN:'))
            if not ok:
                return
            if not a.isdigit() or len(a) < 8 or a != b:
                QMessageBox.warning(d, APP, self.tr('PIN ungültig oder stimmt nicht überein.','PIN invalid or does not match.'))
                return
            try:
                new_blob = self._make_pin_blob(a, self.master_password)
                old_blob = self.pin_blob
                self.pin_blob = new_blob
                self.save_cfg()
                status.setText(self.tr('PIN: eingerichtet','PIN: configured'))
                QMessageBox.information(d, APP, self.tr('PIN wurde gespeichert.','PIN was saved.'))
            except Exception as exc:
                self.pin_blob = old_blob if 'old_blob' in locals() else self.pin_blob
                QMessageBox.critical(d, APP, self.tr('PIN konnte nicht gespeichert werden: ','Could not save PIN: ') + str(exc))
        def remove_pin():
            if self.pin_blob and self.ask_yes_no(APP,self.tr('PIN wirklich entfernen?','Remove PIN?'),d):
                self.pin_blob=None; self.save_cfg(); status.setText(self.tr('PIN: nicht eingerichtet','PIN: not configured'))
        setpin.clicked.connect(set_pin); rempin.clicked.connect(remove_pin)
        buttons=QHBoxLayout(); buttons.addStretch(); save=QPushButton(self.tr('Speichern','Save')); close=QPushButton(self.tr('Schließen','Close')); buttons.addWidget(save); buttons.addWidget(close); v.addLayout(buttons)
        def persist():
            self.idle_lock_minutes=int(combo.currentData()); self.save_cfg(); d.accept()
        save.clicked.connect(persist); close.clicked.connect(d.reject); d.exec()
    def lock(self):
        if not self.kp:return
        self.idle.stop()
        self.kp=None
        self.master_password=None
        self.table.setRowCount(0)
        self.populate_groups()
        self.m_entries.setText('0')
        self.m_state.setText(self.tr('Gesperrt','Locked'))
        try:
            if self.pin_blob:
                # When a PIN is configured, accept ONLY that PIN here.
                # The PIN decrypts the saved master password; the user is not
                # asked for the master password during normal unlocking.
                pin,ok=self.password_prompt(
                    APP,
                    self.tr('Tresor gesperrt. PIN eingeben:',
                            'Vault locked. Enter PIN:'))
                if not ok or not pin:
                    self.statusBar().showMessage(
                        self.tr('Tresor bleibt gesperrt.','Vault remains locked.'))
                    return
                master=self._master_from_pin(pin)
            else:
                master,ok=self.password_prompt(
                    APP,
                    self.tr('Tresor gesperrt. Master-Passwort eingeben:',
                            'Vault locked. Enter master password:'))
                if not ok or not master:
                    self.statusBar().showMessage(
                        self.tr('Tresor bleibt gesperrt.','Vault remains locked.'))
                    return
            reopened=PyKeePass(self.path,password=master)
            self.kp=reopened
            self.master_password=master
            self.populate_groups()
            self.refresh()
            self.m_state.setText(self.tr('Geöffnet','Open'))
        except Exception:
            QMessageBox.warning(
                self,APP,
                self.tr('PIN falsch oder PIN-Daten ungültig. Tresor bleibt gesperrt.',
                        'Incorrect PIN or invalid PIN data. Vault remains locked.')
                if self.pin_blob else
                self.tr('Master-Passwort falsch. Tresor bleibt gesperrt.',
                        'Incorrect master password. Vault remains locked.'))
            self.statusBar().showMessage(
                self.tr('Tresor bleibt gesperrt.','Vault remains locked.'))
        finally:
            self.last_activity=time.monotonic()
            self.idle.start(1000)
    def export_ltx(self):
        if not self.kp:return
        if AESGCM is None: QMessageBox.critical(self,APP,'cryptography fehlt.'); return
        path,_=QFileDialog.getSaveFileName(self,APP,'LunaTresor-Export.ltx','LunaTresor Export (*.ltx)')
        if not path:return
        pw,ok=QInputDialog.getText(self,APP,self.tr('Export-Passwort:','Export password:'),QLineEdit.Password)
        if not ok or not pw:return
        try:
            rows=[{'group':g,'title':e.title or '','username':e.username or '','password':e.password or '','url':e.url or '','notes':e.notes or ''} for e,g in self.entries()]
            salt=os.urandom(16); nonce=os.urandom(12); key=hashlib.pbkdf2_hmac('sha256',pw.encode(),salt,600000,dklen=32)
            ct=AESGCM(key).encrypt(nonce,json.dumps(rows,ensure_ascii=False).encode(),b'LunaTresor encrypted export v1')
            Path(path).write_text(json.dumps({'format':'LunaTresor encrypted export','version':1,'iterations':600000,'salt':base64.b64encode(salt).decode(),'nonce':base64.b64encode(nonce).decode(),'ciphertext':base64.b64encode(ct).decode()})); Path(path).chmod(0o600)
            QMessageBox.information(self,APP,self.tr('Verschlüsselter Export erstellt.','Encrypted export created.'))
        except Exception as ex: QMessageBox.critical(self,APP,str(ex))
    def import_ltx(self):
        if not self.kp:return
        path,_=QFileDialog.getOpenFileName(self,APP,'','LunaTresor Export (*.ltx)')
        if not path:return
        pw,ok=QInputDialog.getText(self,APP,self.tr('Export-Passwort:','Export password:'),QLineEdit.Password)
        if not ok:return
        try:
            d=json.loads(Path(path).read_text()); salt=base64.b64decode(d['salt']); nonce=base64.b64decode(d['nonce'])
            key=hashlib.pbkdf2_hmac('sha256',pw.encode(),salt,int(d.get('iterations',600000)),dklen=32)
            rows=json.loads(AESGCM(key).decrypt(nonce,base64.b64decode(d['ciphertext']),b'LunaTresor encrypted export v1'))
            if not self.ask_yes_no(APP,self.tr(f'{len(rows)} Einträge importieren?','Import {len(rows)} entries?')):return
            for row in rows:
                name=(row.get('group') or 'Allgemein').split('/')[0]
                grp=next((g for g in self.kp.root_group.subgroups if g.name==name),None) or self.kp.add_group(self.kp.root_group,name)
                self.kp.add_entry(grp,row.get('title',''),row.get('username',''),row.get('password',''),row.get('url',''),row.get('notes',''))
            self.kp.save(); self.refresh()
        except Exception as ex: QMessageBox.critical(self,APP,self.tr('Import fehlgeschlagen: ','Import failed: ')+str(ex))
    def closeEvent(self,e):
        self.kp=None; super().closeEvent(e)

def main():
    app=QApplication(sys.argv); app.setApplicationName(APP); app.setFont(QFont('Noto Sans',10))
    w=Main(); w.show(); sys.exit(app.exec())
if __name__=='__main__': main()
