from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QLabel, QPushButton, QWidget, QMessageBox, QStyleFactory, QDialog, QComboBox, QHBoxLayout, qApp
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt, QTranslator
from modules.titles import make_title
import qdarktheme
import json
from pyqt_windows_os_light_dark_theme_window.main import Window

LOCALIZATIONS_DIR = "localizations"

LANGUAGES = {
    "en": "English",
    "ru": "Русский"
}

SETTINGS = {
    "theme": "dark",
    "theme_style": "modern",
    "language": "en"
}

class Settings:
    def __init__(self, filename, parent=None):
        self.parent = parent
        self.filename = filename
        self.filenotfound = False
        self.data = self.load_settings()

    def load_settings(self):
        try:
            with open(self.filename, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            self.filenotfound = True
            with open(self.filename, "w") as file:
                json.dump(SETTINGS, file, indent=4)
            return SETTINGS
        except json.JSONDecodeError:
            QMessageBox.critical(self.parent, "Error", "Couldn't load the settings.")
            self.filenotfound = True
            with open(self.filename, "w") as file:
                json.dump(SETTINGS, file, indent=4)
            return SETTINGS

    def save_settings(self):
        with open(self.filename, "w") as file:
            json.dump(self.data, file, indent=4)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save_settings()

class SettingsWindow(QMainWindow, Window):
    SETTINGS_FILE = "settings.json"

    def __init__(self, parent = None):
        super().__init__()
        self.setParent(parent)
        self.setWindowTitle(make_title(self.parent().tr("Настройки")))
        self.setFixedSize(400, 215)
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        self.statusbar = self.statusBar()
        self.statusbar.showMessage(self.parent().tr("Готов к работе"))
        
        self.settings = Settings(self.SETTINGS_FILE, self)

        self._layout = QVBoxLayout()
        self.header_label = QLabel(self.tr("Настройки программы"))
        self.header_label.setObjectName("title")

        theme_layout = QHBoxLayout()
        self.theme_label = QLabel(self.tr("Тема"))
        self.theme_combobox = QComboBox()
        self.theme_combobox.addItems([self.tr("Системная тема"), self.tr("Темная тема"), self.tr("Светлая тема")])
        self.theme_combobox.currentIndexChanged.connect(self.change_theme)
        theme_layout.addWidget(self.theme_label)
        theme_layout.addWidget(self.theme_combobox)

        theme_style_layout = QHBoxLayout()
        self.theme_style_label = QLabel(self.tr("Стиль темы"))
        self.theme_style_combobox = QComboBox()
        self.theme_style_combobox.addItems([self.tr("Современная тема"), self.tr("Fusion тема"), self.tr("Плоская тема (Windows 10)"), self.tr("Windows 95 тема")])
        self.theme_style_combobox.currentIndexChanged.connect(self.change_theme_style)
        theme_style_layout.addWidget(self.theme_style_label)
        theme_style_layout.addWidget(self.theme_style_combobox)

        language_layout = QHBoxLayout()
        self.language_label = QLabel(self.tr("Язык"))
        self.language_combobox = QComboBox()
        self.language_combobox.addItems([LANGUAGES[lang] for lang in LANGUAGES])
        self.language_combobox.currentIndexChanged.connect(self.change_language)
        language_layout.addWidget(self.language_label)
        language_layout.addWidget(self.language_combobox)

        self.save_button = QPushButton(self.tr("Сохранить"))
        self.save_button.clicked.connect(self.save_settings)

        self._layout.addWidget(self.header_label)
        self._layout.addLayout(theme_layout)
        self._layout.addLayout(theme_style_layout)
        self._layout.addLayout(language_layout)
        self._layout.addWidget(self.save_button)

        central_widget = QWidget()
        central_widget.setLayout(self._layout)
        self.setCentralWidget(central_widget)

        self.center()

        self.load_settings()

        # Создать приветственное окно с настройками
        if self.settings.filenotfound:
            dialog = QDialog(self)
            dialog.setWindowTitle(self.tr("Первоначальная настройка программы"))
            layout = QVBoxLayout()
            title = QLabel(self.tr("Добро пожаловать!"))
            title.setObjectName("title")
            layout.addWidget(title)
            layout.addWidget(QLabel(self.tr("Для начала работы необходимо настроить программу.")))
            layout.addWidget(QLabel(self.tr("Настройки будут сохранены в файл settings.json.")))

            theme_layout = QHBoxLayout()
            theme_label = QLabel(self.tr("Тема"))
            theme_combobox = QComboBox()
            theme_combobox.addItems([self.tr("Системная тема"), self.tr("Темная тема"), self.tr("Светлая тема")])
            theme_combobox.currentIndexChanged.connect(self.change_theme)
            theme_layout.addWidget(theme_label)
            theme_layout.addWidget(theme_combobox)

            def _change_theme_style(index):
                styles = ["modern", "fusion", "flat", "95"]
                theme_style = styles[index]
                theme_combobox.setDisabled(False)
                if theme_style == "flat" or theme_style == "95":
                    theme_combobox.setDisabled(True)
                    theme_combobox.setCurrentIndex(2)
                self.change_theme_style(index)

            theme_style_layout = QHBoxLayout()
            theme_style_label = QLabel(self.tr("Стиль темы"))
            theme_style_combobox = QComboBox()
            theme_style_combobox.setModel(self.theme_style_combobox.model())
            theme_style_combobox.currentIndexChanged.connect(_change_theme_style)
            theme_style_layout.addWidget(theme_style_label)
            theme_style_layout.addWidget(theme_style_combobox)

            language_layout = QHBoxLayout()
            language_label = QLabel(self.tr("Язык"))
            language_combobox = QComboBox()
            language_combobox.addItems([LANGUAGES[lang] for lang in LANGUAGES])
            language_combobox.currentIndexChanged.connect(self.change_language)
            language_layout.addWidget(language_label)
            language_layout.addWidget(language_combobox)

            layout.addLayout(theme_layout)
            layout.addLayout(theme_style_layout)
            layout.addLayout(language_layout)
            save_close_button = QPushButton(self.tr("Сохранить и закрыть"))
            save_close_button.clicked.connect(lambda: (self.save_settings(), self.load_settings(apply=False), dialog.close()))
            layout.addWidget(save_close_button)
            dialog.setLayout(layout)
            frame_geometry = dialog.frameGeometry()
            center_point = self.screen().availableGeometry().center()
            frame_geometry.moveCenter(center_point)
            dialog.move(frame_geometry.topLeft())
            try:
                import pyi_splash # type: ignore
                pyi_splash.close()
            except:
                pass
            dialog.exec_()
            

    def center(self):
        """Центрирует окно по центру экрана."""
        frame_geometry = self.frameGeometry()
        center_point = self.screen().availableGeometry().center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def change_theme(self, index):
        themes = ["auto", "dark", "light"]
        self.settings.set("theme", themes[index])
        self.apply_theme()

    def change_theme_style(self, index):
        styles = ["modern", "fusion", "flat", "95"]
        self.settings.set("theme_style", styles[index])
        self.apply_theme()

    def change_language(self, index):
        languages = ["en", "ru"]
        selected_language = languages[index]
        self.settings.set("language", selected_language)
        self.apply_language(selected_language)

    def apply_language(self, language):
        translator = QTranslator()
        translator.load(f'{language}.qm', 'localizations')
        qApp.installTranslator(translator)
        self.parent().retranslateUi()
        self.retranslateUi()

    def apply_theme(self):
        """Применяет тему."""
        theme: str = self.settings.get("theme", "auto")
        theme_style: str = self.settings.get("theme_style", "auto")
        self.settings.set("theme", theme)
        qdarktheme.setup_theme('light')
        qApp.setStyleSheet('')
        qApp.setPalette(QPalette())
        self.theme_combobox.setDisabled(False)
        self.parent().update_button_icons()
        if theme_style == "modern":
            qdarktheme.setup_theme(theme)
            qdarktheme.setup_theme(theme)
        elif theme_style == "fusion":
            qApp.setStyle(QStyleFactory.create("Fusion"))
            if theme == "dark":
                palette = QPalette()
                palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
                palette.setColor(QPalette.ColorRole.WindowText, Qt.white)
                palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
                palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
                palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.black)
                palette.setColor(QPalette.ColorRole.ToolTipText, Qt.white)
                palette.setColor(QPalette.ColorRole.Text, Qt.white)
                palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
                palette.setColor(QPalette.ColorRole.ButtonText, Qt.white)
                palette.setColor(QPalette.ColorRole.BrightText, Qt.red)
                palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
                palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
                palette.setColor(QPalette.ColorRole.HighlightedText, Qt.black)
                qApp.setPalette(palette)
        elif theme_style == "flat":
            self.settings.set("theme", "light")
            self.theme_combobox.setCurrentIndex(2)
            self.theme_combobox.setDisabled(True)
            qApp.setStyle(QStyleFactory.create("windowsvista"))
        elif theme_style == "95":
            self.settings.set("theme", "light")
            self.theme_combobox.setCurrentIndex(2)
            self.theme_combobox.setDisabled(True)
            qApp.setStyle(QStyleFactory.create("Windows"))

    def load_settings(self, apply = True):
        """Загружает настройки из файла."""
        self.settings.load_settings()
        theme = self.settings.get("theme", "auto")
        theme_style = self.settings.get("theme_style", "modern")

        theme_index = ["auto", "dark", "light"].index(theme)
        theme_style_index = ["modern", "fusion", "flat", "95"].index(theme_style)

        self.theme_combobox.setCurrentIndex(theme_index)
        self.theme_style_combobox.setCurrentIndex(theme_style_index)

        language = self.settings.get("language", "en")
        language_index = ["en", "ru"].index(language)
        self.language_combobox.setCurrentIndex(language_index)
        if apply:
            self.apply_language(language)
            self.apply_theme()

    def save_settings(self):
        """Сохраняет настройки в файл."""
        self.settings.save_settings()
        self.statusbar.showMessage(self.tr("Настройки успешно сохранены."))

    def retranslateUi(self):
        self.setWindowTitle(make_title(self.tr("Настройки")))
        self.header_label.setText(self.tr("Настройки программы"))
        self.theme_combobox.setItemText(0, self.tr("Системная тема"))
        self.theme_combobox.setItemText(1, self.tr("Темная тема"))
        self.theme_combobox.setItemText(2, self.tr("Светлая тема"))
        self.theme_style_combobox.setItemText(0, self.tr("Современная тема"))
        self.theme_style_combobox.setItemText(1, self.tr("Fusion тема"))
        self.theme_style_combobox.setItemText(2, self.tr("Плоская тема (Windows 10)"))
        self.theme_style_combobox.setItemText(3, self.tr("Windows 95 тема"))
        self.language_label.setText(self.tr("Язык"))
        self.save_button.setText(self.tr("Сохранить"))

