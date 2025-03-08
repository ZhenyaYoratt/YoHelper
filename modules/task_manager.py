
import ctypes, os
from ctypes import wintypes
from .logger import *
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QMessageBox, QPushButton, QCheckBox
try:
    from psutil import STATUS_RUNNING, STATUS_SLEEPING, STATUS_DISK_SLEEP, STATUS_STOPPED, STATUS_TRACING_STOP, STATUS_ZOMBIE, STATUS_DEAD, STATUS_WAKING, STATUS_IDLE, STATUS_LOCKED, STATUS_WAITING, STATUS_LOCKED, STATUS_PARKED, Process as pProcess, NoSuchProcess, AccessDenied, process_iter, REALTIME_PRIORITY_CLASS, HIGH_PRIORITY_CLASS
except ImportError:
    log("Модуль psutil недоступен", ERROR)
    
    # Process.status()
    STATUS_RUNNING = "running"
    STATUS_SLEEPING = "sleeping"
    STATUS_DISK_SLEEP = "disk-sleep"
    STATUS_STOPPED = "stopped"
    STATUS_TRACING_STOP = "tracing-stop"
    STATUS_ZOMBIE = "zombie"
    STATUS_DEAD = "dead"
    STATUS_WAKE_KILL = "wake-kill"
    STATUS_WAKING = "waking"
    STATUS_IDLE = "idle"  # Linux, macOS, FreeBSD
    STATUS_LOCKED = "locked"  # FreeBSD
    STATUS_WAITING = "waiting"  # FreeBSD
    STATUS_SUSPENDED = "suspended"  # NetBSD
    STATUS_PARKED = "parked"  # Linux
