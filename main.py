__version__ = '0.2'

#print('Инициализация...')
#import time
# _startup = time.perf_counter()
import ctypes, os
from ctypes import wintypes

# WM_CLOSE = 0x0010
# WM_SYSCOMMAND = 0x0112
# SC_CLOSE = 0xF060
# original_wnd_proc = None

# current_pid = os.getpid()

# def disable_console_close():
#     # Получаем handle текущего окна консоли
#     hwnd = ctypes.windll.kernel32.GetConsoleWindow()
#     if hwnd == 0:
#         #print("Консольное окно не обнаружено.")
#         return
    
#     # Получаем текущее меню окна
#     hMenu = ctypes.windll.user32.GetSystemMenu(hwnd, False)
#     if hMenu == 0:
#         #print("Не удалось получить меню системы.")
#         return

#     # Отключаем пункт "Закрыть"
#     SC_CLOSE = 0xF060
#     ctypes.windll.user32.RemoveMenu(hMenu, SC_CLOSE, 0x00000000)

#     # Обновляем меню консоли
#     ctypes.windll.user32.DrawMenuBar(hwnd)
#     ##print("Кнопка 'Закрыть' консоли отключена.")
# def disable_console_close_by_pid(pid):
#     # Ищем консольное окно по PID
#     hwnd = None
#     def callback(h, _):
#         nonlocal hwnd
#         process_id = ctypes.c_ulong()
#         ctypes.windll.user32.GetWindowThreadProcessId(h, ctypes.byref(process_id))
#         if process_id.value == pid:
#             hwnd = h
#             return False
#         return True

#     # Перебираем все окна
#     ctypes.windll.user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(callback), 0)

#     if hwnd:
#         # Удаляем кнопку "Закрыть"
#         hMenu = ctypes.windll.user32.GetSystemMenu(hwnd, False)
#         if hMenu:
#             SC_CLOSE = 0xF060
#             ctypes.windll.user32.RemoveMenu(hMenu, SC_CLOSE, 0x00000000)
#             ctypes.windll.user32.DrawMenuBar(hwnd)
#     #        print(f"Кнопка 'Закрыть' отключена для окна с PID {pid}.")
#     #    else:
#     #        print("Не удалось получить системное меню.")
#     #else:
#     #    print(f"Окно с PID {pid} не найдено.")=
# def enable_debug_privileges():
#     hToken = ctypes.wintypes.HANDLE()
#     TOKEN_ADJUST_PRIVILEGES = 0x0020
#     TOKEN_QUERY = 0x0008
#     SE_PRIVILEGE_ENABLED = 0x00000002

#     class LUID(ctypes.Structure):
#         _fields_ = [("LowPart", ctypes.wintypes.DWORD), ("HighPart", ctypes.wintypes.LONG)]

#     class TOKEN_PRIVILEGES(ctypes.Structure):
#         _fields_ = [("PrivilegeCount", ctypes.wintypes.DWORD),
#                     ("Privileges", LUID * 1)]

#     luid = LUID()
#     if not ctypes.windll.advapi32.LookupPrivilegeValueW(None, "SeDebugPrivilege", ctypes.byref(luid)):
#         #print("Ошибка при вызове LookupPrivilegeValueW")
#         return False

#     if not ctypes.windll.advapi32.OpenProcessToken(
#         ctypes.windll.kernel32.GetCurrentProcess(),
#         TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY,
#         ctypes.byref(hToken)
#     ):
#         return False

#     tp = TOKEN_PRIVILEGES()
#     tp.PrivilegeCount = 1
#     tp.Privileges[0].LowPart = luid.LowPart
#     tp.Privileges[0].HighPart = luid.HighPart
#     tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED

#     ctypes.windll.advapi32.AdjustTokenPrivileges(
#         hToken, False, ctypes.byref(tp), ctypes.sizeof(tp), None, None
#     )

#     if ctypes.windll.kernel32.GetLastError() != 0:
#         return False

#     return True
# def new_wnd_proc(hwnd, msg, wparam, lparam):
#     if msg == WM_CLOSE or (msg == WM_SYSCOMMAND and wparam == SC_CLOSE):
#         print("Попытка закрыть консоль заблокирована!")
#         return 0
#     return ctypes.windll.user32.CallWindowProcW(original_wnd_proc, hwnd, msg, wparam, lparam)
# def block_console_close():
#     global original_wnd_proc

