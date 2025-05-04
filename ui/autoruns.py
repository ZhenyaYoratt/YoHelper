# ui/autoruns.py
from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QTabWidget, QWidget, QListWidget, QSplitter, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QStatusBar, QHeaderView, QLabel, QDialog,
    QFormLayout, QLineEdit, QComboBox, QFileDialog, QMessageBox, QGroupBox, QStyledItemDelegate
)
from PyQt5.QtCore import Qt
from modules.autoruns import *  # get_* and add_/remove_/edit_ functions
from modules.titles import make_title
from pyqt_windows_os_light_dark_theme_window.main import Window
import subprocess, os, winreg
import qtawesome as qta

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

TASK_STATE = {0: 'Неизвестно',
              1: 'Отключено',
              2: 'В очереди',
              3: 'Готово',
              4: 'Работает'}

class AutorunsWindow(QMainWindow, Window):
    def __init__(self, parent=None):
        super().__init__()
        self.setParent(parent)
        self.setWindowTitle(make_title(self.tr("Автозагрузки")))
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.available_drives = self.detect_system_drives()
        self.current_drive = self.available_drives[0] if self.available_drives else 'C:'
        self.folder_icon = qta.icon('fa.folder')
        self.task_icon = qta.icon('fa.play')
        self.initUI()
        self.resize(1000, 700)
        self.center()
    
    def initUI(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Drive selection
        if self.available_drives:
            hl = QHBoxLayout()
            label = QLabel(self.tr("Выберите системный диск:"))
            label.setAlignment(Qt.AlignmentFlag.AlignRight)
            hl.addWidget(label)
            self.drive_combo = QComboBox()
            self.drive_combo.addItems(self.available_drives)
            self.drive_combo.currentTextChanged.connect(self.on_drive_changed)
            hl.addWidget(self.drive_combo)
            self.layout.addLayout(hl)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        # Tabs
        self.registry_tab = QWidget()
        self.folder_tab = QWidget()
        self.tasks_tab = QWidget()
        self.winlogon_tab = QWidget()
        self.services_tab = QWidget()
        self.tabs.addTab(self.registry_tab, self.tr("Реестр"))
        self.tabs.addTab(self.folder_tab, self.tr("Папка автозагрузки"))
        self.tabs.addTab(self.winlogon_tab, self.tr("Winlogon"))
        self.tabs.addTab(self.tasks_tab, self.tr("Планировщик задач"))
        self.tabs.addTab(self.services_tab, self.tr("Службы"))

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Init each
        self.init_registry_tab()
        self.init_folder_tab()
        self.init_tasks_tab()
        self.init_winlogon_tab()
        self.init_services_tab()

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
        hive_map = {
            winreg.HKEY_CURRENT_USER: "HKEY_CURRENT_USER",
            winreg.HKEY_LOCAL_MACHINE: "HKEY_LOCAL_MACHINE"
        }
        for runonce, table in self.reg_tables.items():
            entries = get_autorun_registry(runonce, drive=self.current_drive)
            table.setRowCount(len(entries))
            for r, e in enumerate(entries):
                table.setItem(r, 0, QTableWidgetItem(e['name']))
                table.setItem(r, 1, QTableWidgetItem(str(e['data'])))
                hive_str = hive_map.get(e['hive'], str(e['hive']))
                loc = f"{hive_str}\\{e['location']}"
                table.setItem(r, 2, QTableWidgetItem(loc))
                table.setItem(r, 3, QTableWidgetItem(str(e['type'])))

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
                res = dlg.get_result()
                # выбираем по умолчанию первый путь из RUN_SUBKEYS или RUNONCE_SUBKEYS
                from modules.autoruns import RUN_SUBKEYS, RUNONCE_SUBKEYS
                keys = RUNONCE_SUBKEYS if runonce else RUN_SUBKEYS
                hive, subkey = keys[0]
                add_autorun_registry(res['name'], res['data'], res['type'], hive, subkey, runonce)
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
        splitter = QSplitter(Qt.Horizontal)
        # User list
        self.user_list = QListWidget()
        self.user_list.currentTextChanged.connect(self.on_user_selected)
        splitter.addWidget(self.user_list)
        # Table
        self.folder_table = QTableWidget()
        self.folder_table.setColumnCount(5)
        self.folder_table.setHorizontalHeaderLabels([
            self.tr("Название файла"), self.tr("Дата создания"),
            self.tr("Расположение"), self.tr("Дата открытия"), self.tr("Дата изменения")
        ])
        self.folder_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.folder_table.setSelectionBehavior(QTableWidget.SelectRows)
        splitter.addWidget(self.folder_table)
        splitter.setStretchFactor(1, 3)
        layout.addWidget(splitter)
        # Buttons
        hl = QHBoxLayout()
        for name in ["Добавить", "Удалить", "Изменить", "Открыть папку расположения"]:
            btn = QPushButton(self.tr(name))
            btn.clicked.connect(lambda _, n=name: self.on_folder_btn(n))
            setattr(self, f"folder_btn_{name}".replace(" ", "_"), btn)
            hl.addWidget(btn)
        layout.addLayout(hl)

        # Load users
        self.folders = get_startup_folder_entries()
        for user in self.folders:
            self.user_list.addItem(user)
        if self.user_list.count():
            self.user_list.setCurrentRow(0)

    def on_user_selected(self, user):
        entries = self.folders.get(user, [])
        self.folder_table.setRowCount(len(entries))
        for r, e in enumerate(entries):
            self.folder_table.setItem(r, 0, QTableWidgetItem(e['file']))
            self.folder_table.setItem(r, 1, QTableWidgetItem(e['created'].strftime("%Y-%m-%d %H:%M:%S")))
            self.folder_table.setItem(r, 2, QTableWidgetItem(e['path']))
            self.folder_table.setItem(r, 3, QTableWidgetItem(e['accessed'].strftime("%Y-%m-%d %H:%M:%S")))
            self.folder_table.setItem(r, 4, QTableWidgetItem(e['modified'].strftime("%Y-%m-%d %H:%M:%S")))

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

    def on_folder_btn(self, name):
        user = self.user_list.currentItem().text()
        entries = self.folders.get(user, [])
        rows = sorted({i.row() for i in self.folder_table.selectedIndexes()})
        sel = [entries[r] for r in rows]
        folder = get_startup_folders()[user]
        if name == "Добавить":
            dlg = FileEntryDialog(self)
            if dlg.exec() == QDialog.Accepted:
                res = dlg.get_result()
                add_startup_file(folder, res['file'], res['path'])
        elif name == "Удалить":
            remove_startup_files(sel)
        elif name == "Изменить" and len(sel) == 1:
            dlg = FileEntryDialog(self, sel[0])
            if dlg.exec() == QDialog.Accepted:
                res = dlg.get_result(); edit_startup_file(sel[0], res['file'], folder)
        elif name == "Открыть папку расположения" and sel:
            subprocess.Popen(f'explorer "{folder}"')
        # reload
        self.folders = get_startup_folder_entries()
        self.on_user_selected(user)

    def init_tasks_tab(self):
        layout = QVBoxLayout(self.tasks_tab)
        self.tasks_tree = QTreeWidget()
        self.tasks_tree.setHeaderLabels([
            self.tr("Название задачи"), self.tr("Состояние"),
            self.tr("Последний запуск"), self.tr("Последний результат"), self.tr("Папка")
        ])
        self.tasks_tree.header().setSectionResizeMode(QHeaderView.Interactive)
        self.tasks_tree.setColumnWidth(0, 300)
        layout.addWidget(self.tasks_tree)

        hl = QHBoxLayout()
        for name in ["Запустить", "Включить", "Отключить", "Удалить", "Обновить"]:
            btn = QPushButton(self.tr(name))
            btn.clicked.connect(lambda _, n=name: self.on_task_btn(n))
            setattr(self, f"task_btn_{name}".replace(" ", "_"), btn)
            hl.addWidget(btn)
        layout.addLayout(hl)
        self.load_tasks_tree()

    def load_tasks_tree(self):
        # preserve expanded paths
        expanded = set()
        def collect(item):
            for i in range(item.childCount()):
                c: QTreeWidgetItem = item.child(i)
                if c.isExpanded():
                    expanded.add(c.data(0, Qt.UserRole).Path if c.data(0, Qt.UserRole) else c.text(4))
                collect(c)
        collect(self.tasks_tree.invisibleRootItem())

        self.tasks_tree.clear()
        pythoncom.CoInitialize()
        self.scheduler = win32com.client.Dispatch('Schedule.Service')
        self.scheduler.Connect()
        root_folder = self.scheduler.GetFolder('\\')
        self._populate_task_folder(root_folder, self.tasks_tree.invisibleRootItem())

        self.tasks_tree.collapseAll()
        root_item = self.tasks_tree.topLevelItem(0)
        if root_item:
            self.tasks_tree.expandItem(root_item)
        # restore expansions
        def restore(item):
            for i in range(item.childCount()):
                c = item.child(i)
                obj = c.data(0, Qt.UserRole)
                path = obj.Path if obj else c.text(4)
                if path in expanded:
                    self.tasks_tree.expandItem(c)
                restore(c)
        restore(self.tasks_tree.invisibleRootItem())

    def _populate_task_folder(self, folder, parent_item):
        # folder: COM ITaskFolder
        fi = QTreeWidgetItem(parent_item, [folder.Name, "", "", "", folder.Path])
        fi.setIcon(0, self.folder_icon)
        fi.setData(0, Qt.UserRole, folder)
        # tasks
        for task in folder.GetTasks(1):
            ti = QTreeWidgetItem(fi, [
                task.Name,
                TASK_STATE.get(task.State, "Unknown"),
                str(task.LastRunTime),
                str(task.LastTaskResult),
                folder.Path
            ])
            ti.setIcon(0, self.task_icon)
            ti.setData(0, Qt.UserRole, task)
        # subfolders
        for sub in folder.GetFolders(0):
            self._populate_task_folder(sub, fi)

    def on_task_btn(self, action):
        if action == "Обновить":
            self.load_tasks_tree()
        item = self.tasks_tree.currentItem()
        if not item:
            return
        obj = item.data(0, Qt.UserRole)
        try:
            if hasattr(obj, 'Path'):
                # it's a folder
                if action == "Удалить":
                    parent = item.parent()
                    if parent:
                        p_obj = parent.data(0, Qt.UserRole)
                    else:
                        p_obj = self.scheduler.GetFolder('\\')
                    p_obj.DeleteFolder(obj.Name, 0)
            else:
                # it's a task
                task = obj
                folder = self.scheduler.GetFolder(item.text(4))
                if action == "Запустить": task.Run(None)
                elif action == "Включить": task.Enabled = True
                elif action == "Отключить": task.Enabled = False
                elif action == "Удалить": folder.DeleteTask(task.Name, 0)
            # refresh tree for all actions except maybe refresh
            self.load_tasks_tree()
        except Exception as ex:
            QMessageBox.warning(self, self.tr("Ошибка"), str(ex))
        self.load_tasks_tree()
    
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
        hive_map = {
            winreg.HKEY_CURRENT_USER: "HKEY_CURRENT_USER",
            winreg.HKEY_LOCAL_MACHINE: "HKEY_LOCAL_MACHINE"
        }
        entries = get_winlogon_entries(drive=self.current_drive)
        for arch, table in self.win_tables.items():
            filt = [e for e in entries if e['arch'] == arch]
            table.setRowCount(len(filt))
            for r, e in enumerate(filt):
                table.setItem(r, 0, QTableWidgetItem(e['name']))
                table.setItem(r, 1, QTableWidgetItem(str(e['data'])))
                hive_str = hive_map.get(e['hive'], str(e['hive']))
                loc = f"{hive_str}\\{e['location']}"
                table.setItem(r, 2, QTableWidgetItem(loc))
                table.setItem(r, 3, QTableWidgetItem(str(e['type'])))
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

    def detect_system_drives(self):
        # detect letters where Windows folder exists
        drives = []
        for letter in list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"): 
            path = f"{letter}:/Windows"
            if os.path.isdir(path):
                drives.append(f"{letter}:")
        return drives
    
    def center(self):
        frame = self.frameGeometry()
        center = self.screen().availableGeometry().center()
        frame.moveCenter(center)
        self.move(frame.topLeft())