class Process():
    STATUS = {
        STATUS_RUNNING: "Выполняется",
        STATUS_SLEEPING: "Спит",
        STATUS_DISK_SLEEP: "Спит (диск)",
        STATUS_STOPPED: "Остановлен",
        STATUS_TRACING_STOP: "Остановлен (трассировка)",
        STATUS_ZOMBIE: "Зомби",
        STATUS_DEAD: "Мертв",
        STATUS_WAKING: "Пробуждается",
        STATUS_IDLE: "Простаивает",
        STATUS_LOCKED: "Заблокирован",
        STATUS_WAITING: "Ожидает",
        STATUS_LOCKED: "Блокирован",
        STATUS_PARKED: "Припаркован",
    }
    PROCESS_TYPE = {
        'system': 'Системный',
        'critical': 'Критический',
        'normal': 'Обычный',
    }

    def __init__(self, pid, name, status, cpu_percent, memory_percent, create_time, description, window_title):
        self.process_type = get_process_type(pid)
        self.pid = pid
        self.name = name
        self.status = status
        self.cpu_percent = cpu_percent
        self.memory_percent = memory_percent
        self.create_time = create_time
        self.description = description
        self.window_title = window_title

    def get_process_icon(self) -> None | QPixmap:
        try:
            if self.pid == 0:
                return None
            # Получение пути к исполняемому файлу процесса
            process = pProcess(self.pid)
            exe_path = process.exe()

            # Извлечение иконки из исполняемого файла
            hicon = ctypes.windll.shell32.ExtractIconW(0, exe_path, 0)
            if hicon:
                hdc = ctypes.windll.user32.GetDC(0)
                hdc_mem = ctypes.windll.gdi32.CreateCompatibleDC(hdc)
                hbm = ctypes.windll.gdi32.CreateCompatibleBitmap(hdc, 32, 32)
                hbm_old = ctypes.windll.gdi32.SelectObject(hdc_mem, hbm)
                ctypes.windll.user32.DrawIconEx(hdc_mem, 0, 0, hicon, 32, 32, 0, 0, 3)
                ctypes.windll.gdi32.SelectObject(hdc_mem, hbm_old)
                ctypes.windll.gdi32.DeleteDC(hdc_mem)
                ctypes.windll.user32.ReleaseDC(0, hdc)
                ctypes.windll.user32.DestroyIcon(hicon)

                # Преобразование Bitmap в QPixmap
                class BITMAP(ctypes.Structure):
                    _fields_ = [
                        ("bmType", ctypes.c_long),
                        ("bmWidth", ctypes.c_long),
                        ("bmHeight", ctypes.c_long),
                        ("bmWidthBytes", ctypes.c_long),
                        ("bmPlanes", ctypes.c_ushort),
                        ("bmBitsPixel", ctypes.c_ushort),
                        ("bmBits", ctypes.c_void_p)
                    ]

                bmpinfo = BITMAP()
                ctypes.windll.gdi32.GetObjectW(hbm, ctypes.sizeof(BITMAP), ctypes.byref(bmpinfo))
                bmpstr = ctypes.create_string_buffer(bmpinfo.bmWidthBytes * bmpinfo.bmHeight)
                ctypes.windll.gdi32.GetBitmapBits(hbm, len(bmpstr), bmpstr)
                image = QImage(bmpstr, bmpinfo.bmWidth, bmpinfo.bmHeight, QImage.Format_ARGB32)
                pixmap = QPixmap.fromImage(image)
                ctypes.windll.gdi32.DeleteObject(hbm)
                return pixmap
            return None
        except Exception as e:
            log(f"Ошибка при получении иконки процесса с PID {self.pid}: {e}", ERROR)
            return None

    def kill(self):
        """Завершает процесс по PID."""
        try:
            process = pProcess(self.pid)
            # Подтверждение завершения самого себя
            if self.pid == os.getpid():
                msgBox = QMessageBox()
                msgBox.setIcon(QMessageBox.Question)
                msgBox.setWindowTitle("Диспетчер задач")
                msgBox.setText(f"<b>Вы хотите завершить YoHelper?</b>")
                msgBox.setInformativeText("Завершение этого процесса приведет к завершению работы программы. Вы действительно хотите продолжить?")
                msgBox.addButton(QPushButton('Завершить'), QMessageBox.ButtonRole.YesRole)
                msgBox.addButton(QPushButton('Отмена'), QMessageBox.ButtonRole.NoRole)
                msgBox.exec_()
                if msgBox.clickedButton().text() == 'Завершить':
                    process.kill()
                    msg = f"Процесс {self.name} ({self.pid}) завершен."
                    log(msg)
                    return msg, True
                return "Отмена завершения процесса.", False
            # Подтверждение завершения критического процесса
            if self.process_type in [ProcessType.CRITICAL, ProcessType.SYSTEM]:
                msgBox = QMessageBox()
                msgBox.setIcon(QMessageBox.Question)
                msgBox.setWindowTitle("Диспетчер задач")
                msgBox.setText(f"<b>Вы хотите завершить системный процесс \"{self.name}\"?</b>")
                msgBox.setInformativeText("Завершение этого процесса приведет к нестабильности работы Windows или завершению работы системы, и вы можете потерять несохраненные данные. Вы действительно хотите продолжить?")
                checkbox = QCheckBox('Не сохранять данные и завершить работу.')
                msgBox.setCheckBox(checkbox)
                terminate_button = QPushButton('Завершить работу')
                terminate_button.setEnabled(False)
                checkbox.stateChanged.connect(lambda state: terminate_button.setEnabled(state))
                msgBox.addButton(terminate_button, QMessageBox.ButtonRole.YesRole)
                msgBox.addButton(QPushButton('Отмена'), QMessageBox.ButtonRole.NoRole)
                msgBox.exec_()
                if msgBox.clickedButton().text() == 'Завершить работу':
                    process.kill()
                    msg = f"Процесс {self.name} ({self.pid}) завершен."
                    log(msg)
                    return msg, True
            else:
                process.kill()
                msg = f"Процесс {self.name} ({self.pid}) завершен."
                log(msg)
                return msg, True
            return msg, False
        except Exception as e:
            msg = f"Ошибка завершения процесса {self.name}: {e}"
            log(msg, ERROR)
            return msg, False

    def suspend(self):
        """
        Приостанавливает процесс с указанным PID.

        :param pid: ID процесса, который нужно приостановить.
        :return: Строка с результатом выполнения операции.
        """
        try:
            process = pProcess(self.pid)
            process.suspend()
            msg = f"Процесс с PID {self.pid} успешно приостановлен."
            log(msg)
            return msg
        except NoSuchProcess:
            msg = f"Ошибка: Процесс с PID {self.pid} не существует."
            log(msg, ERROR)
            return msg
        except AccessDenied:
            msg = f"Ошибка: Доступ к процессу с PID {self.pid} запрещён."
            log(msg, ERROR)
            return msg
        except Exception as e:
            msg = f"Ошибка при приостановке процесса с PID {self.pid}: {e}"
            log(msg, ERROR)
            return msg

    def resume(self):
        """
        Возобновляет приостановленный процесс с указанным PID.

        :param pid: ID процесса, который нужно возобновить.
        :return: Строка с результатом выполнения операции.
        """
        try:
            process = pProcess(self.pid)
            process.resume()
            msg = f"Процесс с PID {self.pid} успешно возобновлён."
            log(msg)
            return msg
        except NoSuchProcess:
            msg = f"Ошибка: Процесс с PID {self.pid} не существует."
            log(msg, ERROR)
            return msg
        except AccessDenied:
            msg = f"Ошибка: Доступ к процессу с PID {self.pid} запрещён."
            log(msg, ERROR)
            return msg
        except Exception as e:
            msg = f"Ошибка при возобновлении процесса с PID {self.pid}: {e}"
            log(msg, ERROR)
            return msg


    def __repr__(self):
        return f"Process({self.pid}, {self.name})"
    
    def __str__(self):
        return f"{self.name} ({self.pid})"
    
