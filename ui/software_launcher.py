import os
import traceback
import zipfile
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QMessageBox, QWidget, QScrollArea
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QThread, QByteArray, QObject, QSize
from PyQt5.QtGui import QIcon, QPixmap
from modules.titles import make_title
from modules.browser import open_browser
from modules.logger import log
from ui.browser import BrowserWindow
from pyqt_windows_os_light_dark_theme_window.main import Window
import qtawesome

# Ссылки для загрузки программ (Скоро список будет перемещён в онлайн формат)
SOFTWARE_URLS = {
    "SimpleUnlocker": {
        "url": "https://mirror.ds1nc.ru/su/release/simpleunlocker_release.zip",
        "path": "simpleunlocker_release/SU.exe",
    },
    "SimpleUnlocker (c утилитами)": {
        "url": "https://mirror.ds1nc.ru/su/release/simpleunlocker_release-u.zip",
        "path": "simpleunlocker_release/SU.exe",
    },
    "ProcessHacker": {
        "url": "https://raw.githubusercontent.com/ZhenyaYoratt/YoHelper/refs/heads/main/hosted_softwares/processhacker-2.39-bin.zip",
        "path": "x64/ProcessHacker.exe",
        "icon": "https://www.softportal.com/scr/14593/icons/process_hacker_72.png"
    },
    "Explorer++": {
        "url": "https://download.explorerplusplus.com/stable/1.4.0/explorerpp_x64.zip",
        "path": "Explorer++.exe",
        "icon": "https://explorerplusplus.com/images/favicon.ico"
    },
    "AnVir Task Manager": {
        "url": "https://www.anvir.net/downloads/anvirrus.zip",
        "path": "anvirrus-portable/AnVir.exe",
        "zip": "anvirrus-portable.zip",
        "icon": "https://www.softportal.com/scr/9259/icons/anvir_task_manager_72.png"
    },
    "Autoruns": {
        "url": "https://download.sysinternals.com/files/Autoruns.zip",
        "path": "Autoruns.exe",
        "icon": "https://www.softportal.com/scr/7891/icons/autoruns_72.png"
    },
    "RegCool": {
        "url": "https://kurtzimmermann.com/files/RegCoolX64.zip",
        "path": "RegCool.exe",
        "icon": "https://www.softportal.com/scr/47453/icons/regcool_64.png"
    },
    "RegAlyzer": {
        "url": "https://raw.githubusercontent.com/ZhenyaYoratt/NedoHelper/refs/heads/main/hosted_softwares/RegAlyzerPortable.zip",
        "path": "RegAlyzerPortable/RegAlyzerPortable.exe",
        "icon": "https://cdn2.portableapps.com/RegAlyzerPortable_128.png"
    },
    "Total Commander": {
        "url": "https://totalcommander.ch/1103/tcmd1103x32_64.exe",
        "icon": "https://www.softportal.com/scr/33/icons/total_commander_72.png"
    },
    "CCleaner": {
        "url": "https://download.ccleaner.com/portable/ccsetup631.zip",
        "path": "CCleaner.exe",
        "icon": "https://www.softportal.com/scr/14259/icons/ccleaner_portable_72.png"
    },
    "ZSoft Uninstaller": {
        "url": "https://download2.portableapps.com/portableapps/ZSoftUninstallerPortable/ZSoftUninstallerPortable_2.5_Rev_3.paf.exe",
        "icon": "https://cdn2.portableapps.com/ZSoftUninstallerPortable_128.png"
    },
    "Command Prompt Portable": {
        "url": "https://download2.portableapps.com/portableapps/CommandPromptPortable/CommandPromptPortable_2.6.paf.exe",
        "icon": "https://cdn2.portableapps.com/CommandPromptPortable_128.png"
    },
    "7-Zip": {
        "url": "https://download2.portableapps.com/portableapps/7-ZipPortable/7-ZipPortable_24.09.paf.exe",
        "icon": "https://cdn2.portableapps.com/7-ZipPortable_128.png"
    },
    "ccPortable": {
        "url": "https://download2.portableapps.com/portableapps/ccPortable/ccPortable_6.31.11415_online.paf.exe",
        "icon": "https://cdn2.portableapps.com/ccPortable_128.png"
    },
    "DTaskManager": {
        "url": "https://download2.portableapps.com/portableapps/DTaskManagerPortable/DTaskManagerPortable_1.57.31.paf.exe",
        "icon": "https://cdn2.portableapps.com/DTaskManagerPortable_128.png"
    },
    "WizTree": {
        "url": "https://download2.portableapps.com/portableapps/WizTreePortable/WizTreePortable_4.20.paf.exe",
        "icon": "https://cdn2.portableapps.com/WizTreePortable_128.png"
    },
    "Run-Command Portable": {
        "url": "https://download2.portableapps.com/portableapps/Run-CommandPortable/Run-CommandPortable_6.23.paf.exe",
        "icon": "https://cdn2.portableapps.com/Run-CommandPortable_128.png"
    },
    "Process Explorer": {
        "url": "https://download2.portableapps.com/portableapps/ProcessExplorerPortable/ProcessExplorerPortable_17.06_online.paf.exe",
        "icon": "https://cdn2.portableapps.com/ProcessExplorerPortable_128.png"
    },
    "Process Monitor": {
        "url": "https://download2.portableapps.com/portableapps/ProcessMonitorPortable/ProcessMonitorPortable_4.01_online.paf.exe",
        "icon": "https://cdn2.portableapps.com/ProcessMonitorPortable_128.png"
    }
}

