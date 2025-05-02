from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QLabel, QListWidget, QLineEdit, QPushButton, QWidget, QInputDialog, QMessageBox, QListWidgetItem, QDialog
from PyQt5.QtCore import Qt, QTimer, QDateTime
from modules.user_manager import list_users, add_user, delete_user, set_password
from modules.titles import make_title
from modules.logger import *
from pyqt_windows_os_light_dark_theme_window.main import Window

class UserManagerWindow(QMainWindow, Window):
    def __init__(self, parent = None):
        super().__init__()
        self.setParent(parent)
        self.setWindowTitle(make_title(self.parent().tr("Управление пользователями")))
        self.setFixedSize(500, 500)
        self.setWindowFlags(Qt.WindowType.Dialog)

        self.statusbar = self.statusBar()
        self.statusbar.showMessage(self.parent().tr("Готов к работе"))

        layout = QVBoxLayout()
        self.header_label = QLabel(self.parent().tr("Управление пользователями"))
        self.header_label.setObjectName("title")
        label = QLabel(self.tr("Нажмите на пользователя, чтобы просмотреть информацию о нём"))
        self.users_view = QListWidget()
        self.users_view.itemClicked.connect(self.show_user_info)

        # Добавление пользователя
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(self.tr("Имя пользователя"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(self.tr("Пароль"))
        add_user_button = QPushButton(self.tr("Добавить пользователя"))
        add_user_button.clicked.connect(self.add_user)

        layout.addWidget(self.header_label)
        layout.addWidget(label)
        layout.addWidget(self.users_view)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(add_user_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.center()

        self.update_users()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_users)
        self.timer.start(5000)
    def center(self):
        """Центрирует окно по центру экрана."""
        frame_geometry = self.frameGeometry()
        center_point = self.screen().availableGeometry().center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def closeEvent(self, a0):
        self.timer.stop()
        return super().closeEvent(a0)

    def show_user_info(self, item: QListWidgetItem):
        user = item.data(Qt.ItemDataRole.UserRole)
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("Информация о пользователе {0}").format(user.name))
        dialog.setFixedSize(400, 200)
        dialog.move(self.cursor().pos())
        layout = QVBoxLayout()
        username_label = QLabel(self.tr("Имя пользователя") + ": " + user.name)
        terminal_label = QLabel(self.tr("Терминал") + ": " + (user.terminal if user.terminal else 'Неизвестно'))
        host_label = QLabel(self.tr("Хост") + ": " + (user.host if user.host else 'Неизвестно'))
        started_label = QLabel(self.tr("Запущен") + ": " + QDateTime.fromSecsSinceEpoch(int(user.started)).toString())
        delete_user_button = QPushButton(self.tr("Удалить пользователя"))
        delete_user_button.clicked.connect(lambda: self.delete_user(user.name))
        set_password_button = QPushButton(self.tr("Установить пароль"))
        set_password_button.clicked.connect(lambda: self.set_password(user.name))
        layout.addWidget(username_label)
        layout.addWidget(terminal_label)
        layout.addWidget(host_label)
        layout.addWidget(started_label)
        layout.addWidget(delete_user_button)
        layout.addWidget(set_password_button)
        dialog.setLayout(layout)
        dialog.exec()

    def update_users(self):
        users = list_users()
        self.users_view.clear()
        for user in users:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, user)
            item.setText(user.name)
            self.users_view.addItem(item)

    def add_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        ok, result = add_user(username, password)
        self.statusbar.showMessage(result)
        self.username_input.clear()
        self.password_input.clear()
        if ok:
            QMessageBox.information(self, self.parent().tr("Успешно"), self.tr("Пользователь {0} успешно добавлен. Однако требуется инициализация пользователя, чтобы показался в списке.").format(username))
        else:
            QMessageBox.warning(self, self.parent().tr("Ошибка"), self.tr("Ошибка добавления пользователя {0}.").format(username))
        self.update_users()

    def delete_user(self, username: str):
        if QMessageBox.question(self, self.parent().tr("Подтверждение"), self.tr("Удалить пользователя {0}?").format(username), QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            ok, result = delete_user(username)
            self.statusbar.showMessage(result)
            self.update_users()
            if ok:
                QMessageBox.information(self, self.parent().tr("Успешно"), self.tr("Пользователь {0} успешно удален. Может потребоваться перезагрузка компьютера.").format(username))
            else:
                QMessageBox.warning(self, self.parent().tr("Ошибка"), self.tr("Ошибка удаления пользователя {0}.").format(username))

    def set_password(self, username: str):
        password, ok = QInputDialog.getText(self, "Установка пароля", self.tr("Введите новый пароль для пользователя {0}").format(username))
        if ok:
            ok, result = set_password(username, password)
            self.statusbar.showMessage(result)
            self.update_users()
            if ok:
                QMessageBox.information(self, self.parent().tr("Успешно"), self.tr("Пароль для пользователя {0} успешно установлен.").format(username))
            else:
                QMessageBox.warning(self, self.parent().tr("Ошибка"), self.tr("Ошибка установки пароля для пользователя {0}.").format(username))