def get_process_list():
    """Возвращает список активных процессов."""
    processes = []
    for proc in process_iter(attrs=["pid", "name", "status", "cpu_percent", "memory_percent", "create_time", "username"]):
        description = proc.info.get('description', '')
        window_title = proc.info.get('window_title', '')
        processes.append(Process(
            proc.info['pid'],
            proc.info['name'],
            proc.info['status'],
            proc.info['cpu_percent'],
            proc.info['memory_percent'],
            proc.info['create_time'],
            description,
            window_title
        ))
    return processes

class ProcessType:
    SYSTEM = 'system'
    CRITICAL = 'critical'
    NORMAL = 'normal'

def is_process_critical(pid: int):
    try:
        process = pProcess(pid)
        return process.nice() in [REALTIME_PRIORITY_CLASS, HIGH_PRIORITY_CLASS]
    except NoSuchProcess:
        log(f"Процесс с PID {pid} не найден.", WARNING)
        return False
    except Exception as e:
        log(f"Ошибка при определении критичности процесса с PID {pid}: {e}", ERROR)
        return False

def get_process_type(pid):
    try:
        if pid == 0:
            return ProcessType.SYSTEM
        process = pProcess(pid)
        if process.username() in ['SYSTEM', 'NT AUTHORITY\\SYSTEM', 'NT AUTHORITY\\СИСТЕМА', 'root', 'СИСТЕМА', 'NT AUTHORITY\\LOCAL SERVICE']:
            return ProcessType.SYSTEM 
        elif is_process_critical(process.pid):
            return ProcessType.CRITICAL
        else:
            return ProcessType.NORMAL
    except NoSuchProcess:
        log(f"Процесс с PID {pid} не найден.", WARNING)
        return None
    except Exception as e:
        log(f"Ошибка при определении типа процесса с PID {pid}: {e}", ERROR)
        return None