SOFTWARE_DIR = "software"

class DownloadSoftwareWorker(QObject):
    progress = pyqtSignal(int)  # Для прогресса
    completed = pyqtSignal(str)  # Для завершения
    error = pyqtSignal(str)  # Для ошибок
    set_max = pyqtSignal(int)

    def __init__(self, parent, url, save_path):
        super().__init__()
        self.setParent(parent)
        self.url = url
        self.save_path = save_path
        self.manager = QNetworkAccessManager()
        self.manager.finished.connect(self.on_finished)

    def run(self):
        request = QNetworkRequest(QUrl(self.url))
        self.reply = self.manager.get(request)
        self.reply.downloadProgress.connect(self.on_download_progress)

    def on_download_progress(self, bytes_received, bytes_total):
        if bytes_total > 0:
            self.set_max.emit(bytes_total)
            self.progress.emit(bytes_received)

    def on_finished(self, reply: QNetworkReply):
        if reply.error() == QNetworkReply.NoError:
            with open(self.save_path, "wb") as file:
                file.write(reply.readAll())
            self.completed.emit(self.save_path)
        else:
            self.error.emit(str(reply.errorString()))
        reply.deleteLater()

class AsyncQIcon(QObject):
    icon_downloaded = pyqtSignal(QIcon)

    def __init__(self, url, placeholder_icon=None, parent=None):
        super().__init__(parent)
        self.url = url
        self.placeholder_icon = placeholder_icon or QIcon()
        self.manager = QNetworkAccessManager(parent)

    def download_icon(self):
        request = QNetworkRequest(QUrl(self.url))
        self.reply = self.manager.get(request)
        self.reply.finished.connect(self.on_finished)

    def on_finished(self):
        reply = self.reply
        if reply.error() == QNetworkReply.NetworkError.NoError:
            pixmap = QPixmap()
            data: QByteArray = reply.readAll()
            if pixmap.loadFromData(data):
                icon = QIcon(pixmap)
                self.icon_downloaded.emit(icon)
            else:
                self.icon_downloaded.emit(self.placeholder_icon)
        else:
            self.icon_downloaded.emit(self.placeholder_icon)
        reply.deleteLater()

