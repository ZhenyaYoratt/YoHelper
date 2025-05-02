# ui/autoruns.py
from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QTabWidget, QWidget,
    QGroupBox, QTableWidget, QTableWidgetItem, QPushButton,
    QHBoxLayout, QStatusBar, QHeaderView, QLabel, QDialog,
    QFormLayout, QLineEdit, QComboBox, QFileDialog, QMessageBox, QStyledItemDelegate
)
from PyQt5.QtCore import Qt, QDateTime
from modules.autoruns import *  # get_* and add_/remove_/edit_ functions
from modules.titles import make_title
from pyqt_windows_os_light_dark_theme_window.main import Window
import subprocess, os, winreg

# Delegate to prevent eliding
class NoElideDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.textElideMode = Qt.ElideNone

# Dialog for registry entries (Run, RunOnce, Winlogon)
class RegistryEntryDialog(QDialog):
    def __init__(self, parent=None, entry=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Редактировать запись реестра") if entry else self.tr("Добавить запись реестра"))
        self.entry = entry
        layout = QFormLayout(self)
        self.name_edit = QLineEdit(entry['name'] if entry else "")
        self.data_edit = QLineEdit(entry['data'] if entry else "")
        self.type_combo = QComboBox()
        basic = ["REG_SZ", "REG_DWORD", "REG_QWORD"]
        extended = ["REG_BINARY", "REG_DWORD_LITTLE_ENDIAN", "REG_DWORD_BIG_ENDIAN", "REG_EXPAND_SZ",
                    "REG_LINK", "REG_MULTI_SZ", "REG_NONE", "REG_QWORD_LITTLE_ENDIAN",
                    "REG_RESOURCE_LIST", "REG_FULL_RESOURCE_DESCRIPTOR", "REG_RESOURCE_REQUIREMENTS_LIST"]
        self.type_combo.addItems(basic)
        self.expand_btn = QPushButton(self.tr("Расширить"))
        self.expand_btn.clicked.connect(lambda: (self.type_combo.clear(), self.type_combo.addItems(basic), self.type_combo.addItems(extended)))
        layout.addRow(self.tr("Название"), self.name_edit)
        layout.addRow(self.tr("Значение"), self.data_edit)
        row = QHBoxLayout()
        row.addWidget(self.type_combo)
        row.addWidget(self.expand_btn)
        layout.addRow(self.tr("Тип реестра"), row)
        btns = QHBoxLayout()
        ok = QPushButton(self.tr("OK")); ok.clicked.connect(self.accept)
        cancel = QPushButton(self.tr("Отмена")); cancel.clicked.connect(self.reject)
        btns.addWidget(ok); btns.addWidget(cancel)
        layout.addRow(btns)
        self.resize(750, 140)

    def get_result(self):
        typ = getattr(winreg, self.type_combo.currentText(), winreg.REG_SZ)
        return { 'name': self.name_edit.text(), 'data': self.data_edit.text(), 'type': typ }

# Dialog for file entries (Startup folder)
class FileEntryDialog(QDialog):
    def __init__(self, parent=None, entry=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Редактировать файл автозагрузки") if entry else self.tr("Добавить файл автозагрузки"))
        self.entry = entry
        layout = QFormLayout(self)
        self.name_edit = QLineEdit(entry['file'] if entry else "")
        self.path_edit = QLineEdit(entry['path'] if entry else "")
        browse = QPushButton(self.tr("Обзор"))
        browse.clicked.connect(self.select_file)
        hl = QHBoxLayout()
        hl.addWidget(self.path_edit)
        hl.addWidget(browse)
        layout.addRow(self.tr("Название файла"), self.name_edit)
        layout.addRow(self.tr("Расположение"), hl)
        btns = QHBoxLayout()
        ok = QPushButton(self.tr("OK")); ok.clicked.connect(self.accept)
        cancel = QPushButton(self.tr("Отмена")); cancel.clicked.connect(self.reject)
        btns.addWidget(ok); btns.addWidget(cancel)
        layout.addRow(btns)
        self.resize(750, 140)

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr("Выберите файл"))
        if path:
            self.path_edit.setText(path)

    def get_result(self):
        return { 'file': self.name_edit.text(), 'path': self.path_edit.text() }

class AutorunsWindow(QMainWindow, Window):
    def __init__(self, parent=None):
        super().__init__()
        self.setParent(parent)
        self.setWindowTitle(make_title(self.tr("Автозагрузки")))
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.available_drives = self.detect_system_drives()
        self.current_drive = self.available_drives[0] if self.available_drives else 'C:'
        self.initUI()
        self.resize(900, 700)
        self.center()

    def detect_system_drives(self):
        # detect letters where Windows folder exists
        drives = []
        for letter in list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"): 
            path = f"{letter}:/Windows"
            if os.path.isdir(path):
                drives.append(f"{letter}:")
        return drives
    
    def initUI(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        # Drive selection
        if self.available_drives:
            hl = QHBoxLayout()
            hl.addWidget(QLabel(self.tr("Выберите системный диск:")))
            self.drive_combo = QComboBox()
            self.drive_combo.addItems(self.available_drives)
            self.drive_combo.currentTextChanged.connect(self.on_drive_changed)
            hl.addWidget(self.drive_combo)
            self.layout.addLayout(hl)

        self.tabs = QTabWidget(); self.layout.addWidget(self.tabs)
        self.registry_tab = QWidget(); self.folder_tab = QWidget()
        self.tasks_tab = QWidget(); self.winlogon_tab = QWidget(); self.services_tab = QWidget()
        self.tabs.addTab(self.registry_tab, self.tr("Реестр"))
        self.tabs.addTab(self.folder_tab, self.tr("Папка автозагрузки"))
        self.tabs.addTab(self.winlogon_tab, self.tr("Winlogon"))
        self.tabs.addTab(self.tasks_tab, self.tr("Планировщик задач"))
        self.tabs.addTab(self.services_tab, self.tr("Службы"))
        self.status_bar = QStatusBar(); self.setStatusBar(self.status_bar)
        self.init_registry_tab(); self.init_folder_tab()
        self.init_tasks_tab(); self.init_winlogon_tab(); self.init_services_tab()

    def on_drive_changed(self, drive):
        self.current_drive = drive
        # reload registry and winlogon tabs
        self.load_registry()
        self.load_winlogon()
        
    def configure_table(self, table: QTableWidget):
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setItemDelegate(NoElideDelegate())
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.resizeColumnsToContents()
        table.resizeRowsToContents()

    def init_registry_tab(self):
        layout = QVBoxLayout(self.registry_tab)
        self.reg_tables = {}
        for runonce in (False, True):
            title = self.tr("RunOnce") if runonce else self.tr("Run")
            group = QGroupBox(title); g_layout = QVBoxLayout(group)
            table = QTableWidget(); table.setColumnCount(4)
            table.setHorizontalHeaderLabels([self.tr("Название"), self.tr("Значение"), self.tr("Расположение"), self.tr("Тип")])
            self.configure_table(table)
            table.itemSelectionChanged.connect(self.update_reg_buttons)
            g_layout.addWidget(table)
            self.reg_tables[runonce] = table
            hl = QHBoxLayout()
            table.btns = {}
            for name in ["Добавить", "Удалить", "Изменить", "Открыть папку расположения"]:
                btn = QPushButton(self.tr(name)); btn.clicked.connect(lambda _, n=name, ro=runonce: self.on_reg_btn(n, ro))
                btn.setEnabled(name == "Добавить"); hl.addWidget(btn)
                table.btns[btn.text()] = btn
            g_layout.addLayout(hl); layout.addWidget(group)
        self.load_registry()

    def load_registry(self):
        for runonce, table in self.reg_tables.items():
            entries = get_autorun_registry(runonce, drive=self.current_drive)
            table.setRowCount(len(entries))
            for r, e in enumerate(entries):
                table.setItem(r, 0, QTableWidgetItem(e['name']))
                table.setItem(r, 1, QTableWidgetItem(str(e['data'])))
                table.setItem(r, 2, QTableWidgetItem(e['location']))
                table.setItem(r, 3, QTableWidgetItem(str(e['type'])))
                table.setRowHeight(r, 20)
            table.resizeColumnsToContents()
            table.resizeRowsToContents()

    def update_reg_buttons(self):
        for runonce, table in self.reg_tables.items():
            sel = len(table.selectedIndexes()) > 0
            btns = table.btns
            btns["Удалить"].setEnabled(sel)
            btns["Изменить"].setEnabled(sel and len({i.row() for i in table.selectedIndexes()}) == 1)
            btns["Открыть папку расположения"].setEnabled(sel)

    def on_reg_btn(self, name, runonce):
        table = self.reg_tables[runonce]
        if name == "Добавить":
            dlg = RegistryEntryDialog(self)
            if dlg.exec()==QDialog.Accepted:
                res=dlg.get_result()
                add_autorun_registry(res['name'], res['data'], res['type'], None, None, runonce)
                self.load_registry()
        else:
            # get selected entries
            rows = sorted({i.row() for i in table.selectedIndexes()})
            entries=[get_autorun_registry(runonce)[r] for r in rows]
            if name=="Удалить": remove_autorun_registry(entries); self.load_registry()
            elif name=="Изменить" and len(entries)==1:
                dlg=RegistryEntryDialog(self, entries[0])
                if dlg.exec()==QDialog.Accepted:
                    new=dlg.get_result(); edit_autorun_registry(entries[0], {**entries[0], **new}); self.load_registry()
            elif name=="Открыть папку расположения" and entries:
                path=os.path.dirname(entries[0]['data']); subprocess.Popen(f'explorer "{path}"')

    def init_folder_tab(self):
        layout = QVBoxLayout(self.folder_tab)
        self.folder_tables = {}
        for user, folder in get_startup_folders().items():
            group = QGroupBox(user); gl = QVBoxLayout(group)
            table = QTableWidget(); table.setColumnCount(5)
            table.setHorizontalHeaderLabels([
                self.tr("Название файла"), self.tr("Дата создания"), self.tr("Расположение"), self.tr("Дата открытия"), self.tr("Дата изменения")
            ])
            self.configure_table(table)
            table.itemSelectionChanged.connect(self.update_folder_buttons)
            gl.addWidget(table)
            hl = QHBoxLayout()
            table.btns = {}
            for name in ["Добавить", "Удалить", "Изменить", "Открыть папку расположения"]:
                btn = QPushButton(self.tr(name)); btn.clicked.connect(lambda _, n=name, u=user: self.on_folder_btn(n, u))
                btn.setEnabled(name == "Добавить"); hl.addWidget(btn)
                table.btns[btn.text()] = btn
            gl.addLayout(hl); layout.addWidget(group)
            self.folder_tables[user] = table
        self.load_folders()

    def load_folders(self):
        from modules.autoruns import get_startup_folder_entries
        data=get_startup_folder_entries()
        for user, table in self.folder_tables.items():
            items=data.get(user,[])
            table.setRowCount(len(items))
            for r,e in enumerate(items):
                table.setItem(r,0,QTableWidgetItem(e['file']))
                table.setItem(r,1,QTableWidgetItem(e['created'].strftime("%Y-%m-%d %H:%M:%S")))
                table.setItem(r,2,QTableWidgetItem(e['path']))
                table.setItem(r,3,QTableWidgetItem(e['accessed'].strftime("%Y-%m-%d %H:%M:%S")))
                table.setItem(r,4,QTableWidgetItem(e['modified'].strftime("%Y-%m-%d %H:%M:%S")))
            table.resizeColumnsToContents()
            table.resizeRowsToContents()

    def update_folder_buttons(self):
        for user, table in self.folder_tables.items():
            sel = len(table.selectedIndexes()) > 0
            btns = table.btns
            btns["Удалить"].setEnabled(sel)
            btns["Изменить"].setEnabled(sel and len({i.row() for i in table.selectedIndexes()}) == 1)
            btns["Открыть папку расположения"].setEnabled(sel)

    def on_folder_btn(self, name, user):
        table=self.folder_tables[user]; folder=get_startup_folders()[user]
        rows=sorted({i.row() for i in table.selectedIndexes()})
        data=[get_startup_folder_entries()[user][r] for r in rows]
        if name=="Добавить":
            dlg=FileEntryDialog(self)
            if dlg.exec()==QDialog.Accepted:
                res=dlg.get_result(); add_startup_file(folder, res['file'], res['path']); self.load_folders()
        elif name=="Удалить": remove_startup_files(data); self.load_folders()
        elif name=="Изменить" and len(data)==1:
            dlg=FileEntryDialog(self, data[0])
            if dlg.exec()==QDialog.Accepted:
                res=dlg.get_result(); edit_startup_file(data[0], res['file'], folder); self.load_folders()
        elif name=="Открыть папку расположения" and data:
            subprocess.Popen(f'explorer "{folder}"')

    def init_tasks_tab(self):
        layout = QVBoxLayout(self.tasks_tab)
        self.tasks_table = QTableWidget(); self.tasks_table.setColumnCount(5)
        self.tasks_table.setHorizontalHeaderLabels([
            self.tr("Название задачи"), self.tr("Состояние"), self.tr("Расположение"), self.tr("Последний запуск"), self.tr("Последний результат")
        ])
        self.configure_table(self.tasks_table)
        layout.addWidget(self.tasks_table)
        self.load_tasks()

    def load_tasks(self):
        tasks=get_scheduled_tasks()
        self.tasks_table.setRowCount(len(tasks))
        for r,t in enumerate(tasks):
            self.tasks_table.setItem(r,0,QTableWidgetItem(t['name']))
            self.tasks_table.setItem(r,1,QTableWidgetItem(t['state']))
            self.tasks_table.setItem(r,2,QTableWidgetItem(t['path']))
            self.tasks_table.setItem(r,3,QTableWidgetItem(str(t['last_run'])))
            self.tasks_table.setItem(r,4,QTableWidgetItem(str(t['last_result'])))
        self.tasks_table.resizeColumnsToContents()
        self.tasks_table.resizeRowsToContents()

    def init_winlogon_tab(self):
        layout = QVBoxLayout(self.winlogon_tab)
        self.win_tables = {}
        for arch, (hive, sub) in WINLOGON_SUBKEYS.items():
            group = QGroupBox(self.tr(f"Система {arch}")); gl = QVBoxLayout(group)
            table = QTableWidget(); table.setColumnCount(4)
            table.setHorizontalHeaderLabels([self.tr("Название"), self.tr("Значение"), self.tr("Расположение"), self.tr("Тип")])
            self.configure_table(table)
            table.itemSelectionChanged.connect(self.update_win_buttons)
            gl.addWidget(table)
            hl = QHBoxLayout()
            table.btns = {}
            for name in ["Добавить", "Удалить", "Изменить", "Открыть папку расположения"]:
                btn = QPushButton(self.tr(name)); btn.clicked.connect(lambda _, n=name, a=arch: self.on_winlogon_btn(n, a))
                btn.setEnabled(name == "Добавить"); hl.addWidget(btn)
                table.btns[btn.text()] = btn
            gl.addLayout(hl); layout.addWidget(group)
            self.win_tables[arch] = table
        self.load_winlogon()

    def load_winlogon(self):
        for arch, table in self.win_tables.items():
            entries = get_winlogon_entries(drive=self.current_drive)
            filt = [e for e in entries if e['arch'] == arch]
            table.setRowCount(len(filt))
            for r, e in enumerate(filt):
                table.setItem(r, 0, QTableWidgetItem(e['name']))
                table.setItem(r, 1, QTableWidgetItem(str(e['data'])))
                table.setItem(r, 2, QTableWidgetItem(e['location']))
                table.setItem(r, 3, QTableWidgetItem(str(e['type'])))
            table.resizeColumnsToContents()
            table.resizeRowsToContents()

    def update_win_buttons(self):
        for arch, table in self.win_tables.items():
            sel = len(table.selectedIndexes()) > 0
            btns = table.btns
            btns["Удалить"].setEnabled(sel)
            btns["Изменить"].setEnabled(sel and len({i.row() for i in table.selectedIndexes()}) == 1)
            btns["Открыть папку расположения"].setEnabled(sel)

    def on_winlogon_btn(self, name, arch):
        table=self.win_tables[arch]; rows=sorted({i.row() for i in table.selectedIndexes()})
        entries=[e for e in get_winlogon_entries() if e['arch']==arch]
        sel=[entries[r] for r in rows]
        if name=="Добавить":
            dlg=RegistryEntryDialog(self)
            if dlg.exec()==QDialog.Accepted:
                res=dlg.get_result(); add_autorun_registry(res['name'], res['data'], res['type'], None, WINLOGON_SUBKEYS[arch], False); self.load_winlogon()
        elif name=="Удалить": remove_autorun_registry(sel); self.load_winlogon()
        elif name=="Изменить" and len(sel)==1:
            dlg=RegistryEntryDialog(self, sel[0])
            if dlg.exec()==QDialog.Accepted:
                new=dlg.get_result(); edit_autorun_registry(sel[0], {**sel[0], **new}); self.load_winlogon()
        elif name=="Открыть папку расположения" and sel:
            path=os.path.dirname(sel[0]['data']); subprocess.Popen(f'explorer "{path}"')

    def init_services_tab(self):
        layout = QVBoxLayout(self.services_tab)
        self.svc_table = QTableWidget(); self.svc_table.setColumnCount(4)
        self.svc_table.setHorizontalHeaderLabels([
            self.tr("Название службы"), self.tr("Состояние"), self.tr("Тип запуска"), self.tr("Описание")
        ])
        self.configure_table(self.svc_table)
        self.svc_table.itemSelectionChanged.connect(self.update_svc_buttons)
        layout.addWidget(self.svc_table)
        self.prop_btn = QPushButton(self.tr("Свойства")); self.prop_btn.setEnabled(False)
        self.prop_btn.clicked.connect(self.show_service_props)
        #layout.addWidget(self.prop_btn)
        self.load_services()

    def load_services(self):
        svcs=get_services()
        self.svc_table.setRowCount(len(svcs))
        for r,s in enumerate(svcs):
            self.svc_table.setItem(r,0,QTableWidgetItem(s['display_name']))
            self.svc_table.setItem(r,1,QTableWidgetItem(s['state']))
            self.svc_table.setItem(r,2,QTableWidgetItem(s['start_mode']))
            self.svc_table.setItem(r,3,QTableWidgetItem(s['description']))
        self.svc_table.resizeColumnsToContents()
        self.svc_table.resizeRowsToContents()

    def update_svc_buttons(self):
        sel_count=len({i.row() for i in self.svc_table.selectedIndexes()})
        self.prop_btn.setEnabled(sel_count==1)

    def show_service_props(self):
        row=list({i.row() for i in self.svc_table.selectedIndexes()})[0]
        name=self.svc_table.item(row,0).text()
        QMessageBox.information(self, self.tr("Свойства службы"), f"{self.tr('Служба')}: {name}")

    def center(self):
        frame=self.frameGeometry(); center=self.screen().availableGeometry().center()
        frame.moveCenter(center); self.move(frame.topLeft())