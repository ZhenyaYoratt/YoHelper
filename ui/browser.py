from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QTabWidget, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QMenu, QWidget,
    QMessageBox, QDialog, QListWidget, QApplication, QTextEdit, QListWidgetItem
)
from PyQt5.QtCore import Qt, QUrl, QSize, QDir
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile, QWebEngineDownloadItem
import webbrowser
import validators
import json
import os
from modules.titles import make_title
import qtawesome
from pyqt_windows_os_light_dark_theme_window.main import Window

def spin_icon(self):
    animation = qtawesome.Spin(self, autostart=True, step=5, interval=10)
    spin_icon = qtawesome.icon('mdi.loading', animation=animation)
    return spin_icon

# Ensure storage directory
STORAGE_DIR = os.path.join(os.path.dirname(__file__), 'browser')
os.makedirs(STORAGE_DIR, exist_ok=True)
HISTORY_FILE = os.path.join(STORAGE_DIR, 'history.json')
BOOKMARKS_FILE = os.path.join(STORAGE_DIR, 'bookmarks.json')
DOWNLOADS_FILE = os.path.join(STORAGE_DIR, 'downloads.json')
DOWNLOAD_FOLDER = os.path.join(STORAGE_DIR, 'downloads')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

NEW_TAB_HTML = '''
<!DOCTYPE html>
<html lang="ru" data-bs-theme="dark">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Новая вкладка</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.5/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="p-5 text-center"><div class="container">
        <h1>Браузер YoHelper</h1>
        <form action="https://www.google.com/search" method="get">
            <div class="input-group my-5">
                <input type="text" class="form-control" name="q" placeholder="Поиск в Google">
                <input class="btn btn-secondary" type="submit" value="Поиск">
            </div>
        </form>
        <div class="btn-group" role="group">
            <a type="button" class="btn btn-outline-primary" href="//nedotube.vercel.app/">Сайт NedoTube</a>
            <a type="button" class="btn btn-outline-primary" href="//nedohackers.site/">Сам Себе Сайт Недохакеров</a>
        </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.8/dist/umd/popper.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.5/dist/js/bootstrap.min.js"></script>
    </body>
</html>'''

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def spin_icon(self):
    animation = qtawesome.Spin(self, autostart=True, step=5, interval=10)
    return qtawesome.icon('mdi.loading', animation=animation)


