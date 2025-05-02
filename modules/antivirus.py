import hashlib
import os, sys, requests
from .logger import *
from PyQt5.QtCore import pyqtSignal, QUrl, QEventLoop, QObject, QThread
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager, QNetworkReply

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.path.dirname(__file__)

LIST_DATABASES_URL = "https://raw.githubusercontent.com/ZhenyaYoratt/NedoHelper/refs/heads/main/antivirus_databases_list"
DATABASES_FORLDER = os.path.join(application_path, '..', 'databases')

class UpdateWorker(QObject):
    progress = pyqtSignal(int)  # Для прогресса
    set_max = pyqtSignal(int)
    completed = pyqtSignal()  # Для завершения

    main_url = LIST_DATABASES_URL
    databases_folder = DATABASES_FORLDER

    def run(self):
        """
        Обновляет базу данных, загружая файлы по ссылкам, полученным с главной ссылки.

        :param main_url: Главная ссылка для получения списка ссылок с файлами (в формате JSON).
        :param databases_folder: Папка, куда будут сохраняться файлы (по умолчанию 'databases').
        """
        if not os.path.exists(self.databases_folder):
            os.makedirs(self.databases_folder)

        req = QNetworkRequest(QUrl(self.main_url))
        
        self.nam = QNetworkAccessManager()
        self.nam.finished.connect(self.handleResponse)
        self.nam.get(req)

    def handleResponse(self, reply: QNetworkReply):
        self.nam.finished.disconnect(self.handleResponse)
        loop = QEventLoop()

        if reply.error() == QNetworkReply.NoError:
            bytes_string = reply.readAll()
            file_links = bytes_string.data().decode('utf-8').split('\n') # Получаем JSON, который содержит ссылки на файлы

            # Скачиваем каждый файл по ссылке
            self.set_max.emit(len(file_links))
            i = 1
            for file_url in file_links:
                self.progress.emit(i)
                file_name = file_url.split("/")[-1]  # Извлекаем имя файла из URL
                file_path = os.path.join(self.databases_folder, file_name)

                if not os.path.exists(file_path):
                    # Загружаем файл
                    req = QNetworkRequest(QUrl(file_url))
                    reply = self.nam.get(req)
                    reply.finished.connect(loop.quit)
                    loop.exec_()
                    if reply.error() == QNetworkReply.NoError:
                        with open(file_path, 'wb') as f:
                            f.write(reply.readAll().data())
                    else:
                        log(f"Ошибка при загрузке файла {file_url}:", ERROR)
                i += 1
            self.completed.emit()
        else:
            log(f"Ошибка при получении списка файлов: {reply.errorString()}", ERROR)

def load_database(databases_folder=DATABASES_FORLDER):
    """
    Загружает базу данных из файлов в папке `databases`, исключая строки, начинающиеся с #.

    :param databases_folder: Папка с файлами базы данных (по умолчанию 'databases').
    :return: Список строк из файлов, исключая строки, начинающиеся с '#'.
    """
    database_content = []

    # Проверяем, существует ли папка с файлами
    if not os.path.exists(databases_folder):
        log(f"Папка {databases_folder} не найдена.")
        return []

    # Проходим по всем файлам в папке
    for filename in os.listdir(databases_folder):
        file_path = os.path.join(databases_folder, filename)

        # Пропускаем директории
        if os.path.isdir(file_path):
            continue

        # Открываем и читаем файл
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                # Пропускаем строки, начинающиеся с '#'
                if not line.startswith('#'):
                    database_content.append(line.strip())

    return database_content


class ScanThread(QObject):
    progress = pyqtSignal(int)  # Для прогресса
    set_max = pyqtSignal(int)
    suspicious_file = pyqtSignal(str)
    completed = pyqtSignal(list)  # Для завершения
    progress_text = pyqtSignal(str)

    def __init__(self, directory):
        super().__init__()
        self.directory = directory

    def run(self):
        try:
            """Сканирует папку на наличие файлов с хешами из базы данных."""
            malicious_hashes = load_database()
            suspicious_files = []
            self.set_max.emit(len([name for name in os.listdir(self.directory) if os.path.isfile(os.path.join(self.directory, name))]))
            i = 1
            for root, _, files in os.walk(self.directory):
                for file_name in files:
                    file_path = os.path.abspath(os.path.join(root, file_name))
                    self.progress_text.emit(file_name)
                    file_hash = calculate_md5(file_path)
                    if file_hash in malicious_hashes:
                        suspicious_files.append(file_path)
                        self.suspicious_file.emit(file_path)
                    self.progress.emit(i)
                    i += 1

            self.completed.emit(suspicious_files)
        except requests.RequestException as e:
            log(f"Ошибка при получении списка файлов: {e}", ERROR)
        finally:
            QThread.currentThread().quit()

def calculate_md5(file_path):
    """Вычисляет MD5 хеш файла."""
    try:
        with open(file_path, "rb") as file:
            file_hash = hashlib.md5()
            while chunk := file.read(4096):
                file_hash.update(chunk)
            return file_hash.hexdigest()
    except Exception as e:
        return None

def delete_file(file_path):
    """Удаляет файл."""
    try:
        os.remove(file_path)
        return f"Удалён файл: {file_path}"
    except Exception as e:
        return f"Ошибка удаления {file_path}: {e}"
