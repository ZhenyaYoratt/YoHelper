from subprocess import Popen, PIPE
from .logger import *
from PyQt5.QtCore import QObject

class ProcessLauncher(QObject):
    def __init__(self, parent, command):
        super().__init__()
        self.setParent(parent)
        self.command = command

    def launch_process(self):
        """Запускает процесс с опциональными правами администратора."""
        try:
            process = Popen(self.command, shell=True, stdout=PIPE, stderr=PIPE, text=True)
            stdout, stderr = process.communicate()
            if stdout:
                log(f"Процесс `{self.command}`: {stdout}")
            if stderr:
                log(f"Процесс `{self.command}`: {stderr}", ERROR)
        except Exception as e:
            msg = f"Ошибка запуска процесса `{self.command}`: {e}"
            log(msg, ERROR)
            return msg