from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QStackedWidget,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView,
    QAbstractItemView, QDesktopWidget
)
import qtawesome
import os, subprocess

from modules.monitor import *

class ProcessMonitorWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Монитор процесса")
        self.resize(600, 150)

        self.thread = None

        # Stacked widget
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Page select
        self.page_select = QWidget(); self._build_select_page(); self.stack.addWidget(self.page_select)
        # Page monitor
        self.page_monitor = QWidget(); self._build_monitor_page(); self.stack.addWidget(self.page_monitor)
        self.stack.setCurrentWidget(self.page_select)

    def _build_select_page(self):
        layout = QVBoxLayout()
        self.page_select.setLayout(layout)
        layout.addStretch()

        top = QLabel("Выберите .exe файл для мониторинга (Монитор отслеживает дочерние процессы и создаваемые ими файлы/папки)")
        top.setWordWrap(True)
        top.setAlignment(Qt.AlignCenter)
        layout.addWidget(top)

        file_h = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Путь к .exe файлу")
        browse_btn = QPushButton("Обзор")
        browse_btn.clicked.connect(self.browse_file)
        file_h.addWidget(self.file_input)
        file_h.addWidget(browse_btn)
        layout.addLayout(file_h)

        uac_h = QHBoxLayout()
        self.uac_label = QLabel("")  # shield
        uac_h.addWidget(self.uac_label)
        uac_h.addStretch()
        layout.addLayout(uac_h)

        start_btn = QPushButton("Начать мониторинг")
        start_btn.clicked.connect(self.start_monitoring)
        layout.addWidget(start_btn)

        layout.addStretch()

        self.file_input.textChanged.connect(self.update_uac_icon)

    def _build_monitor_page(self):
        layout = QVBoxLayout()
        self.page_monitor.setLayout(layout)

        top_h = QHBoxLayout()
        self.status_label = QLabel("Ожидание")
        top_h.addWidget(self.status_label)
        top_h.addStretch()
        stop_btn = QPushButton("Остановить мониторинг")
        stop_btn.clicked.connect(self.stop_monitoring)
        top_h.addWidget(stop_btn)
        layout.addLayout(top_h)

        # Table columns: Date/time (grey), +time (s) dark green, Action, Path (full), Risk %, Actions (buttons)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Время", "+сек", "Действие", "Путь", "Риск", "Действия"])
        self.table.verticalHeader().setVisible(False)  # remove row numbers
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Custom)
        header.resizeSection(2, 150)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        # compact rows
        self.table.setStyleSheet("QTableWidget::item { padding: 2px; }")
        layout.addWidget(self.table)

    def browse_file(self):
        p, _ = QFileDialog.getOpenFileName(self, "Выберите .exe", "", "Executable (*.exe);;All files (*.*)")
        if p:
            self.file_input.setText(p)

    def update_uac_icon(self):
        path = self.file_input.text().strip()
        if path and os.path.isfile(path) and requires_elevation_exe(path):
            self.uac_label.setText("🛡 Требуется запуск от имени администратора")
        else:
            self.uac_label.setText("")

    def start_monitoring(self):
        exe_path = self.file_input.text().strip()
        if not exe_path or not os.path.isfile(exe_path):
            QMessageBox.warning(self, "Ошибка", "Выберите корректный .exe файл.")
            return
        need_elev = requires_elevation_exe(exe_path)
        if need_elev:
            ans = QMessageBox.question(self, "Требуются права администратора",
                                       "Файл, по всей видимости, требует повышения прав. Запустить с повышением?",
                                       QMessageBox.Yes | QMessageBox.No)
            if ans != QMessageBox.Yes:
                return

        self.resize(1400, 800)
        qr = self.frameGeometry()  
        cp = QDesktopWidget().availableGeometry().center()  
        qr.moveCenter(cp)  
        self.move(qr.topLeft())

        # prepare watch dirs: exe directory, TEMP, Desktop, APPDATA
        watch_dirs = []
        try:
            ed = os.path.dirname(exe_path)
            if ed: watch_dirs.append(ed)
            t = os.environ.get("TEMP", "")
            if t: watch_dirs.append(t)
            desk = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
            if desk: watch_dirs.append(desk)
            ad = os.environ.get("APPDATA", "")
            if ad: watch_dirs.append(ad)
        except Exception:
            pass
        watch_dirs = [d for d in watch_dirs if d and os.path.exists(d)]

        # switch UI
        self.table.setRowCount(0)
        self.status_label.setText("Запуск...")
        self.stack.setCurrentWidget(self.page_monitor)

        # start thread
        self.thread = MonitorThread(exe_path, require_elevate=need_elev, watch_dirs=watch_dirs)
        self.thread.event_signal.connect(self.on_log_event)
        self.thread.status_signal.connect(self.status_label.setText)
        self.thread.finished_signal.connect(self.on_monitor_finished)
        self.thread.start()
        # initial message
        self.add_table_row({
            "time": now_str(),
            "since": 0,
            "action": "Мониторинг запущен",
            "path": exe_path,
            "pid": None,
            "risk": 0
        })

    def stop_monitoring(self):
        if hasattr(self, "thread") and self.thread:
            try:
                self.thread.stop()
            except Exception:
                pass

        self.stack.setCurrentWidget(self.page_select)
        self.status_label.setText("Остановлен (завершение потока продолжается в фоне)")
        self.resize(600, 150)
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def on_monitor_finished(self):
        self.add_table_row({
            "time": now_str(),
            "since": round(seconds_since(self.thread.start_ts), 3) if getattr(self.thread, "start_ts", None) else 0.000,
            "action": "Мониторинг завершён",
            "path": "",
            "pid": None,
            "risk": 0
        })
        self.status_label.setText("Остановлен")

    def on_log_event(self, ev):
        # ev is dict: time, since, action, path, pid, extra, risk
        self.add_table_row(ev)

    def add_table_row(self, ev):
        row = self.table.rowCount()
        self.table.insertRow(row)
        # Date/time (grey)
        item_time = QTableWidgetItem(ev.get("time", now_str()))
        item_time.setForeground(QBrush(QColor(120, 120, 120)))
        item_time.setFlags(item_time.flags() ^ Qt.ItemIsEditable)
        self.table.setItem(row, 0, item_time)
        # +time (dark green)
        item_since = QTableWidgetItem(str(ev.get("since", '')))
        item_since.setForeground(QBrush(QColor(0, 100, 0)))
        item_since.setFlags(item_since.flags() ^ Qt.ItemIsEditable)
        self.table.setItem(row, 1, item_since)
        # Action
        item_act = QTableWidgetItem(ev.get("action", ""))
        item_act.setFlags(item_act.flags() ^ Qt.ItemIsEditable)
        self.table.setItem(row, 2, item_act)
        # Path full
        path_txt = ev.get("path", "") or ""
        item_path = QTableWidgetItem(path_txt)
        item_path.setFlags(item_path.flags() ^ Qt.ItemIsEditable)
        self.table.setItem(row, 3, item_path)
        # Risk percent with background
        risk = int(ev.get("risk", 0))
        item_risk = QTableWidgetItem(str(risk) + "%")
        item_risk.setFlags(item_risk.flags() ^ Qt.ItemIsEditable)
        item_risk.setBackground(risk_brush(risk))
        self.table.setItem(row, 4, item_risk)
        # Actions column (buttons)
        action_widget = QWidget()
        ah = QHBoxLayout()
        ah.setContentsMargins(0, 0, 0, 0)
        ah.setSpacing(4)
        # depending on action, add appropriate buttons
        if ev.get("action", "").startswith("Создан файл") or ev.get("action", "").startswith("Создана папка"):
            # open folder + copy path
            btn_open = QPushButton()
            btn_open.setIcon(qtawesome.icon("mdi.folder"))
            btn_open.setProperty("path", path_txt)
            btn_open.clicked.connect(lambda _, p=path_txt: self.open_folder(p))
            btn_copy = QPushButton()
            btn_copy.setIcon(qtawesome.icon("mdi.content-copy"))
            btn_copy.clicked.connect(lambda _, p=path_txt: self.copy_path(p))
            ah.addWidget(btn_open)
            ah.addWidget(btn_copy)
        elif ev.get("action", "").startswith("Установлено") or "автозапуска" in ev.get("action", "").lower() or ev.get("action", "").startswith("Удалён ключ"):
            # registry buttons
            btn_openreg = QPushButton()
            btn_openreg.setIcon(qtawesome.icon("mdi.cube-off-outline"))
            btn_openreg.clicked.connect(lambda _, p=path_txt: self.open_regedit(p))
            btn_copy = QPushButton()
            btn_copy.setIcon(qtawesome.icon("mdi.content-copy"))
            btn_copy.clicked.connect(lambda _, p=path_txt: self.copy_path(p))
            ah.addWidget(btn_openreg)
            ah.addWidget(btn_copy)
        elif ev.get("action", "").lower().startswith("создан процесс") or ev.get("action", "").lower().startswith("процесс"):
            btn_copy = QPushButton()
            btn_copy.setIcon(qtawesome.icon("mdi.content-copy"))
            btn_copy.clicked.connect(lambda _, p=path_txt: self.copy_path(p))
            ah.addWidget(btn_copy)
        else:
            # default: copy
            if path_txt:
                btn_copy = QPushButton()
                btn_copy.setIcon(qtawesome.icon("mdi.content-copy"))
                btn_copy.clicked.connect(lambda _, p=path_txt: self.copy_path(p))
                ah.addWidget(btn_copy)

        action_widget.setLayout(ah)
        self.table.setCellWidget(row, 5, action_widget)

        # compact row height
        self.table.setRowHeight(row, 26)
        # autoscroll
        self.table.scrollToBottom()

    # action handlers
    def open_folder(self, path):
        """
        Если path указывает на файл — откроет Проводник и выделит файл.
        Если path указывает на папку — откроет эту папку.
        """
        if not path:
            return
        # Если path — несуществующий, попробуем извлечь папку
        if os.path.isdir(path):
            folder = path
            try:
                os.startfile(folder)
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось открыть папку:\n{e}")
            return

        # если это файл (или путь к файлу)
        folder = os.path.dirname(path)
        if not folder or not os.path.exists(folder):
            QMessageBox.warning(self, "Ошибка", f"Путь не найден: {path}")
            return

        # Используем explorer.exe с аргументом /select,"<path>"
        try:
            # Make sure path is absolute and properly quoted
            abspath = os.path.abspath(path)
            subprocess.Popen(['explorer', '/select,', abspath])
        except Exception as e:
            # fallback: открыть папку
            try:
                os.startfile(folder)
            except Exception:
                QMessageBox.warning(self, "Ошибка", f"Не удалось открыть папку или выделить файл:\n{e}")

    def copy_path(self, path):
        QApplication.clipboard().setText(path)
        QMessageBox.information(self, "Скопировано", "Путь скопирован в буфер обмена.")

    def open_regedit(self, path):
        # Best-effort: open regedit. Selecting exact key programmatically is non-trivial; here we just open regedit.
        try:
            subprocess.Popen(["regedit.exe"])
            QMessageBox.information(self, "Regedit", "Regedit открыт — скопируйте путь и найдите нужный ключ вручную.")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось запустить regedit:\n{e}")