from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMenu, QLineEdit, QTableWidget, QTableWidgetItem, QStatusBar, QWidget, QTabWidget
from PyQt5.QtCore import Qt, QThread, QDateTime, pyqtSignal, QObject, QRunnable, QThreadPool, QPoint
from PyQt5.QtGui import QIcon, QColor
from modules.task_manager import get_process_list, get_process_type, Process
from modules.titles import make_title
try:
    from psutil import boot_time
except ImportError:
    boot_time = lambda: -1

def parse_precents(value):
    if value is not None and value > 100:
        return f"{int(value)}%WTF"
    return f"{value:.1f}%" if value is not None else "0.0%"

def parse_create_time(value):
    return QDateTime.fromSecsSinceEpoch(int(value)).toString(Qt.DateFormat.ISODate)

def set_item_color(item: QTableWidgetItem, value):
    if value is not None:
        color_intensity = min(255, int(value * 2.55))
        item.setBackground(QColor(255, 255 - color_intensity, 0, min(255, 20 + color_intensity)))

class ProcessListWorker(QObject):
    process_list_updated = pyqtSignal(list)
    update_interval = 1

    def __init__(self):
        super().__init__()
        self._running = True

    def run(self):
        while self._running:
            self.process_list_updated.emit(get_process_list())
            QThread.msleep(int(self.update_interval * 1000))

    def stop(self):
        self._running = False

class IconLoader(QObject):
    icon_ready = pyqtSignal(int, QIcon)  # row, icon

class IconTask(QRunnable):
    def __init__(self, process: Process, row: int, loader: IconLoader):
        super().__init__()
        self.process = process
        self.row = row
        self.loader = loader

    def run(self):
        pixmap = self.process.get_process_icon()
        if pixmap:
            icon = QIcon(pixmap)
            self.loader.icon_ready.emit(self.row, icon)

