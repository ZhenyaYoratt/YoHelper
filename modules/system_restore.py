import ctypes, subprocess
from ctypes import wintypes
import win32com.client
from .logger import log, ERROR

class RestorePoint:
    def __init__(self, sequence_number, description, creation_time):
        self.sequence_number = sequence_number
        self.description = description
        self.creation_time = creation_time

def _get_system_restore_obj():
    # Получаем COM-объект SystemRestore в пространстве имён root\default
    return win32com.client.GetObject(r"winmgmts:{impersonationLevel=impersonate}!\\.\root\default:SystemRestore")

def list_restore_points():
    """
    Возвращает список существующих точек восстановления.
    """
    try:
        svc = win32com.client.Dispatch("WbemScripting.SWbemLocator") \
              .ConnectServer(".", "root\\default")
        pts = svc.InstancesOf("SystemRestore")
        points = [RestorePoint(p.SequenceNumber, p.Description, p.CreationTime) for p in pts]
        return points
    except Exception as e:
        log(f"Ошибка при получении списка точек восстановления: {e}", ERROR)
        return []

def create_restore_point(description="Custom Restore Point", restore_type=0, event_type=100):
    """
    Создаёт точку восстановления.
    :param description: текст описания точки
    :param restore_type: тип (0=APPLICATION_INSTALL,12=MODIFY_SETTINGS и т.п.)
    :param event_type: событие (100 = BEGIN_SYSTEM_CHANGE / END_SYSTEM_CHANGE)
    :return: True при успехе
    """
    try:
        sr = _get_system_restore_obj()
        # CreateRestorePoint возвращает 0 (S_OK) при успехе
        result = sr.CreateRestorePoint(description, restore_type, event_type)  # :contentReference[oaicite:0]{index=0}
        if result == 0:
            log(f"Точка восстановления создана: {description}")
            return True
        else:
            log(f"Ошибка создания точки восстановления, код {result}", ERROR)
            return False
    except Exception as e:
        log(f"Ошибка создания точки восстановления: {e}", ERROR)
        return False

def delete_restore_point(sequence_number):
    """
    Удаляет точку восстановления по её sequence number.
    """
    try:
        # Загружаем SrClient.dll и вызываем SRRemoveRestorePoint
        sr = ctypes.WinDLL("SrClient.dll")
        fn = sr.SRRemoveRestorePoint  # :contentReference[oaicite:1]{index=1}
        fn.argtypes = [wintypes.DWORD]
        fn.restype  = wintypes.DWORD
        res = fn(sequence_number)
        if res == 0:  # ERROR_SUCCESS
            log(f"Точка восстановления {sequence_number} удалена.")
            return True
        else:
            log(f"Не удалось найти/удалить точку {sequence_number}, код {res}", ERROR)
            return False
    except Exception as e:
        log(f"Ошибка при удалении точки восстановления: {e}", ERROR)
        return False

def restore_to_point(sequence_number):
    """
    Откат системы к указанной точке восстановления.
    """
    try:
        sr = _get_system_restore_obj()
        # Метод Restore у SystemRestore
        result = sr.Restore(sequence_number)  # :contentReference[oaicite:2]{index=2}
        if result == 0:
            log(f"Система восстановлена до точки {sequence_number}.")
            return True
        else:
            log(f"Ошибка восстановления до точки {sequence_number}, код {result}", ERROR)
            return False
    except Exception as e:
        log(f"Ошибка восстановления до точки {sequence_number}: {e}", ERROR)
        return False

def enable_system_protection(drive="C:\\"):
    """
    Включает защиту системы (System Restore) на указанном диске.
    """
    try:
        sr = _get_system_restore_obj()
        res = sr.Enable(drive)  # :contentReference[oaicite:3]{index=3}
        if res == 0:
            log(f"Защита системы включена на {drive}")
            return True
        else:
            log(f"Не удалось включить защиту на {drive}, код {res}", ERROR)
            return False
    except Exception as e:
        log(f"Error enabling system protection: {e}", ERROR)
        return False

def disable_system_protection(drive="C:\\"):
    """
    Выключает System Restore на указанном диске через wmic.
    """
    try:
        # Формируем команду
        cmd = [
            "wmic", "/namespace:\\\\root\\default",
            "path", "SystemRestore", "call", "Disable", f"\"{drive}\""
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0 and "ReturnValue = 0" in result.stdout:
            log(f"Защита системы отключена на {drive}")
            return True
        else:
            log(f"WMIC error disabling protection: {result.stdout.strip()}", ERROR)
            return False
    except Exception as e:
        log(f"Error disabling system protection: {e}", ERROR)
        return False

def is_system_protection_enabled(drive="C:\\"):
    """
    Проверяет, включена ли защита системы на диске.
    Делает это через попытку получить точки восстановления: 
    если WMI вернул хотя бы одну точку или не выдал ошибку доступа — считаем, что защита включена.
    """
    try:
        pts = list_restore_points()
        # если доступ к WMI есть — Protection включена (хотя точек может ещё не быть)
        return True
    except:
        return False

def toggle_system_protection(drive="C:\\"):
    """
    Переключает состояние защиты системы на диске.
    """
    if is_system_protection_enabled(drive):
        disable_system_protection(drive)
    else:
        enable_system_protection(drive)
