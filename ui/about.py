from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QApplication, QMessageBox
from PyQt5.QtCore import Qt
from modules.titles import make_title
from modules.browser import open_browser
from ui.browser import BrowserWindow
from pyqt_windows_os_light_dark_theme_window.main import Window

class AboutWindow(QMainWindow, Window):
    def __init__(self, parent = None):
        super().__init__()
        self.setParent(parent)
        self.setWindowTitle(make_title(self.tr("О программе")))
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.resize(500, 270)
        self.initUI()

    def initUI(self):

        layout = QVBoxLayout()

        self.header_label = QLabel(self.tr("О программе"), self)
        self.header_label.setObjectName('title')
        layout.addWidget(self.header_label)
        
        buttons_layout = QHBoxLayout()

        self.version_label = QLabel(self.tr("Версия программы: ") + self.parent().__version__, self)
        self.version_label.setMargin(10)
        self.version_label.setObjectName('version')
        layout.addWidget(self.version_label)

        self.about_label = QLabel(self)
        self.about_label.setTextFormat(Qt.TextFormat.AutoText | Qt.TextFormat.RichText)
        self.about_label.setText(self.tr("""
Программа мультул позволит вам удалить вирусы (наверное) и восстановить Windows 10 до её идеального состояния. Эта программа разработана эксклюзивно для YouTube-канала "НЕДОХАКЕРЫ Lite".

Для получения дополнительной информации посетите <a href="https://github.com/ZhenyaYoratt/NedoHelper">GitHub репозиторий</a>.
"""))
        self.about_label.linkActivated.connect(self.link_clicked)
        self.about_label.setWordWrap(True)
        layout.addWidget(self.about_label)

        self.about_qt_button = QPushButton(self.tr("О Qt"), self)
        self.about_qt_button.clicked.connect(QApplication.aboutQt)
        buttons_layout.addWidget(self.about_qt_button)

        self.close_button = QPushButton(self.tr("Закрыть"), self)
        self.close_button.clicked.connect(self.close)
        buttons_layout.addWidget(self.close_button)
        
        layout.addLayout(buttons_layout)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
    
    def link_clicked(self, url):        
        url = "https://github.com/ZhenyaYoratt/YoHelper/discussions/new?category=suggest-programs"
        msg = QMessageBox()
        msg.setWindowTitle(self.parent().tr("Открытие ссылки"))
        msg.setText(self.parent().tr('Открыть ссылку во встроенном браузере? Нажмите "Нет", чтобы открыть в браузере по умолчанию.'))
        msg.setInformativeText(url)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Yes)
        ret = msg.exec_()
        if ret == QMessageBox.Yes:
            self.browser_window = BrowserWindow(self.parent(), url)
            self.browser_window.show()
        elif ret == QMessageBox.No:
            open_browser(url)

    def retranslateUi(self):
        self.setWindowTitle(make_title(self.tr("О программе")))
        self.header_label.setText(self.tr("О программе"))
        self.about_label.setText(self.tr("""
Программа мультул позволит вам удалить вирусы (наверное) и восстановить Windows 10 до её идеального состояния. Эта программа разработана эксклюзивно для YouTube-канала "НЕДОХАКЕРЫ Lite".

Для получения дополнительной информации посетите <a href="https://github.com/ZhenyaYoratt/NedoHelper">GitHub репозиторий</a>.
"""))
        self.about_qt_button.setText(self.tr("О Qt"))
        self.close_button.setText(self.parent().tr("Закрыть"))