class TaskManagerWindow(QMainWindow):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle(make_title(self.parent().tr("Диспетчер задач")))
        self.resize(1200, 700)
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setStyleSheet(self.styleSheet() + "QPushButton { padding: 0px 4px; }")

        self.tabs = QTabWidget(self)

        layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel(self.parent().tr("Диспетчер задач")))

        view_button = QPushButton(self.tr("Вид"))
        view_button.setMenu(QMenu(self))
        view_button.menu().addAction(self.tr("Обновить сейчас"), self.refresh_process_list)
        update_interval_menu = view_button.menu().addMenu(self.tr("Скорость обновления"))
        update_interval_menu.addAction(self.tr("Очень быстро — 0.1 сек"), lambda: self.set_update_interval(0.5))
        update_interval_menu.addAction(self.tr("Быстро — 0.5 секунд"), lambda: self.set_update_interval(0.5))
        update_interval_menu.addAction(self.tr("Обычная — 1 секунд"), lambda: self.set_update_interval(1))
        update_interval_menu.addAction(self.tr("Низкая — 3 секунд"), lambda: self.set_update_interval(5))
        update_interval_menu.addAction(self.tr("Очень низкая — 5 секунд"), lambda: self.set_update_interval(5))
        update_interval_menu.addAction(self.tr("Черепаха — 10 секунд"), lambda: self.set_update_interval(10))
        view_button.menu().addSeparator()
        hide_critical_processes_action = view_button.menu().addAction(self.tr("Скрыть критические процессы"), self.toggle_critical_processes)
        hide_critical_processes_action.setCheckable(True)
        hide_system_processes_action = view_button.menu().addAction(self.tr("Скрыть системные процессы"), self.toggle_system_processes)
        hide_system_processes_action.setCheckable(True)
        hide_system_processes_action.setChecked(True)

        # Поиск
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(self.tr('Поиск процесса, файла, названия, PID...'))
        self.search_bar.setClearButtonEnabled(True)
        self.search_bar.textChanged.connect(lambda text: self.filter_process_list(text))

        boot_time_label = QLabel(self.tr("Время загрузки BIOS") + ": " + QDateTime.fromSecsSinceEpoch(int(boot_time())).toString(Qt.DateFormat.ISODate))

        top_layout.addWidget(view_button)
        top_layout.addWidget(self.search_bar)
        top_layout.addWidget(boot_time_label)

        # Таблица процессов
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(9)
        self.process_table.setHorizontalHeaderLabels([self.tr("Имя процесса"), self.tr("ЦП"), self.tr("ОЗУ"), self.tr("Состояние"), "PID", self.tr("Тип"), self.tr("Создано"), self.tr("Описание"), self.tr("Название заголовка")])
        self.process_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.process_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.process_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.process_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.process_table.customContextMenuRequested.connect(self.on_table_context_menu)

        layout.addLayout(top_layout)
        layout.addWidget(self.process_table)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.tabs.addTab(central_widget, self.tr("Процессы"))
        #label = QLabel('В разработке')
        #label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        #self.tabs.addTab(label, self.tr("Производительность"))
        self.setCentralWidget(self.tabs)

        self.icon_loader = IconLoader()
        self.icon_loader.icon_ready.connect(self.on_icon_ready)
        self.thread_pool = QThreadPool.globalInstance()

        # Таймер обновления списка процессов
        self._worker = ProcessListWorker()
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._worker.process_list_updated.connect(lambda process_list: self.update_process_list(process_list))
        self._thread.started.connect(self._worker.run)
        self._thread.start()
        
        self.process_list_ui = []
        self.process_list = []

        self.hide_critical_processes = False
        self.hide_system_processes = True

        self.setStatusBar(QStatusBar())

        self.update_process_list(get_process_list())

        for col in range(self.process_table.columnCount()):
            if col != 1 or col != 2:
                self.process_table.resizeColumnToContents(col)
        self.process_table.resizeRowsToContents()
        self.process_table.setColumnWidth(1, 65)
        self.process_table.setColumnWidth(2, 65)

    def on_table_context_menu(self, pos: QPoint):
        # получаем индекс ячейки, где кликнули
        index = self.process_table.indexAt(pos)
        if not index.isValid():
            return

        row = index.row()
        proc = self.process_list_ui[row]

        menu = QMenu(self.process_table)
        kill_action     = menu.addAction(self.tr("Завершить процесс"))
        suspend_action  = menu.addAction(self.tr("Приостановить"))
        resume_action   = menu.addAction(self.tr("Возобновить"))

        action = menu.exec(self.process_table.viewport().mapToGlobal(pos))
        if action == kill_action:
            proc.kill()
        elif action == suspend_action:
            proc.suspend()
        elif action == resume_action:
            proc.resume()

    def closeEvent(self, a0):
        self._worker.stop()
        self._thread.quit()
        self._thread.wait()
        return super().closeEvent(a0)
    
    def set_update_interval(self, interval):
        self._worker.update_interval = interval

    def toggle_critical_processes(self):
        self.hide_critical_processes = not self.hide_critical_processes
        self.filter_process_list()

    def toggle_system_processes(self):
        self.hide_system_processes = not self.hide_system_processes
        self.filter_process_list()

    def filter_process_list(self, search_text = None):
        """Фильтрует список процессов по имени процесса, имя файла или PID."""
        if search_text:
            self.process_list_ui = [process for process in self.process_list if search_text.lower() in process.window_title.lower() + ";" + process.name.lower() + ";" + process.description.lower() + ";" + str(process.pid)]
        if self.hide_critical_processes:
            self.process_list_ui = [process for process in self.process_list_ui if process.process_type != 'critical']
        if self.hide_system_processes:
            self.process_list_ui = [process for process in self.process_list_ui if process.process_type != 'system']
        return self.refresh_process_list()
    
    def update_process_list(self, process_list):
        self.process_list = process_list
        if self.search_bar.text():
            self.filter_process_list(self.search_bar.text())
        else:
            self.process_list_ui = self.process_list
        self.filter_process_list()

    def refresh_process_list(self):
        """Обновляет список процессов."""
        self.process_table.setUpdatesEnabled(False)

        count = len(self.process_list)
        count_ui = len(self.process_list_ui)
        self.statusBar().showMessage(self.tr("Всего: {0}. Показано процессов: {1} (из них скрыты: {2})").format(str(count), str(count_ui), str(count - count_ui)))
        self.process_table.setRowCount(count_ui)
        for row, process in enumerate(self.process_list_ui):
            process: Process = process
            item = QTableWidgetItem(process.name)
            self.process_table.setItem(row, 0, item)
            cpu_item = QTableWidgetItem(parse_precents(process.cpu_percent) if process.pid != 0 else None)
            self.process_table.setItem(row, 1, cpu_item)
            ram_item = QTableWidgetItem(parse_precents(process.memory_percent) if process.pid != 0 else None)
            self.process_table.setItem(row, 2, ram_item)
            self.process_table.setItem(row, 3, QTableWidgetItem(Process.STATUS[process.status]))
            self.process_table.setItem(row, 4, QTableWidgetItem(str(process.pid)))
            self.process_table.setItem(row, 5, QTableWidgetItem(Process.PROCESS_TYPE[process.process_type]))
            self.process_table.setItem(row, 6, QTableWidgetItem(parse_create_time(process.create_time)))
            self.process_table.setItem(row, 7, QTableWidgetItem(process.description))
            self.process_table.setItem(row, 8, QTableWidgetItem(process.window_title))

            task = IconTask(process, row, self.icon_loader)
            self.thread_pool.start(task)
            
            # Set row color based on process type
            if process.process_type == 'system':
                for col in range(self.process_table.columnCount()):
                    self.process_table.item(row, col).setBackground(QColor(36, 164, 255, 60))  # Light blue
                    #self.process_table.item(row, col).setForeground(QColor(173, 216, 230))  # Light blue
            elif process.process_type == 'critical':
                for col in range(self.process_table.columnCount()):
                    self.process_table.item(row, col).setBackground(QColor(255, 165, 0, 60))  # Orange
            
            set_item_color(cpu_item, process.cpu_percent)
            set_item_color(ram_item, process.memory_percent)
        
        self.process_table.setUpdatesEnabled(True)
        self.process_table.resizeRowsToContents()

    def on_icon_ready(self, row: int, icon: QIcon) -> None:
        item = self.process_table.item(row, 0)
        if item:
            item.setIcon(icon)

    def retranslateUi(self):
        self.setWindowTitle(make_title(self.parent().tr("Диспетчер задач")))
        self.process_table.setHorizontalHeaderLabels([self.tr("Имя процесса"), self.tr("ЦП"), self.tr("ОЗУ"), self.tr("Состояние"), "PID", self.tr("Тип"), self.tr("Действия с процессом"), self.tr("Создано"), self.tr("Описание"), self.tr("Название заголовка")])