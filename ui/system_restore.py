from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QLabel, QPushButton, QWidget
from PyQt5.QtCore import Qt
from modules.system_restore import create_restore_point, restore_to_point
from modules.titles import make_title
from pyqt_windows_os_light_dark_theme_window.main import Window

class SystemRestoreWindow(QMainWindow, Window):
    def __init__(self, parent = None):
        super().__init__()
        self.setParent(parent)
        self.setWindowTitle(make_title(self.parent().tr("Точка восстановления")))
        self.setFixedSize(400, 300)
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        self.statusbar = self.statusBar()

        layout = QVBoxLayout()
        self.header_label = QLabel(self.tr("Управление точками восстановления"))
        self.header_label.setObjectName("title")
        self.create_restore_button = QPushButton(self.tr("Создать точку восстановления"))
        self.create_restore_button.clicked.connect(self.create_restore_point)

        self.restore_button = QPushButton(self.tr("Восстановить систему"))
        self.restore_button.clicked.connect(self.restore_system)

        layout.addWidget(self.header_label)
        layout.addWidget(self.create_restore_button)
        layout.addWidget(self.restore_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def create_restore_point(self):
        """Создает точку восстановления."""
        result = create_restore_point()
        self.statusbar.showMessage(result)

    def restore_system(self):
        """Восстанавливает систему к точке восстановления."""
        result = restore_to_point()
        self.statusbar.showMessage(result)

    def retranslateUi(self):
        self.setWindowTitle(make_title(self.parent().tr("Точка восстановления")))
        self.header_label.setText(self.tr("Управление точками восстановления"))
        self.create_restore_button.setText(self.tr("Создать точку восстановления"))
        self.restore_button.setText(self.tr("Восстановить систему"))