#     if not enable_debug_privileges():
#         #print("Не удалось включить привилегии SeDebugPrivilege.")
#         return

#     hwnd = ctypes.windll.kernel32.GetConsoleWindow()
#     if hwnd == 0:
#         #print("Не удалось получить окно консоли.")
#         return

#     if ctypes.sizeof(ctypes.c_void_p) == 8:  # 64-битная система
#         set_window_long = ctypes.windll.user32.SetWindowLongPtrW
#     else:
#         set_window_long = ctypes.windll.user32.SetWindowLongW

#     original_wnd_proc = set_window_long(
#         hwnd, -4, ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.wintypes.HWND, ctypes.wintypes.UINT,
#                                      ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM)(new_wnd_proc)
#     )
#     if not original_wnd_proc:
#         print("Не удалось установить обработчик оконных сообщений.")
#     else:
#         print("Закрытие консоли заблокировано.")

#     atexit.register(lambda: set_window_long(hwnd, -4, original_wnd_proc))

#if __name__ == "__main__":
#    block_console_close()
#    disable_console_close()
#    disable_console_close_by_pid(current_pid)

import sys, traceback
from subprocess import Popen
from PyQt5.QtWidgets import QMainWindow, QApplication, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QPushButton, QCompleter, QLineEdit, QWidget, QMessageBox, qApp, QErrorMessage, QTableView, QListWidget, QListWidgetItem, QFileDialog, QFileIconProvider
from PyQt5.QtCore import Qt, QSize, QTimer, QThread, QCoreApplication, QUrl, QFileInfo #QTranslator, QLocale
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem, QDesktopServices #QColor
from PyQt5.QtWinExtras import QWinTaskbarButton
from modules.process_launcher import ProcessLauncher
from modules.logger import *
from modules.titles import make_title
from modules.tts import say_async
from modules.browser import open_browser
from ui.antivirus import AntivirusWindow
from ui.disk_manager import DiskManagerWindow
from ui.user_manager import UserManagerWindow
from ui.desktop_manager import DesktopManagerWindow
from ui.system_restore import SystemRestoreWindow
from ui.browser import BrowserWindow
from ui.task_manager import TaskManagerWindow
from ui.software_launcher import SoftwareLauncher
from ui.settings import SettingsWindow
from ui.about import AboutWindow
from ui.unlocker import UnlockerWindow
from ui.autoruns import AutorunsWindow
from modules.system_info import SystemInfoWorker
from PyQt5.QtCore import QThreadPool
#from fp.fp import FreeProxy
import qdarktheme
from pyqt_windows_os_light_dark_theme_window.main import Window
import qtawesome
#import qtmdi

#os.system('chcp 65001')

BANNER_TEXT = """
 __   __     _  _       _                 
 \ \ / /___ | || | ___ | | _ __  ___  _ _ 
  \ V // _ \| __ |/ -_)| || '_ \/ -_)| '_|
   |_| \___/|_||_|\___||_|| .__/\___||_|  
                          |_|               
"""

CMD_PROGRAMS_LIST = [
    'regedit',
    'taskmgr',
    'msconfig',
    'tasklist',
    'taskkill',
    'shutdown',
    'systeminfo',
    'ping'
    'sfc',
]

def is_admin():
    """
    Проверяет, запущен ли скрипт с правами администратора.
    :return: True, если скрипт запущен с правами администратора, иначе False.
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def run_as_admin():
    """
    Перезапускает скрипт с правами администратора.
    """
    if sys.argv[0] != "main.py":  # Проверка, чтобы избежать бесконечного цикла
        # Запуск скрипта с правами администратора
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)

def show_error_message(error_message):
    """Показывает окно с сообщением об ошибке."""
    error_dialog = QErrorMessage()
    error_dialog.setBaseSize(600, 500)
    error_dialog.setWindowTitle('Произошла ошибка! An error has occurred!')
    error_dialog.showMessage(error_message, 'error')
    error_dialog.exec_()

is_pyi_splash = False

try:
    import pyi_splash # type: ignore
    pyi_splash.update_text("Loading...")
    is_pyi_splash = True
except:
    pass

class VirusProtectionApp(QMainWindow, Window):
    __version__ = '0.2'

    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        #self.setWindowFlag(Qt.WindowType.WindowMinMaxButtonsHint, False)
        self.setWindowTitle(make_title('YoHelper - MultiTool for Windows 10'))
        self.setMinimumSize(900, 400)
        self.resize(1000, 700)
        #self.setMaximumSize(1600, 1000)
        fileInfo = QFileInfo(__file__)
        iconProvider = QFileIconProvider()
        icon = iconProvider.icon(fileInfo)
        self.setWindowIcon(icon)

        self.setStyleSheet("""
