from PyQt5.QtCore import Qt, QThread
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QProgressBar, QListWidget, QFileDialog, QWidget, QCheckBox, QListWidgetItem
from modules.antivirus import delete_file, UpdateWorker, ScanThread, DATABASES_FORLDER
from modules.titles import make_title
from pyqt_windows_os_light_dark_theme_window.main import Window
import os

application_path = os.path.dirname(os.path.abspath(__file__))

class AntivirusWindow(QMainWindow, Window):
    def __init__(self, parent = None):
        super().__init__()
        self.setParent(parent)
        self.setWindowTitle(make_title(self.parent().tr("Антивирус")))
        self.setMaximumSize(800, 1000)
        self.resize(450, 350)
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        self.statusbar = self.statusBar()
        self.statusbar.showMessage(self.parent().tr("Готов к работе"))

        layout = QVBoxLayout()

        self.header_label = QLabel(self.parent().tr("Антивирус"))
        self.header_label.setObjectName("title")

        top_layout = QHBoxLayout()
        self.start_scan_button = QPushButton(self.tr("Сканировать папку"))
        self.start_scan_button.clicked.connect(self.start_scan)
        self.update_db_button = QPushButton(self.tr("Обновить базы данных"))
        self.update_db_button.clicked.connect(self.update_db)
        top_layout.addWidget(self.start_scan_button)
        top_layout.addWidget(self.update_db_button)

        self.results_label = QLabel(self.tr("Результаты сканирования")+"")
        self.results_list = QListWidget()

        self.progress_label = QLabel()

        bottom_layout = QHBoxLayout()

        self.select_all_checkbox = QCheckBox(self.tr("Выделить всё"))
        self.select_all_checkbox.stateChanged.connect(self.select_all_items)
        self.delete_button = QPushButton(self.tr("Удалить выделенные"))
        self.delete_button.clicked.connect(self.delete_selected_items)
        self.quarantine_button = QPushButton(self.tr("Переместить в карантин"))
        self.quarantine_button.clicked.connect(self.quarantine_selected_items)

        bottom_layout.addWidget(self.select_all_checkbox)
        bottom_layout.addWidget(self.delete_button)
        bottom_layout.addWidget(self.quarantine_button)

        self.progress_bar = QProgressBar()
        self.statusbar.addPermanentWidget(self.progress_bar)

        layout.addWidget(self.header_label)
        layout.addLayout(top_layout)
        layout.addWidget(self.results_label)
        layout.addWidget(self.results_list)
        layout.addWidget(self.progress_label)
        layout.addLayout(bottom_layout)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def update_db(self, after_start_scan = False, directory_scan = None):
        self.statusbar.showMessage(self.tr("Обновление базы данных..."))
        self.progress_bar.setValue(0)
        self.worker = UpdateWorker()
        self.worker.set_max.connect(self.progress_bar.setMaximum)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.completed.connect(lambda: (
            self.statusbar.showMessage(self.tr("Базы данных обновлены!")),
            self.progress_bar.setMaximum(1),
            self.progress_bar.reset(),
            (self.start_scan(directory = directory_scan) if after_start_scan else None)
        ))
        thread = QThread(self.parent())
        self.worker.moveToThread(thread)
        thread.started.connect(self.worker.run)
        thread.start()

    def start_scan(self, directory = None):
        """Начинает сканирование выбранной папки."""
        if not directory:
            directory = QFileDialog.getExistingDirectory(self, self.tr("Выберите папку для сканирования"))
        if not directory:
            self.statusbar.showMessage(self.parent().tr("Операция отменена пользователем"))
            return
        
        # Проверяем, существует ли папка с файлами
        if not os.path.exists(DATABASES_FORLDER) or (os.path.exists(DATABASES_FORLDER) and len(os.listdir(DATABASES_FORLDER)) == 0):
            self.update_db(after_start_scan = True, directory_scan = directory)

        self.statusbar.showMessage(self.tr("Сканирование..."))
        self.progress_bar.setValue(0)
        self._thread = QThread(self)
        self._worker = ScanThread(directory)
        self._worker.moveToThread(self._thread)
        self._worker.set_max.connect(self.progress_bar.setMaximum)
        self._worker.progress.connect(self.progress_bar.setValue)
        self._worker.progress_text.connect(self.progress_label.setText)
        self._worker.suspicious_file.connect(self.results_list.addItem)
        self._worker.completed.connect(self.complete_scan)
        self._thread.started.connect(self._worker.run)
        self._thread.start()

    def complete_scan(self, suspicious_files):
        self.progress_bar.setMaximum(1)
        self.progress_bar.reset()
        self.progress_label.setText("")
        if not suspicious_files:
            self.statusbar.showMessage(self.tr("Угроз не обнаружено."))
        else:
            self.statusbar.showMessage(self.tr("Сканирование завершено."))
            self.results_list.clear()
            for file in suspicious_files:
                item = QListWidgetItem(file)
                item.setCheckState(Qt.Unchecked)
                self.results_list.addItem(item)

    def select_all_items(self, state):
        for index in range(self.results_list.count()):
            item = self.results_list.item(index)
            item.setCheckState(Qt.Checked if state == Qt.Checked else Qt.Unchecked)

    def delete_selected_items(self):
        for index in range(self.results_list.count() - 1, -1, -1):
            item = self.results_list.item(index)
            if item.checkState() == Qt.Checked:
                delete_file(item.text())
                self.results_list.takeItem(index)
        self.statusbar.showMessage(self.tr("Выделенные файлы удалены."))

    def quarantine_selected_items(self):
        quarantine_folder = os.path.join(application_path, 'quarantine')
        if not os.path.exists(quarantine_folder):
            os.makedirs(quarantine_folder)
        for index in range(self.results_list.count() - 1, -1, -1):
            item = self.results_list.item(index)
            if item.checkState() == Qt.Checked:
                file_path = item.text()
                quarantine_path = os.path.join(quarantine_folder, os.path.basename(file_path))
                os.rename(file_path, quarantine_path)
                self.results_list.takeItem(index)
        self.statusbar.showMessage(self.tr("Выделенные файлы перемещены в карантин."))

    def retranslateUi(self):
        self.setWindowTitle(make_title(self.parent().tr("Антивирус")))
        self.header_label.setText(self.parent().tr("Антивирус"))
        self.results_label.setText(self.tr("Результаты сканирования"))
        self.update_db_button.setText(self.tr("Обновить базы данных"))
        self.start_scan_button.setText(self.tr("Сканировать папку"))
        self.select_all_checkbox.setText(self.tr("Выделить всё"))
        self.delete_button.setText(self.tr("Удалить выделенные"))
        self.quarantine_button.setText(self.tr("Переместить в карантин"))