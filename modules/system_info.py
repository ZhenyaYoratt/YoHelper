from psutil import cpu_percent, virtual_memory, disk_partitions, disk_usage
from .logger import *
from .disk_manager import check_disk_status
import platform
import subprocess
import re
import platform
from PyQt5.QtGui import QIcon
from PyQt5.QtWinExtras import QtWin

def get_system_info():
    """Возвращает информацию о системе."""
    info = {}

    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW


    # Имя устройства
    info['Имя устройства'] = platform.node()

    # Процессор
    info['Процессор'] = platform.processor()

    # Оперативная память
    mem_bytes = int(subprocess.check_output(['wmic', 'ComputerSystem', 'get', 'TotalPhysicalMemory'], startupinfo=si).split()[1])
    info['ОЗУ (Всего)'] = f"{mem_bytes / (1024 ** 3):.2f} ГБ"

    # Код устройства и Код продукта
    device_id = subprocess.check_output(['wmic', 'csproduct', 'get', 'UUID'], startupinfo=si).decode().split('\n')[1].strip()
    product_id = subprocess.check_output(['wmic', 'os', 'get', 'SerialNumber'], startupinfo=si).decode().split('\n')[1].strip()
    info['Код устройства'] = device_id
    info['Код продукта'] = product_id

    # Тип системы
    system_type = subprocess.check_output(['wmic', 'os', 'get', 'OSArchitecture'], startupinfo=si).decode('cp866').split('\n')[1].strip()
    info['Тип системы'] = system_type

    # Перо и сенсорный ввод
    pen_touch = subprocess.check_output(['powershell', '(Get-PnpDevice -Class "HIDClass" | Where-Object { $_.FriendlyName -like "*Touch Screen*" }).FriendlyName'], startupinfo=si).decode().strip()
    if pen_touch:
        info['Перо и сенсор'] = pen_touch
    else:
        info['Перо и сенсор'] = 'Для этого монитора недоступен'

    # Выпуск
    edition = subprocess.check_output(['wmic', 'os', 'get', 'Caption'], startupinfo=si).decode('cp866').split('\n')[1].strip()
    info['Выпуск'] = edition

    # Версия
    version = subprocess.check_output(['wmic', 'os', 'get', 'Version'], startupinfo=si).decode().split('\n')[1].strip()
    info['Версия'] = version

    # Дата установки
    install_date = subprocess.check_output(['wmic', 'os', 'get', 'InstallDate'], startupinfo=si).decode().split('\n')[1].strip()
    install_date = re.sub(r'(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})', r'\3.\2.\1', install_date)
    info['Дата установки'] = install_date

    # Сборка ОС
    build_number = subprocess.check_output(['wmic', 'os', 'get', 'BuildNumber'], startupinfo=si).decode().split('\n')[1].strip()
    info['Сборка ОС'] = build_number

    # Взаимодействие
    #experience_pack = subprocess.check_output(['powershell', '(Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion").BuildLabEx']).decode().strip()
    #info['Взаимодействие'] = f"Windows Feature Experience Pack {experience_pack}"

    return info

def get_load_info():
    cpu = cpu_percent()
    memory = virtual_memory()
    return f"CPU: {cpu}%, RAM: {memory.percent}%"

def get_disk_info():
    """Возвращает информацию о дисках."""
    disk_info = disk_partitions()
    disk_data = []
    for partition in disk_info:
        try:
            if check_disk_status(partition.mountpoint):
                usage = disk_usage(partition.mountpoint)
                disk_data.append(f"{partition.mountpoint}: занято {usage.percent}%")
            else:
                disk_data.append(f"{partition.mountpoint}: недоступен")
        except:
            log(f'Не удалось получить информацию использования диска {partition}', WARN)
    return "\n".join(disk_data)

def get_os_icon():
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