* {
    font-size: 14px;
    font-family: 'Consolas';
}
QPushButton {
    padding: 5px 13px;
}
#title {
    font-size: 28px;
    font-weight: bold;
}
""")

        self.software_launcher = SoftwareLauncher(self)

        self.initUI()

        self.threads = list()

        self.reason = 'Подтвердите завершение работы, нажав кнопку выхода в окне программы'
        try:
            user32 = ctypes.windll.user32
            ShutdownBlockReasonCreate = user32.ShutdownBlockReasonCreate
            ShutdownBlockReasonCreate.argtypes = [wintypes.HWND, wintypes.LPCWSTR]
            ShutdownBlockReasonCreate.restype  = wintypes.BOOL

            if not ShutdownBlockReasonCreate(int(self.winId()), self.reason):
                raise ctypes.WinError()
        except Exception:
            print(traceback.format_exc())
            pass

    def initUI(self):
        # Основной макет
        main_layout = QVBoxLayout()

        premain_layout = QVBoxLayout()

        self.title = QLabel('YoHelper')
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet('font-size: 48px;font-weight: bold;font-family: "Comic Sans MS";')
        premain_layout.addWidget(self.title)

        mains_layout = QHBoxLayout()

        side_layout = QVBoxLayout()

        # Система
        self.system_group = QGroupBox()
        self.system_group.setTitle(self.tr("Система"))
        system_layout = QVBoxLayout()
        self.system_info_table = QTableView()
        self.system_info_table.setEditTriggers(QTableView.NoEditTriggers)
        self.system_info_table.setSortingEnabled(False)
        self.system_info_table.setShowGrid(False)
        self.system_info_table.verticalHeader().hide()
        self.system_info_table.horizontalHeader().hide()
        self.system_info_table.resizeColumnsToContents()
        self.system_info_table.resizeRowsToContents()
        system_layout.addWidget(self.system_info_table)
        self.system_group.setLayout(system_layout)

        # Системная информация
        self.system_info_group = QGroupBox(self.tr("Информация о системе"))
        system_info_layout = QVBoxLayout()
        self.system_info_label = QLabel("CPU: --%, RAM: --%")
        self.disk_info_label = QLabel("C:\\")
        self.update_system_info_button = QPushButton(self.tr("Обновить"))
        self.update_system_info_button.clicked.connect(self.update_system_info)
        os_icon = QLabel()
        #os_icon.setPixmap(get_os_icon())
        system_info_layout.addWidget(os_icon)
        system_info_layout.addWidget(self.system_info_label)
        system_info_layout.addWidget(self.disk_info_label)
        system_info_layout.addWidget(self.update_system_info_button)
        self.system_info_group.setLayout(system_info_layout)
        side_layout.addWidget(self.system_info_group)

        module_buttons = [
            ("Разблокировка ограничений", self.tr("Разблокировка ограничений"), self.open_unlocker, "mdi.lock-open"),
            ("Редактор автозагрузки", self.tr("Редактор автозагрузки"), self.open_autoruns, "mdi.file-document-edit-outline"),
            ("Диспетчер задач", self.tr("Диспетчер задач"), self.open_task_manager, "mdi.format-list-bulleted-square"),
            ("Запуск сторонних программ", self.tr("Запуск сторонних программ"), self.software_launcher.show, "mdi.application-cog"),
            ("Браузер", self.tr("Браузер"), lambda: self.open_browser(), "mdi.web"),
            ("Среда восстановления", self.tr("Среда восстановления"), self.open_bootim, "mdi.menu"),
            ("Управление дисками", self.tr("Управление дисками"), self.open_disk_manager, "mdi.harddisk"),
            ("Управление пользователями", self.tr("Управление пользователями"), self.open_user_manager, "mdi.account-group"),
            ("Персонализация", self.tr("Персонализация"), self.open_desktop_manager, "mdi.image"),
            #("Точка восстановления", self.tr("Точка восстановления"), self.open_system_restore, "mdi.restore"),
            ("Антивирус", self.tr("Антивирус"), self.open_antivirus, "mdi.shield-bug"),
            #("Обход Ютуба", self.tr("Обход Ютуба"), self.open_youtube, "mdi.shield"),
        ]
        self.module_buttons_list = QListWidget(self)
        self.module_buttons_list.setMaximumWidth(310)
        self.module_buttons_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.module_buttons_list_layout = QVBoxLayout()
        self.module_buttons_list.setLayout(self.module_buttons_list_layout)
        self.module_buttons = []
        for original_text, text, action, icon in module_buttons:
            btn = QPushButton(text)
            btn.setIcon(qtawesome.icon(icon))
            btn.setIconSize(QSize(24, 24))
            btn.clicked.connect(action)
            btn.setMinimumHeight(35)
            btn.setContentsMargins(0, 10, 0, 10)
            btn.icon_ = icon
            btn.original_text = original_text

            item = QListWidgetItem()
            item.setSizeHint(QSize(self.module_buttons_list.width(), 35))
            self.module_buttons_list.addItem(item)
            self.module_buttons_list.setItemWidget(item, btn)

            self.module_buttons.append(btn)

        side_layout.addWidget(self.module_buttons_list)

        exit_button = QPushButton(self.tr("Выход"))
        exit_button.setIcon(qtawesome.icon("mdi.exit-to-app"))
        exit_button.clicked.connect(qApp.quit)
        exit_button.icon_ = "mdi.exit-to-app"
        exit_button.original_text = "Выход"
        self.module_buttons.append(exit_button)
        side_layout.addWidget(exit_button)

        # Логирование
        self.log_group = QGroupBox(self.tr("Логирование"))
        log_layout = QVBoxLayout()
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        setup_logger(self.log_text_edit)
        self.log_text_edit.setHtml(f'<pre style="font-size:8pt;white-space: pre;">{BANNER_TEXT}</pre>')
        self.log_text_edit.setStyleSheet("font-size: 11px;")
        log_layout.addWidget(self.log_text_edit)
        self.log_group.setLayout(log_layout)

        # Поле запуска команд
        command_layout = QHBoxLayout()
        self.command_input = QLineEdit()
        completer = QCompleter(CMD_PROGRAMS_LIST, self.command_input)
        self.command_input.setCompleter(completer) 
        self.command_input.setPlaceholderText(self.tr("Введите команду..."))
        self.command_input.returnPressed.connect(self.run_command)
        self.command_file_run_button = QPushButton(self.tr("Обзор"))
        self.command_file_run_button.clicked.connect(self.run_file_command)
        self.command_run_button = QPushButton(self.tr("Запустить"))
        self.command_run_button.clicked.connect(self.run_command)
        command_layout.addWidget(self.command_input)
        command_layout.addWidget(self.command_file_run_button)
        command_layout.addWidget(self.command_run_button)

        other_layout = QHBoxLayout()
        other_buttons = [
            ("Настройки", self.tr("Настройки"), self.open_settings),
            ("Сайт NedoTube", self.tr("Сайт NedoTube"), lambda: self.open_browser('https://nedotube.vercel.app/')),
            ("О программе", self.tr("О программе"), self.open_about),
        ]

        self.other_buttons = []
        for original_text, text, action in other_buttons:
            btn = QPushButton(text)
            btn.clicked.connect(action)
            btn.original_text = original_text
            self.other_buttons.append(btn)
            other_layout.addWidget(btn)

        # Добавление компонентов в макеты
        mains_layout.addLayout(premain_layout)
        mains_layout.addLayout(side_layout)

        main_layout.addLayout(mains_layout)
        premain_layout.addWidget(self.system_group)
        premain_layout.addLayout(command_layout)
        premain_layout.addWidget(self.log_group)
        premain_layout.addLayout(other_layout)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.thread_pool = QThreadPool.globalInstance()
        self.defer_system_info()

        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(1000)

        self.taskbar_button = QWinTaskbarButton(self)
        self.taskbar_button.setWindow(self.windowHandle())
        self.taskbar_button.setOverlayIcon(QIcon(":/loading.png"));
        self.taskbar_progress = self.taskbar_button.progress()
        self.taskbar_progress.setVisible(True)
        self.taskbar_progress.setValue(50)
        self.taskbar_progress.show()

        self.move(QApplication.desktop().screen().rect().center() - self.rect().center())
        
        self.settings_window = SettingsWindow(self)

    def on_timer(self):
        self.update_info()
    def update_info(self):
        """Обновляет информацию о системе."""
        from modules.system_info import get_disk_info, get_load_info
        self.system_info_label.setText(get_load_info())
        self.disk_info_label.setText(get_disk_info())
    def defer_system_info(self):
        """Показываем плейсхолдер, а потом асинхронно подгружаем"""
        # очистить таблицу / показать «загрузка…»
        model = QStandardItemModel(1, 2)
        model.setHorizontalHeaderLabels([self.tr("Параметр"), self.tr("Значение")])
        model.setItem(0, 0, QStandardItem("…"))
        model.setItem(0, 1, QStandardItem("…"))
        self.system_info_table.setModel(model)
        self.update_system_info_button.setDisabled(True)

        worker = SystemInfoWorker()
        worker.signals.finished.connect(self.on_system_info_ready)
        worker.signals.loaded.connect(self.on_system_info_loaded)
        self.thread_pool.start(worker)
        
    def on_system_info_ready(self, info: dict):
        self.on_system_info_loaded(info)
        self.update_system_info_button.setDisabled(False)

    def on_system_info_loaded(self, info: dict):
        """Слот: получили данные — строим модель"""
        model = QStandardItemModel(len(info), 2)
        model.setHorizontalHeaderLabels([self.tr("Параметр"), self.tr("Значение")])
        for i, (k, v) in enumerate(info.items()):
            model.setItem(i, 0, QStandardItem(k))
            model.setItem(i, 1, QStandardItem(str(v)))
        self.system_info_table.setModel(model)
        self.system_info_table.resizeColumnsToContents()

    def update_system_info(self):
        self.defer_system_info()
    def run_command(self):
        """Запускает команду из текстового поля."""
        command = self.command_input.text().strip()
        if not command:
            return
        self.command_input.clear()
        t = self.tr("Введена комманда")
        log(f"<b>{t}:</b> {command}")

        self.threads.append(QThread())
        self.process_launcher = ProcessLauncher(self, command)
        self.process_launcher.moveToThread(self.threads[-1])
        self.process_launcher.process_output.connect(self.handle_process_output)
        self.threads[-1].started.connect(self.process_launcher.launch_process)
        self.threads[-1].start()
    def run_file_command(self):
        # Открываем диалог выбора файла
        file_path, _ = QFileDialog.getOpenFileName(None, self.tr("Выберите файл для открытия"))

        # Если файл выбран
        if file_path:
            # Преобразуем путь в QUrl
            url = QUrl.fromLocalFile(file_path)
            # Запускаем файл с помощью системы
            QDesktopServices.openUrl(url)
    def handle_process_output(self, stdout, stderr):
        """Обрабатывает вывод процесса."""
        if stdout:
            t = self.tr("Вывод")
            log(f"<b>{t}:</b>")
            text = ""
            for line in stdout.splitlines():
                text += line + "<br>\n"
            log(text)
        if stderr:
            t = self.tr("Ошибка")
            log(f"<b>{t}:</b>", ERROR)
            text = ""
            for line in stdout.splitlines():
                text += line + "<br>\n"
            log(text, ERROR)
    def open_autoruns(self):
        """Открывает окно Редактора автозагрузки."""
        btn: QPushButton = self.sender()
        btn.setDisabled(True)
        qApp.processEvents()
        self.autoruns_window = AutorunsWindow(self)
        self.autoruns_window.show()
        btn.setDisabled(False)
    def open_unlocker(self):
        """Открывает окно Разблокировки ограничений."""
        btn: QPushButton = self.sender()
        btn.setDisabled(True)
        qApp.processEvents()
        self.unlocker_window = UnlockerWindow(self)
        self.unlocker_window.show()
        btn.setDisabled(False)
    def open_antivirus(self):
        """Открывает окно Антивируса."""
        btn: QPushButton = self.sender()
        btn.setDisabled(True)
        qApp.processEvents()
        self.antivirus_window = AntivirusWindow(self)
        self.antivirus_window.show()
        btn.setDisabled(False)
    def open_disk_manager(self):
        btn: QPushButton = self.sender()
        btn.setDisabled(True)
        qApp.processEvents()
        """Открывает окно Управления дисками."""
        self.disk_manager_window = DiskManagerWindow(self)
        self.disk_manager_window.show()
        btn.setDisabled(False)
    def open_user_manager(self):
        btn: QPushButton = self.sender()
        btn.setDisabled(True)
        qApp.processEvents()
        """Открывает окно Управления пользователями."""
        self.user_manager_window = UserManagerWindow(self)
        self.user_manager_window.show()
        btn.setDisabled(False)
    def open_desktop_manager(self):
        """Открывает окно Управления обоями."""
        btn: QPushButton = self.sender()
        btn.setDisabled(True)
        qApp.processEvents()
        self.desktop_manager_window = DesktopManagerWindow(self)
        self.desktop_manager_window.show()
        btn.setDisabled(False)
    def open_system_restore(self):
        """Открывает окно Точки восстановления."""
        btn: QPushButton = self.sender()
        btn.setDisabled(True)
        qApp.processEvents()
        self.system_restore_window = SystemRestoreWindow(self)
        self.system_restore_window.show()
        btn.setDisabled(False)
    def open_browser(self, url = None):
        """Открывает окно Встроенного браузера."""
        btn: QPushButton = self.sender()
        btn.setDisabled(True)
        qApp.processEvents()
        if url is None:
            url = "yobrowser://new-tab"
            try:
                self.browser_window = BrowserWindow(self, url)
                self.browser_window.show()
            except Exception as e:
                print(traceback.format_exc())
                log('Ошибка открытия браузера: ' + str(e), ERROR)
                pass
        else:
            msg = QMessageBox()
            msg.setWindowTitle(self.tr("Открытие ссылки"))
            msg.setText(self.tr('Открыть ссылку во встроенном браузере? Нажмите "Нет", чтобы открыть в браузере по умолчанию.'))
            msg.setInformativeText(url)
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            msg.setDefaultButton(QMessageBox.Yes)
            ret = msg.exec_()
            if ret == QMessageBox.Yes:
                self.browser_window = BrowserWindow(self, url)
                self.browser_window.show()
            elif ret == QMessageBox.No:
                open_browser(url)
        btn.setDisabled(False)
    def open_task_manager(self):
        """Открывает окно Диспетчера задач."""
        btn: QPushButton = self.sender()
        btn.setDisabled(True)
        qApp.processEvents()
        self.task_manager_window = TaskManagerWindow(self)
        self.task_manager_window.show()
        btn.setDisabled(False)
    def open_settings(self):
        """Открывает окно Настроек."""
        btn: QPushButton = self.sender()
        btn.setDisabled(True)
        qApp.processEvents()
        self.settings_window.show()
        btn.setDisabled(False)
    def open_about(self):
        """Открывает окно О программе."""
        btn: QPushButton = self.sender()
        btn.setDisabled(True)
        qApp.processEvents()
        self.about_window = AboutWindow(self)
        self.about_window.show()
        btn.setDisabled(False)
    def open_bootim(self):
        """Запуск bootim.exe"""
        btn: QPushButton = self.sender()
        btn.setDisabled(True)
        msg = QMessageBox()
        msg.setWindowTitle(self.tr("Среда восстановления"))
        msg.setText(self.tr('Вы уверены, что хотите открыть среду восстановления? Это перезагрузит компьютер в меню восстановления.\n\nПеред этим сохраните все несохранённые данные!'))
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        ret = msg.exec_()
        if ret == QMessageBox.Yes:
            Popen("shutdown.exe /r /o /t 0", shell=False)
            self.hide()
        btn.setDisabled(False)

    def update_button_icons(self):
        """Обновляет цвет иконок кнопок в зависимости от темы."""
        for btn in self.module_buttons:
            icon = qtawesome.icon(btn.icon_)
            btn.setIcon(icon)

    def retranslateUi(self):
        self.system_group.setTitle(self.tr("Система"))
        self.log_group.setTitle(self.tr("Логирование"))
        self.system_info_group.setTitle(self.tr("Информация о системе"))
        self.update_system_info_button.setText(self.tr("Обновить"))
        self.command_run_button.setText(self.tr("Запустить"))
        self.command_input.setPlaceholderText(self.tr("Введите команду..."))
        for btn in self.module_buttons:
            btn.setText(self.tr(btn.original_text))
        for btn in self.other_buttons:
            btn.setText(self.tr(btn.original_text))
        self.software_launcher.retranslateUi()
        if hasattr(self, "antivirus_window"):
            self.antivirus_window.retranslateUi()
        if hasattr(self, "task_manager_window"):
            self.task_manager_window.retranslateUi()

    #def make_process_critical(self):  # Ненадёжный вариант, т.к. вирусы могут крашнуть систему из-за простого закрытия программы :P
    #    """Устанавливает процесс как критический."""
    #    try:
    #        ntdll = ctypes.WinDLL("ntdll")
    #        hproc = ctypes.windll.kernel32.GetCurrentProcess()
    #        status = ntdll.RtlSetProcessIsCritical(1, 0, 0)
    #        if status != 0:
    #            raise Exception("Не удалось установить процесс как критический.")
    #    except Exception as e:
    #        log(f"Ошибка защиты процесса:\n{str(e)}", ERROR)

    def closeEvent(self, event):
        """Предотвращает закрытие программы."""
        
        #QMessageBox.warning(self, self.tr("Предупреждение"), self.tr("Закрытие программы заблокировано! Используйте кнопку выхода."))
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("YoHelper")
        msg.setText(self.tr("Закрытие программы заблокировано! Используйте кнопку выхода."))
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        try:
            user32 = ctypes.windll.user32
            ShutdownBlockReasonCreate = user32.ShutdownBlockReasonCreate
            ShutdownBlockReasonCreate.argtypes = [wintypes.HWND, wintypes.LPCWSTR]
            ShutdownBlockReasonCreate.restype  = wintypes.BOOL

            if not ShutdownBlockReasonCreate(int(msg.winId()), self.reason):
                raise ctypes.WinError()
        except Exception:
            print(traceback.format_exc())
            pass
        event.ignore()

def main():
    def trying_close(**k):
        log(window.tr("Произошла попытка завершения процесса программы!"), WARNING)

    #free_proxy = urlparse(FreeProxy(anonym=True).get())
    #print(free_proxy)
    #proxy = QNetworkProxy()
    #proxy.setType(QNetworkProxy.HttpProxy)
    #proxy.setHostName(free_proxy.hostname)
    #proxy.setPort(free_proxy.port)
    #QNetworkProxy.setApplicationProxy(proxy)

    app = QApplication(sys.argv)
    qdarktheme.setup_theme()
    
    #say_async("Примечание: Чтобы сделать окно поверх всех окон, нажмите сочетание клавиш: Shift + F10")

    QCoreApplication.setQuitLockEnabled(True)  # Включаем блокировку выхода
    window = VirusProtectionApp()
    app.aboutToQuit.connect(trying_close)

    if is_pyi_splash:
        pyi_splash.close()

    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    error_code = ctypes.windll.kernel32.GetLastError()
    if error_code != 0:
        log(f"Error setup the handler: {error_code}", ERROR)

    if not is_admin():
        print("Attempt to run with administrator rights...")
        run_as_admin()
    else:
        print(BANNER_TEXT)
        try:
            if is_pyi_splash:
                pyi_splash.update_text("Hi!")
            main()
        except Exception as e:
            error_message = traceback.format_exc()
            print(error_message)
            show_error_message(error_message)
            os.system('pause')
