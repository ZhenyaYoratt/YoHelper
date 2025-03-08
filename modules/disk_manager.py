from .logger import *
from PyQt5.QtGui import QPixmap, QImage
import subprocess

try:
    import win32com.client
    from ctypes import wintypes, windll, Structure, byref, sizeof

    import psutil
    import os
    from win32com.shell import shell, shellcon # type: ignore
    from PyQt5.QtGui import QPixmap, QIcon
    from PyQt5.QtWinExtras import QtWin

    def get_disk_type(drive_letter):
        """
        Получает тип устройства для указанного диска.
        
        :param drive_letter: Буква диска, например, "C:" или "D:".
        :return: Строка с типом устройства (например, "Физический диск", "CD-ROM", "USB", и т.д.)
        """
        try:
            # Проверяем доступность диска
            if not os.path.exists(drive_letter):
                return f"{drive_letter} не доступен."

            # Получаем информацию о разделе диска
            partitions = psutil.disk_partitions()
            for partition in partitions:
                if partition.device.startswith(drive_letter):
                    # Определяем тип устройства (например, физический диск или CD-ROM)
                    if 'cdrom' in partition.opts:
                        return "CD-ROM"
                    elif 'usb' in partition.opts:
                        return "USB"
                    else:
                        return "Физический диск"
            return "Неизвестный тип устройства"
        except Exception as e:
            msg = f"Ошибка определения типа диска: {e}"
            log(msg, ERROR)
            return msg

    def check_disk_status(drive_letter):
        """
        Проверяет, готов ли диск к использованию (например, доступен ли он для чтения).
        
        :param drive_letter: Буква диска (например, "C:", "D:").
        :return: Статус доступности диска (True - доступен, False - не доступен).
        """
        try:
            # Проверяем доступность устройства
            return os.path.exists(drive_letter) and os.access(drive_letter, os.R_OK)
        except Exception as e:
            log(f"Ошибка при проверке статуса диска {drive_letter}: {e}", ERROR)
            return False

    class DriveInfo:
        def __init__(self, status = False, letter = None, type = None):
            self.status = False
            self.letter = None
            self.type = None

    def get_drive_info(drive_letter):
        """
        Получает информацию о диске: тип и доступность.
        
        :param drive_letter: Буква диска, например, "C:".
        :return: Строка с информацией о типе и статусе устройства.
        """
        if check_disk_status(drive_letter):
            disk_type = get_disk_type(drive_letter)
            return DriveInfo(status=True, letter=drive_letter, type=disk_type)
        else:
            return DriveInfo(status=False, letter=drive_letter)

    def unlock_bitlocker(drive_letter, credential):
        """Попытка разблокировать диск с BitLocker."""
        try:
            letter = drive_letter.replace('/', '').replace('\\', '').replace(':', '') + ':'
            log(f"Попытка разблокировки диска: {letter}", DEBUG)

            # Используем manage-bde для разблокировки диска
            result = subprocess.run(['manage-bde', '-unlock', letter, '-password', credential], capture_output=True, text=True, encoding='cp866')
            if result.returncode == 0:
                return f"Диск {drive_letter} успешно разблокирован.", True
            else:
                # Если не удалось разблокировать с паролем, пробуем с ключом восстановления
                result = subprocess.run(['manage-bde', '-unlock', letter, '-recoverypassword', credential], capture_output=True, text=True)
                if result.returncode == 0:
                    return f"Диск {drive_letter} успешно разблокирован.", True
                else:
                    return f"Не удалось разблокировать диск {drive_letter}. Ошибка: {result.stderr}", False
        except Exception as e:
            msg = f"Ошибка разблокировки диска: {e}"
            log(msg, ERROR)
            return msg, False

    def is_bitlocker_protected(drive_letter):
        """
        Проверяет, защищен ли диск BitLocker.
        
        :param drive_letter: Буква диска, например, 'C:'.
        :return: True, если диск защищен BitLocker, иначе False.
        """
        try:
            letter = drive_letter.replace('/', '').replace('\\', '')
            log(f"Проверка диска: {letter}", DEBUG)

            # Используем manage-bde для проверки состояния защиты
            result = subprocess.run(['manage-bde', '-status', letter], capture_output=True, text=True, encoding='cp866')
            if result.returncode == 0:
                # Проверяем наличие строки "Protection Status: Protection On" в выводе
                for line in result.stdout.splitlines():
                    if "Protection Status" in line or "Состояние блокировки" in line:
                        status = line.split(":")[1].strip()
                        return status.lower() in ["on", "включено", "защита включена", "блокировка"]
            return False
        except Exception as e:
            log(f"Ошибка проверки защиты BitLocker: {e}", ERROR)
            return None

    def get_volume_name(drive_letter: str):
        try:
            # Подключение к WMI
            wmi = win32com.client.GetObject("winmgmts:\\\\.\\root\\cimv2")
            
            letter = drive_letter.replace('/', '').replace('\\', '')

            # Запрос имени тома для указанного диска
            query = f'SELECT * FROM Win32_LogicalDisk WHERE DeviceID="{letter}"'
            volumes = wmi.ExecQuery(query)

            for volume in volumes:
                return volume.VolumeName
            return None
        except Exception as e:
            log(f"Ошибка получения имени тома диска: {e}", ERROR)
            return None

    def get_disk_icon(drive_letter, size=16):
        try:
            SHGFI_ICON = 0x100
            SHGFI_LARGEICON = 0x0
            SHGFI_USEFILEATTRIBUTES = 0x10
            SHIL_LARGE = 0x0        # 32x32
            SHIL_SMALL = 0x1        # 16x16
            SHIL_EXTRALARGE = 0x2   # 48x48
            SHIL_SYSSMALL = 0x3     # 16x16
            SHIL_JUMBO = 0x4        # 256x256

            SIZE_ICON = SHIL_JUMBO if size >= 256 else SHIL_EXTRALARGE if size >= 48 else SHIL_LARGE if size >= 32 else SHIL_SYSSMALL if size >= 16 else SHIL_JUMBO

            FILE_ATTRIBUTE_NORMAL = 0x80
            FILE_ATTRIBUTE_DIRECTORY = 0x10

            class SHFILEINFO(Structure):
                _fields_ = [
                    ("hIcon", wintypes.HICON),
                    ("iIcon", wintypes.INT),
                    ("dwAttributes", wintypes.DWORD),
                    ("szDisplayName", wintypes.CHAR * 520),
                    ("szTypeName", wintypes.CHAR * 80),
                ]

            shfileinfo = SHFILEINFO()
            windll.shell32.SHGetFileInfoW(
                drive_letter,
                FILE_ATTRIBUTE_DIRECTORY,
                byref(shfileinfo),
                sizeof(shfileinfo),
                SHGFI_ICON | SHGFI_LARGEICON | SHGFI_USEFILEATTRIBUTES | SIZE_ICON,
            )

            hIcon = shfileinfo.hIcon
            icon = QIcon(QtWin.fromHICON(hIcon))
            windll.user32.DestroyIcon(hIcon)
            return icon.pixmap(512, 512)
        except Exception as e:
            log(f"Ошибка получения иконки диска: {e}", ERROR)
            return QPixmap()
except ImportError as e:
    log("Не удалось импортировать модуль disk_manager.py", ERROR)
    log(e, DEBUG)
    def get_disk_type():
        return "Unknown"
    def check_bitlocker_status():
        return False
    def get_drive_info():
        return DriveInfo()
    def get_volume_name():
        return "Unknown"
    def get_disk_icon():
        return QPixmap()