class SoftwareLauncher(QMainWindow, Window):
    def __init__(self, parent = None):
        super().__init__()
        self.setParent(parent)
        self.setWindowTitle(make_title(self.parent().tr("Запуск сторонних программ")))
        self.setMinimumSize(400, 250)
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        # Основной виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Заголовок
        header_label = QLabel(self.parent().tr("Запуск сторонних программ"))
        header_label.setObjectName("title")
        layout.addWidget(header_label)

        # Добавляем область прокрутки
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Виджет содержимого для области прокрутки
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)
        scroll_layout = QVBoxLayout(scroll_content)

        placeholder_icon = QIcon("ui/icons/placeholder.png")

        # Кнопки для запуска и удаления программ
        self.buttons = {}
        for program_name in SOFTWARE_URLS.keys():
            button_layout = QHBoxLayout()
            button = QPushButton(program_name)
            if SOFTWARE_URLS[program_name].get('icon'):
                icon = AsyncQIcon(SOFTWARE_URLS[program_name]['icon'], placeholder_icon, self.parent())
                icon.icon_downloaded.connect(lambda icon, b=button: b.setIcon(icon))
                icon.download_icon()
                button.setIcon(placeholder_icon)
                button.setIconSize(QSize(24, 24))
            button.clicked.connect(lambda checked, p=program_name: self.launch_program(p))
            button_layout.addWidget(button)

            delete_button = QPushButton()
            delete_button.setIcon(qtawesome.icon("fa5s.trash", color="red"))
            delete_button.clicked.connect(lambda checked, p=program_name: self.delete_program(p))
            delete_button.setMaximumSize(28, 28)
            button_layout.addWidget(delete_button)

            scroll_layout.addLayout(button_layout)
            self.buttons[program_name] = (button, delete_button)
            self.update_delete_button_state(program_name)

        # Кнопка для предложения программы
        self.actions_buttons_layout = QHBoxLayout()
        self.suggest_button = QPushButton(self.tr("Предложить программу"))
        self.suggest_button.setIcon(qtawesome.icon("fa5s.plus", color="green"))
        self.suggest_button.clicked.connect(self.suggest_program)
        self.folder_button = QPushButton(self.tr("Открыть папку"))
        self.folder_button.setIcon(qtawesome.icon("fa5s.folder-open"))
        self.folder_button.clicked.connect(self.open_folder)
        self.actions_buttons_layout.addWidget(self.suggest_button)
        self.actions_buttons_layout.addWidget(self.folder_button)
        layout.addLayout(self.actions_buttons_layout)

    def open_folder(self):
        try:
            os.startfile(SOFTWARE_DIR)
        except FileNotFoundError:
            QMessageBox.critical(self, self.tr("Ошибка"), self.tr("Папка не найдена"))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Ошибка"), str(e))

    def retranslateUi(self):
        self.setWindowTitle(make_title(self.parent().tr("Запуск сторонних программ")))
        self.suggest_button.setText(self.tr("Предложить программу"))
        self.folder_button.setText(self.tr("Открыть папку"))

    def suggest_program(self):
        url = "https://github.com/ZhenyaYoratt/YoHelper/discussions/new?category=suggest-programs"
        msg = QMessageBox()
        msg.setWindowTitle(self.parent().tr("Открытие ссылки"))
        msg.setText(self.parent().tr('Открыть ссылку во встроенном браузере? Нажмите "Нет", чтобы открыть в браузере по умолчанию.'))
        msg.setInformativeText(url)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Yes)
        ret = msg.exec_()
        if ret == QMessageBox.Yes:
            self.browser_window = BrowserWindow(self, url)
            self.browser_window.show()
        elif ret == QMessageBox.No:
            open_browser(url)

    def update_delete_button_state(self, program_name):
        program = SOFTWARE_URLS.get(program_name)
        program_dir = os.path.abspath(os.path.join(SOFTWARE_DIR, os.path.basename(program['url']).replace('.zip', '')))
        delete_button = self.buttons[program_name][1]
        delete_button.setEnabled(os.path.exists(program_dir))

    def launch_program(self, program_name):
        program = SOFTWARE_URLS.get(program_name)
        program_dir = os.path.abspath(os.path.join(SOFTWARE_DIR, os.path.basename(program['url']).replace('.zip', '')))

        # Проверяем наличие программы
        if not os.path.exists(program_dir):
            reply = QMessageBox.question(
                self,
                self.tr("Программа отсутствует"),
                self.tr("Программа {0} отсутствует. Хотите загрузить ее?").format(program_name),
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.download_program(program_name)
                return
            else:
                return

        # Запускаем программу
        try:
            if program['url'].endswith(".exe"):
                try:
                    os.startfile(os.path.abspath(os.path.join(SOFTWARE_DIR, os.path.basename(program['url']))))
                except Exception as e:
                    QMessageBox.critical(self, self.parent().tr("Ошибка"), self.tr("Не удалось запустить программу {0}.\n{1}\n\nПопробуйте удалить и скачать завоно.").format(program_name, e))
            else:
                path = os.path.join(program_dir, program['path'])
                os.startfile(path)
        except Exception as e:
            QMessageBox.critical(self, self.parent().tr("Ошибка"), self.tr("Не удалось запустить программу {0}.\n{1}\n\nПопробуйте удалить и скачать завоно.").format(program_name, e))

    def download_program(self, program_name):
        program = SOFTWARE_URLS.get(program_name)

        if not program:
            QMessageBox.critical(self, self.parent().tr("Ошибка"), self.tr("Ссылка для загрузки {0} отсутствует.").format(program_name))
            return

        os.makedirs(SOFTWARE_DIR, exist_ok=True)
        file_path = os.path.join(SOFTWARE_DIR, os.path.basename(program['url']))

        # Настраиваем поток
        progress_bar = QProgressBar()
        self.centralWidget().layout().addWidget(progress_bar)
        progress_bar.setValue(0)
        progress_bar.setFormat(self.parent().tr("Скачивание") + " " + program_name + "... %p%")

        self.worker = DownloadSoftwareWorker(self, program['url'], file_path)
        self.worker.set_max.connect(progress_bar.setMaximum)
        self.worker.progress.connect(progress_bar.setValue)
        self.worker.completed.connect(lambda path: self.on_download_completed(path, program_name, program, progress_bar))
        self.worker.error.connect(lambda error: self.on_download_error(error, progress_bar))
        thread = QThread(self.parent())
        self.worker.moveToThread(thread)
        thread.started.connect(self.worker.run)
        thread.start()

    def on_download_completed(self, file_path: str, program_name: str, program: dict, progress_bar: QProgressBar):
        progress_bar.deleteLater()

        # Если это архив, распаковываем
        if file_path.endswith(".zip"):
            try:
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    extract_path = os.path.abspath(os.path.join(SOFTWARE_DIR, os.path.basename(program['url']).replace('.zip', '')))
                    os.makedirs(extract_path, exist_ok=True)
                    zip_ref.extractall(extract_path)
                os.remove(file_path)  # Удаляем архив после распаковки
                print(program)
                if "zip" in program:
                    # Снова распокавать распокованный zip файл
                    try:
                        file_path = os.path.join(SOFTWARE_DIR, os.path.basename(program['url']).replace('.zip', ''), program['zip'])
                        with zipfile.ZipFile(file_path, "r") as zip_ref:
                            extract_path = os.path.join(SOFTWARE_DIR, os.path.basename(program['url']).replace('.zip', ''), program['zip'].replace('.zip', ''))
                            os.makedirs(extract_path, exist_ok=True)
                            zip_ref.extractall(extract_path)
                        os.remove(file_path)
                    except Exception as e:
                        msg = QMessageBox()
                        msg.setDetailedText(traceback.format_exc())
                        msg.critical(self, self.parent().tr("Ошибка"), self.tr("Ошибка второй распаковки программы {0}: {1}").format(program_name, e))
                        return
                QMessageBox.information(self, self.parent().tr("Успешно"), self.tr("Программа {0} успешно загружена и распакована.").format(program_name))
            except Exception as e:
                msg = QMessageBox()
                msg.setDetailedText(traceback.format_exc())
                msg.critical(self, self.parent().tr("Ошибка"), self.tr("Ошибка распаковки программы {0}: {1}").format(program_name, e))
                return
        else:
            QMessageBox.information(self, self.parent().tr("Успешно"), self.tr("Программа {0} успешно загружена.").format(program_name))
        self.launch_program(program_name)
        self.update_delete_button_state(program_name)

    def on_download_error(self, error_message, progress_bar: QProgressBar):
        progress_bar.deleteLater()
        QMessageBox.critical(self, self.parent().tr("Ошибка"), self.tr("Ошибка загрузки") + ": " + error_message)

    def delete_program(self, program_name):
        program = SOFTWARE_URLS.get(program_name)
        program_dir = os.path.abspath(os.path.join(SOFTWARE_DIR, os.path.basename(program['url']).replace('.zip', '')))

        if os.path.exists(program_dir):
            try:
                for root, dirs, files in os.walk(program_dir, topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
                os.rmdir(program_dir)
                QMessageBox.information(self, self.parent().tr("Успех"), self.tr("Программа {0} успешно удалена.").format(program_name))
            except Exception as e:
                QMessageBox.critical(self, self.parent().tr("Ошибка"), self.tr("Не удалось удалить программу {0}.\n{1}\n\nВозможно, программа запущена.").format(program_name, e))
        else:
            QMessageBox.information(self, self.parent().tr("Информация"), self.tr("Программа {0} не найдена.").format(program_name))
        self.update_delete_button_state(program_name)