class BrowserWindow(QMainWindow, Window):
    zoom_dialog = None

    def __init__(self, parent=None, url="yobrowser://new-tab", profile: QWebEngineProfile = None):
        super().__init__()
        self.setParent(parent)
        self.setWindowTitle(make_title(self.tr("Встроенный браузер")))
        self.resize(1300, 840)
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        # Load persistent data
        self.history = load_json(HISTORY_FILE)
        self.bookmarks = load_json(BOOKMARKS_FILE)
        self.downloads = load_json(DOWNLOADS_FILE)

        # Profile setup
        if profile is None:
            self.profile = QWebEngineProfile.defaultProfile()
            # persistent storage
            self.profile.setPersistentCookiesPolicy(QWebEngineProfile.AllowPersistentCookies)
            self.profile.setCachePath(os.path.join(STORAGE_DIR, 'cache'))
            self.profile.setPersistentStoragePath(os.path.join(STORAGE_DIR, 'storage'))
        else:
            # incognito: no persistent data, but downloads still saved
            self.profile = QWebEngineProfile(parent=self)
            self.profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
            # cache and storage left default (in memory)

        self.profile.downloadRequested.connect(self.on_download_requested)

        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.tabs.tabBarDoubleClicked.connect(self.tab_open_doubleclick)
        self.tabs.currentChanged.connect(self.current_tab_changed)

        # Панель управления
        control_layout = QHBoxLayout()

        self.back_button = QPushButton()
        self.back_button.setIcon(qtawesome.icon("mdi.arrow-left"))
        self.back_button.setIconSize(QSize(28, 28))
        self.back_button.clicked.connect(lambda: self.current_tab().back())

        self.forward_button = QPushButton()
        self.forward_button.setIcon(qtawesome.icon("mdi.arrow-right"))
        self.forward_button.setIconSize(QSize(28, 28))
        self.forward_button.clicked.connect(lambda: self.current_tab().forward())

        self.reload_button = QPushButton()
        self.reload_button.setIcon(qtawesome.icon("mdi.reload"))
        self.reload_button.setIconSize(QSize(28, 28))
        self.reload_button.clicked.connect(lambda: self.current_tab().reload())

        self.home_button = QPushButton()
        self.home_button.setIcon(qtawesome.icon("mdi.home"))
        self.home_button.setIconSize(QSize(28, 28))
        self.home_button.clicked.connect(self.navigate_home)

        self.urlbar = QLineEdit()
        self.urlbar.setPlaceholderText(self.tr("Введите URL..."))
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        self.httpsicon = QLabel()

        self.go_button = QPushButton()
        self.go_button.setIcon(qtawesome.icon("mdi.arrow-right"))
        self.go_button.setIconSize(QSize(28, 28))
        self.go_button.clicked.connect(self.navigate_to_url)

        self.zoom_button = QPushButton('100%')
        self.zoom_button.setIcon(qtawesome.icon("mdi.magnify"))
        self.zoom_button.setIconSize(QSize(28, 28))
        self.zoom_button.clicked.connect(self.toggle_zoom_dialog)
        self.zoom_button.setVisible(False)
        self.zoom_dialog = None

        self.add_new_tab_button = QPushButton()
        self.add_new_tab_button.setIcon(qtawesome.icon("mdi.plus"))
        self.add_new_tab_button.setIconSize(QSize(28, 28))
        self.add_new_tab_button.clicked.connect(lambda: self.add_new_tab())

        self.menu_button = QPushButton()
        self.menu_button.setIcon(qtawesome.icon("mdi.dots-vertical"))
        self.menu_button.setIconSize(QSize(28, 28))

        menu = QMenu()
        menu.addAction(qtawesome.icon("mdi.tab"), self.tr("Новая вкладка"), lambda: self.add_new_tab())
        menu.addAction(qtawesome.icon("mdi.shape-square-rounded-plus"), self.tr("Новое окно"), lambda: BrowserWindow(parent=self.parent()).show())
        menu.addAction(qtawesome.icon("mdi.incognito"), self.tr("Новое окно в режиме инкогнито"), self.open_incognito_mode)
        menu.addSeparator()
        menu.addAction(qtawesome.icon("mdi.history"), self.tr("История"), self.show_history)
        menu.addAction(qtawesome.icon("mdi.bookmark"), self.tr("Закладки"), self.show_bookmarks)
        menu.addAction(qtawesome.icon("mdi.download"), self.tr("Загрузки"), self.show_downloads)
        menu.addSeparator()
        menu.addAction(qtawesome.icon("mdi.bookmark-outline"), self.tr("Закладки"), self.show_bookmarks)
        menu.addAction(qtawesome.icon("mdi.magnify"), self.tr("Найти на странице"), self.show_find)
        menu.addAction(qtawesome.icon("mdi.magnify-plus"), self.tr("Масштаб"), self.show_zoom)
        menu.addAction(qtawesome.icon("mdi.fullscreen"), self.tr("Полный экран"), self.toggle_fullscreen)
        menu.addSeparator()
        menu.addAction(qtawesome.icon("mdi.file-code-outline"), self.tr("Исходный код"), self.view_source)
        menu.addSeparator()
        menu.addAction(qtawesome.icon("mdi.open-in-new"), self.tr("Открыть в стороннем браузере"), self.open_in_external_browser)
        menu.addAction(qtawesome.icon("mdi.cog"), self.parent().tr("Настройки"), self.settings_html)
        menu.addAction(qtawesome.icon("mdi.exit-to-app"), self.parent().tr("Выход"), self.close)
        self.menu_button.setMenu(menu)
        
        for w in [self.back_button, self.forward_button, self.reload_button,
                  self.httpsicon, self.urlbar, self.zoom_button, self.go_button, self.add_new_tab_button, self.menu_button]:
            control_layout.addWidget(w)

        layout.addLayout(control_layout)
        layout.addWidget(self.tabs)
        cw = QWidget()
        cw.setLayout(layout)
        self.setCentralWidget(cw)

        self.add_new_tab(self.get_qurl(url))

        self.move(QApplication.desktop().screen().rect().center() - self.rect().center())

    def add_new_tab(self, qurl=QUrl('yobrowser://new-tab'), label="Новая вкладка"):
        browser = QWebEngineView()

        page = QWebEnginePage(self.profile, browser)
        browser.setPage(page)

        # custom schemes
        if qurl.scheme() == 'yobrowser':
            if qurl.host() == 'new-tab':
                browser.setHtml(self.new_tab_html())
            elif qurl.host() == 'settings':
                browser.setHtml(self.settings_html())
        else:
            browser.setUrl(qurl)
        
        index = self.tabs.addTab(browser, spin_icon(self), label)
        self.tabs.setCurrentIndex(index)

        browser.urlChanged.connect(lambda q, b=browser: self.update_urlbar(q, b))
        browser.titleChanged.connect(
             lambda t, b=browser: self.tabs.setTabText(
                 self.tabs.indexOf(b), b.page().title()
             )
         )
        browser.loadStarted.connect(
            lambda b=browser: self.tabs.setTabIcon(
                self.tabs.indexOf(b), spin_icon(self)
            )
        )
        browser.loadFinished.connect(
            lambda ok, b=browser: (
                self.tabs.setTabText(self.tabs.indexOf(b), b.page().title()),
                self.tabs.setTabIcon(self.tabs.indexOf(b), b.page().icon()),
                self.record_history(b.page().title(), b.url().toString())
            )
        )

    def tab_open_doubleclick(self, i):
        if i == -1:
            self.add_new_tab()

    def current_tab_changed(self, i):
        tab = self.current_tab()
        if hasattr(tab, 'url'):
            qurl = tab.url()
            self.update_urlbar(qurl, self.current_tab())
        else:
            self.update_urlbar(QUrl('nedotube://huh'), self.current_tab())
        
    def close_current_tab(self, i):
        widget = self.tabs.widget(i)
        self.tabs.removeTab(i)
        widget.deleteLater()
        if self.tabs.count() < 1:
            self.close()
    
    def navigate_home(self):
        self.current_tab().setUrl(QUrl("yobrowser://new-tab"))

    def navigate_to_url(self):
        url = self.urlbar.text().strip()
        self.current_tab().setUrl(self.get_qurl(url))

    def get_qurl(self, text):
        if text.lower().startswith('yobrowser://'):
            return QUrl(text)
        
        if text == '' or text == 'yobrowser://new-tab':
            return QUrl('yobrowser://new-tab')
        
        if not validators.url(text):
            text = 'https://www.google.com/search?q=' + text
        
        if not text.startswith('http'):
            text = 'http://' + text
        
        q = QUrl(text)
        q.setScheme(q.scheme() or 'http')
        return q
    
    def update_urlbar(self, q: QUrl, browser=None):
        if browser != self.current_tab():
            return
        if q.scheme() == 'data':
            if q.toString().strip() == NEW_TAB_HTML.strip():
                self.urlbar.setText("yobrowser://new-tab")
            else:
                self.urlbar.setText("yobrowser://")
            return
        url = q.toString()
        self.urlbar.setText(url)
        if not self.urlbar.hasFocus():
            self.urlbar.setCursorPosition(0)
        if url.startswith("https://"):
            self.httpsicon.setPixmap(qtawesome.icon("fa.lock").pixmap(16, 16))
        else:
            self.httpsicon.setPixmap(qtawesome.icon("fa.unlock").pixmap(16, 16))

    def current_tab(self) -> QWebEngineView | QWidget:
        return self.tabs.currentWidget()
    
    def open_in_external_browser(self):
        url = self.urlbar.text().strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url
        webbrowser.open(url)
    
    def open_incognito_mode(self):
        BrowserWindow(parent = self, profile = QWebEngineProfile(parent = self)).show()

    def record_history(self, title, url):
        if self.profile.persistentCookiesPolicy() != QWebEngineProfile.NoPersistentCookies:
            self.history.append({'title': title, 'url': url})
            save_json(HISTORY_FILE, self.history)

    def add_bookmark(self):
        title = self.current_tab().page().title()
        url = self.current_tab().url().toString()
        self.bookmarks.append({'title': title, 'url': url})
        save_json(BOOKMARKS_FILE, self.bookmarks)
        QMessageBox.information(self, self.tr("Закладки"), self.tr("Добавлено в закладки"))

    def show_history(self):
        self.open_list_tab('history')

    def show_bookmarks(self):
        self.open_list_tab('bookmarks')

    def show_downloads(self):
        self.open_list_tab('downloads')

    def open_list_tab(self, kind):
        text = ''
        if kind == 'history':
            data = self.history
            title = self.tr("История")
        elif kind == 'bookmarks':
            data = self.bookmarks
            title = self.tr("Закладки")
        else:
            data = self.downloads
            title = self.tr("Загрузки")

        page = QWidget()

        layout = QVBoxLayout()
        label = QLabel(title)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignTop)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setStyleSheet("font-family: sans-serif; font-size: 14px;")
        layout.addWidget(label)

        page_list = QListWidget()
        page_list.setStyleSheet("font-family: sans-serif; font-size: 14px;")
        layout.addWidget(page_list)
        for item in data[::-1]:
            widget_item = QListWidgetItem()
            label = QLabel()
            label.setText(item.get('title', '') + ' - ' + item.get('url', item.get('path', '')))
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            page_list.addItem(widget_item)
            page_list.setItemWidget(widget_item, label)

        page.setLayout(layout)

        index = self.tabs.addTab(page, title)
        self.tabs.setCurrentIndex(index)

    def on_download_requested(self, download: QWebEngineDownloadItem):
        fn = os.path.basename(download.path())
        target = os.path.join(DOWNLOAD_FOLDER, fn)
        download.setPath(target); download.accept()
        self.downloads.append({'path': target, 'state': 'in_progress'})
        save_json(DOWNLOADS_FILE, self.downloads)
        download.finished.connect(lambda: self.on_download_finished(download, target))

    def on_download_finished(self, download, path):
        for d in self.downloads:
            if d['path'] == path:
                d['state'] = 'completed'
        save_json(DOWNLOADS_FILE, self.downloads)
        QMessageBox.information(self, self.tr("Загрузки"), self.tr(f"Загрузка завершена: {path}"))

    def show_find(self):
        # Плавающий небольшой QDialog (Tool) для поиска
        browser = self.current_tab()
        if not isinstance(browser, QWebEngineView):
            return
        dialog = QDialog(self, flags=Qt.Tool | Qt.FramelessWindowHint)
        dialog.setWindowTitle(self.tr("Найти на странице"))
        # Расположение: под панелью управления (пример смещения)
        toolbar_bottom = self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft()).y()
        dialog.move(self.geometry().x() + 10, toolbar_bottom + 5)

        le = QLineEdit(dialog)
        le.setPlaceholderText(self.tr("Поиск..."))
        le.textChanged.connect(lambda txt: browser.findText(txt))
        dialog.setFixedSize(self.width() - 20, 40)

        layout = QHBoxLayout(dialog)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(le)
        dialog.show()

    def toggle_zoom_dialog(self):
        if self.zoom_dialog and self.zoom_dialog.isVisible():
            self.zoom_dialog.close()
        else:
            self.show_zoom()

    def show_zoom(self):
        browser = self.current_tab()
        if not isinstance(browser, QWebEngineView):
            return
        if self.zoom_dialog is None:
            dialog = QDialog(self, flags=Qt.Tool | Qt.FramelessWindowHint)
            dialog.setWindowTitle(self.tr("Масштаб"))
            dialog.setFixedSize(200, 40)
            label = QLabel(f"{int(browser.zoomFactor()*100)}%", dialog)
            plus = QPushButton("+", dialog)
            minus = QPushButton("–", dialog)
            reset = QPushButton(self.tr("Сбросить"), dialog)
            layout = QHBoxLayout(dialog)
            layout.setContentsMargins(5,5,5,5)
            for w in (label, plus, minus, reset):
                layout.addWidget(w)
            plus.clicked.connect(lambda: self.adjust_zoom(browser, label, 0.25))
            minus.clicked.connect(lambda: self.adjust_zoom(browser, label, -0.25))
            reset.clicked.connect(lambda: self.reset_zoom(browser, label))
            self.zoom_dialog = dialog
        # toggle visibility
        self.zoom_dialog.setVisible(not self.zoom_dialog.isVisible())
        self.update_zoom_button()

    def adjust_zoom(self, browser, label, delta):
        browser.setZoomFactor(browser.zoomFactor() + delta)
        label.setText(f"{int(browser.zoomFactor()*100)}%")
        self.update_zoom_button()

    def reset_zoom(self, browser, label):
        browser.setZoomFactor(1.0)
        label.setText("100%")
        self.update_zoom_button()

    def update_zoom_button(self):
        # Показываем кнопку, если масштаб не 100%
        tab = self.current_tab()
        if isinstance(self.current_tab(), QWebEngineView):
            return
        btn = self.zoom_button
        current = tab.zoomFactor()
        btn.setVisible(current != 1.0)
        btn.setText(f"{int(tab.zoomFactor()*100)}%")

    def moveEvent(self, event):
        super().moveEvent(event)
        # При перетаскивании переносим диалог зума
        if self.zoom_dialog:
            if self.zoom_dialog.isVisible():
                toolbar_bottom = self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft()).y()
                self.zoom_dialog.move(self.geometry().width() - 300, toolbar_bottom - 5)

    def view_source(self):
        def callback(html):
            editor = QTextEdit()
            editor.setReadOnly(True)
            editor.setText(html)
            index = self.tabs.addTab(editor,self.tr("Исходный код"))
            self.tabs.setCurrentIndex(index)
        self.current_tab().page().toHtml(callback)

    def open_devtools(self):
        tab = self.current_tab()
        if isinstance(tab, QWebEngineView):
            tab.page().setDevToolsPage(tab.page())
            tab.page().devToolsPage().createWindow()

    def toggle_fullscreen(self):
        self.setWindowState(self.windowState() ^ Qt.WindowFullScreen)

    def new_tab_html(self):
        return NEW_TAB_HTML
    
    def settings_html(self):
        return '<html><body><h2>Настройки</h2><p>Пока нет.</p></body></html>'

    def retranslateUi(self):
        self.setWindowTitle(make_title(self.tr("Встроенный браузер")))
        self.menu_button.menu().actionAt(0).setText(self.tr("Новая вкладка"))
        self.menu_button.menu().actionAt(1).setText(self.tr("Новое окно"))
        self.menu_button.menu().actionAt(2).setText(self.tr("Новое окно в режиме инкогнито"))
        self.menu_button.menu().actionAt(3).setText(self.tr("История"))
        self.menu_button.menu().actionAt(4).setText(self.tr("Закладки"))
        self.menu_button.menu().actionAt(5).setText(self.tr("Загрузки"))
        self.menu_button.menu().actionAt(6).setText(self.tr("Открыть в стороннем браузере"))
        self.menu_button.menu().actionAt(7).setText(self.parent().tr("Выход"))