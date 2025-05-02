from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QProgressBar, QDialog, QInputDialog, QMessageBox, QPushButton, QWidget, QListWidgetItem
from PyQt5.QtCore import Qt
try:
    from psutil import disk_partitions, disk_usage
except ImportError:
    # empty
    def disk_partitions(**k):
        return None
from modules.disk_manager import *
from modules.titles import make_title
from pyqt_windows_os_light_dark_theme_window.main import Window

class DiskManagerWindow(QMainWindow, Window):
    def __init__(self, parent = None):
        super().__init__()
        self.setParent(parent)
        self.setWindowTitle(make_title(self.parent().tr("Управление дисками")))
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        layout = QVBoxLayout()

        self.header_label = QLabel(self.parent().tr("Управление дисками"))
        self.header_label.setObjectName("title")

        self.click_label = QLabel(self.tr("Нажмите на диск, чтобы открыть меню"))

        self.disk_table = QTableWidget()
        self.disk_table.setColumnCount(6)
        self.disk_table.setHorizontalHeaderLabels([self.tr("Буква"), self.tr("Наименование"), "BitLocker", self.tr("Занято/Свободно"), self.tr("Статус"), self.tr("Тип")])
        self.disk_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.disk_table.setSelectionBehavior(self.disk_table.SelectRows)
        self.disk_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.disk_table.itemClicked.connect(self.open_disk_menu)
        self.disk_table.verticalHeader().hide()

        layout.addWidget(self.header_label)
        layout.addWidget(self.click_label)
        layout.addWidget(self.disk_table)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.resize(750, 400)
        self.center()

        self.refresh_disk_list()

    def center(self):
        """Центрирует окно по центру экрана."""
        frame_geometry = self.frameGeometry()
        center_point = self.screen().availableGeometry().center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def open_disk_menu(self, item: QListWidgetItem):
        row = item.row()
        disk_letter = self.disk_table.item(row, 0).text()
        disk_name = self.disk_table.item(row, 1).text()

        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("Управление диском") + " " + disk_letter)
        dialog.setFixedSize(300, 100)
        dialog.move(self.cursor().pos())
        layout = QVBoxLayout()
        hlayout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(get_disk_icon(disk_letter).scaled(32, 32))
        icon_label.setMaximumSize(32, 32)
        letter_label = QLabel(f"{disk_letter} {disk_name}")
        letter_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        letter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        unlock_bitlocker_button = QPushButton(self.tr("Разблокировать диск c BitLocker"))
        unlock_bitlocker_button.clicked.connect(lambda: self.unlock_bitlocker(disk_letter))
        hlayout.addWidget(icon_label)
        hlayout.addWidget(letter_label)
        layout.addLayout(hlayout)
        layout.addWidget(unlock_bitlocker_button)
        dialog.setLayout(layout)
        dialog.exec()

    def unlock_bitlocker(self, disk_letter):
        """Разблокирует BitLocker на указанном диске."""
        credential, ok = QInputDialog.getText(self, self.tr("Разблокировка диска с BitLocker"), self.tr("Введите пароль или ключ востановления") + ":")
        if ok:
            result, ok = unlock_bitlocker(disk_letter, credential)
            if ok:
                QMessageBox.information(self, self.parent().tr("Успешно"), result)
            else:
                QMessageBox.warning(self, self.parent().tr("Ошибка"), result)
            self.refresh_disk_list()

    def refresh_disk_list(self):
        """Обновляет список дисков."""
        partitions = disk_partitions()
        self.disk_table.setRowCount(len(partitions))

        if partitions:
            for row, partition in enumerate(partitions):
                # Диск
                item = QTableWidgetItem(partition.device)
                item.setIcon(QIcon(get_disk_icon(partition.device, 16)))
                self.disk_table.setItem(row, 0, item)

                # Название (имя устройства)
                self.disk_table.setItem(row, 1, QTableWidgetItem(get_volume_name(partition.device)))

                # Проверка на защиту BitLocker
                bitlocker_status = is_bitlocker_protected(partition.device)  
                self.disk_table.setItem(row, 2, QTableWidgetItem(self.parent().tr("Да") if bitlocker_status == True else self.parent().tr("Нет") if bitlocker_status == False else "N/A"))

                # Прогресс бар
                progress = QProgressBar()
                self.disk_table.setCellWidget(row, 3, progress)

                disk_status = check_disk_status(partition.mountpoint)
                if disk_status:
                    usage = disk_usage(partition.mountpoint)
                    progress.setValue(int((usage.used / usage.total) * 100))
                else:
                    progress.setDisabled(True)
                
                # Доступность
                self.disk_table.setItem(row, 4, QTableWidgetItem("ОК" if disk_status else self.parent().tr("Недоступно")))
                
                # Тип
                self.disk_table.setItem(row, 5, QTableWidgetItem(get_disk_type(partition.mountpoint)))

        self.disk_table.resizeColumnsToContents()
        self.disk_table.resizeRowsToContents()

    def retranslateUi(self):
        self.setWindowTitle(make_title(self.parent().tr("Управление дисками")))
        self.header_label.setText(self.parent().tr("Управление дисками"))
        self.click_label.setText(self.tr("Нажмите на диск, чтобы открыть меню"))
        self.disk_table.setHorizontalHeaderLabels([self.tr("Буква"), self.tr("Наименование"), "BitLocker", self.tr("Занято/Свободно"), self.tr("Статус"), self.tr("Тип")])