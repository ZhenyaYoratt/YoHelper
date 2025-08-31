# anti_bsod_ui.py
import os
import subprocess

from PyQt5.QtCore import QThread, pyqtSignal

SERVICE_NAME = "NoMoreBugCheck"
DRIVER_FILENAME = "NoMoreBugCheck.sys"
SYSTEM_DRIVERS_DIR = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "System32", "drivers")
TARGET_DRIVER_PATH = os.path.join(SYSTEM_DRIVERS_DIR, DRIVER_FILENAME)

def is_windows():
    return os.name == "nt"

def run_cmd(cmd, shell=False, capture=True):
    """Выполнить команду и вернуть (returncode, stdout, stderr). Без исключений."""
    try:
        proc = subprocess.run(cmd, shell=shell, stdout=subprocess.PIPE if capture else None,
                              stderr=subprocess.PIPE if capture else None, text=True)
        out = proc.stdout if capture else ""
        err = proc.stderr if capture else ""
        return proc.returncode, (out or "").strip(), (err or "").strip()
    except Exception as e:
        return -1, "", str(e)

def find_packaged_driver():
    """
    Попытаться найти файл драйвера:
     - если приложение упаковано PyInstaller, искать в sys._MEIPASS
     - иначе искать в текущей директории
     - также попробовать временную папку (temp)
    Возвращает путь или None.
    """
    candidates = []
    try:
        import sys as _sys
        if hasattr(_sys, "_MEIPASS"):
            candidates.append(os.path.join(_sys._MEIPASS, DRIVER_FILENAME))
    except Exception:
        pass
    # current directory
    candidates.append(os.path.join(os.getcwd(), DRIVER_FILENAME))
    # temp directory
    try:
        candidates.append(os.path.join(os.environ.get("TEMP", ""), DRIVER_FILENAME))
    except Exception:
        pass
    for p in candidates:
        if p and os.path.isfile(p):
            return os.path.abspath(p)
    return None

class WorkerThread(QThread):
    finished_signal = pyqtSignal()
    result_signal = pyqtSignal(tuple)  # (returncode, out, err)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            res = self.fn(*self.args, **self.kwargs)
            # res expected to be tuple
            self.result_signal.emit(res)
        except Exception as e:
            self.result_signal.emit((-1, "", str(e)))
        finally:
            self.finished_signal.emit()

