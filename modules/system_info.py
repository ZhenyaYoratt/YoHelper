from .logger import log, WARN
try:
    from PyQt5.QtCore import QObject, pyqtSignal, QRunnable
    import subprocess, platform, re
    from .disk_manager import check_disk_status
    from psutil import cpu_percent, virtual_memory, disk_partitions, disk_usage

    class SystemInfoWorkerSignals(QObject):
        loaded = pyqtSignal(dict)
        finished = pyqtSignal(dict)

    class SystemInfoWorker(QRunnable):
        """
        Выполняет get_system_info() в фоне и отдаёт результат через сигнал.
        """
        def __init__(self):
            super().__init__()
            self.signals = SystemInfoWorkerSignals()

        def run(self):
            info = {}
            try:
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                # Имя устройства
                info['Имя устройства'] = platform.node()
                self.signals.loaded.emit(info)

                # Процессор
                info['Процессор'] = platform.processor()
                self.signals.loaded.emit(info)

                # Оперативная память
                mem_bytes = int(subprocess.check_output(['wmic', 'ComputerSystem', 'get', 'TotalPhysicalMemory'], startupinfo=si).split()[1])
                info['ОЗУ (Всего)'] = f"{mem_bytes / (1024 ** 3):.2f} ГБ"
                self.signals.loaded.emit(info)

                # Код устройства и Код продукта
                device_id = subprocess.check_output(['wmic', 'csproduct', 'get', 'UUID'], startupinfo=si).decode().split('\n')[1].strip()
                info['Код устройства'] = device_id
                self.signals.loaded.emit(info)

                product_id = subprocess.check_output(['wmic', 'os', 'get', 'SerialNumber'], startupinfo=si).decode().split('\n')[1].strip()
                info['Код продукта'] = product_id
                self.signals.loaded.emit(info)

                # Тип системы
                system_type = subprocess.check_output(['wmic', 'os', 'get', 'OSArchitecture'], startupinfo=si).decode('cp866').split('\n')[1].strip()
                info['Тип системы'] = system_type
                self.signals.loaded.emit(info)

                # Перо и сенсорный ввод
                pen_touch = subprocess.check_output(['powershell', '(Get-PnpDevice -Class "HIDClass" | Where-Object { $_.FriendlyName -like "*Touch Screen*" }).FriendlyName'], startupinfo=si).decode().strip()
                if pen_touch:
                    info['Перо и сенсор'] = pen_touch
                else:
                    info['Перо и сенсор'] = 'Для этого монитора недоступен'
                self.signals.loaded.emit(info)

                # Выпуск
                edition = subprocess.check_output(['wmic', 'os', 'get', 'Caption'], startupinfo=si).decode('cp866').split('\n')[1].strip()
                info['Выпуск'] = edition
                self.signals.loaded.emit(info)

                # Версия
                version = subprocess.check_output(['wmic', 'os', 'get', 'Version'], startupinfo=si).decode().split('\n')[1].strip()
                info['Версия'] = version
                self.signals.loaded.emit(info)

                # Дата установки
                install_date = subprocess.check_output(['wmic', 'os', 'get', 'InstallDate'], startupinfo=si).decode().split('\n')[1].strip()
                install_date = re.sub(r'(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})', r'\3.\2.\1', install_date)
                info['Дата установки'] = install_date
                self.signals.loaded.emit(info)

                # Сборка ОС
                build_number = subprocess.check_output(['wmic', 'os', 'get', 'BuildNumber'], startupinfo=si).decode().split('\n')[1].strip()
                info['Сборка ОС'] = build_number
                self.signals.loaded.emit(info)

                # Взаимодействие
                #experience_pack = subprocess.check_output(['powershell', '(Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion").BuildLabEx']).decode().strip()
                #info['Взаимодействие'] = f"Windows Feature Experience Pack {experience_pack}"
                #self.signals.loaded.emit(info)

            except Exception as e:
                log(f"Ошибка при получении информации о системе: {e}", WARN)
                info["Ошибка"] = "Не удалось получить информацию"
            # эмиттим сигнал
            self.signals.finished.emit(info)

    def get_load_info():
        """Возвращает загрузку CPU и памяти."""
        try:
            cpu = cpu_percent()
            memory = virtual_memory()
            return f"CPU: {cpu}%, RAM: {memory.percent}%"
        except Exception as e:
            log(f"Ошибка при получении загрузки системы: {e}", WARN)
            return "Модуль недоступен"

    def get_disk_info():
        """Возвращает информацию о дисках."""
        try:
            disk_info = disk_partitions()
            disk_data = []
            for partition in disk_info:
                try:
                    if check_disk_status(partition.mountpoint):
                        usage = disk_usage(partition.mountpoint)
                        disk_data.append(f"{partition.device}: занято {usage.percent}%")
                    else:
                        disk_data.append(f"{partition.device}: недоступен")
                except:
                    log(f'Не удалось получить информацию использования диска {partition}', WARN)
            return "\n".join(disk_data)
        except Exception as e:
            log(f"Ошибка получения информации о дисках: {e}", WARN)
            return "Модуль недоступен"

    def get_os_icon():
        try:
            from PyQt5.QtGui import QIcon
            from PyQt5.QtWinExtras import QtWin
            os_name = platform.system()
            
            if os_name == "Windows":
                import ctypes
                from ctypes import wintypes

                SHGFI_ICON = 0x000000100
                SHGFI_LARGEICON = 0x000000000
                SHGFI_USEFILEATTRIBUTES = 0x000000010

                FILE_ATTRIBUTE_NORMAL = 0x00000080
                FILE_ATTRIBUTE_DIRECTORY = 0x00000010

                class SHFILEINFO(ctypes.Structure):
                    _fields_ = [
                        ("hIcon", wintypes.HICON),
                        ("iIcon", wintypes.INT),
                        ("dwAttributes", wintypes.DWORD),
                        ("szDisplayName", wintypes.CHAR * 260),
                        ("szTypeName", wintypes.CHAR * 80),
                    ]

                shfileinfo = SHFILEINFO()
                ctypes.windll.shell32.SHGetFileInfoW(
                    "C:\\",
                    FILE_ATTRIBUTE_DIRECTORY,
                    ctypes.byref(shfileinfo),
                    ctypes.sizeof(shfileinfo),
                    SHGFI_ICON | SHGFI_LARGEICON | SHGFI_USEFILEATTRIBUTES,
                )

                hIcon = shfileinfo.hIcon
                icon = QIcon(QtWin.fromHICON(hIcon))
                ctypes.windll.user32.DestroyIcon(hIcon)
            elif os_name == "Darwin":
                icon = QIcon.fromTheme("apple")
            elif os_name == "Linux":
                icon = QIcon.fromTheme("tux")
            else:
                icon = QIcon.fromTheme("unknown")
            
            pixmap = icon.pixmap(128, 128)
            return pixmap
        except Exception as e:
            log(f"Ошибка получения иконки ОС: {e}", WARN)
            return QIcon.fromTheme("unknown").pixmap(128, 128)
    
except ImportError as e:
    log(f"Ошибка импорта модуля: {e}", WARN)

    class SystemInfoWorkerSignals(QObject):
        loaded = pyqtSignal(dict)
        finished = pyqtSignal(dict)

    class SystemInfoWorker(QRunnable):
        """
        Выполняет get_system_info() в фоне и отдаёт результат через сигнал.
        """
        def __init__(self):
            super().__init__()
            self.signals = SystemInfoWorkerSignals()

        def run(self):
            info = {}
            info["Ошибка"] = "Модуль недоступен"
            # эмиттим сигнал
            self.signals.finished.emit(info)

    # Функции-замены при отсутствии модулей
    def get_load_info():
        return "Модуль недоступен"

    def get_disk_info():
        return "Модуль недоступен"
        
    def get_os_icon():
        from PyQt5.QtGui import QIcon
        return QIcon.fromTheme("unknown").pixmap(128, 128)