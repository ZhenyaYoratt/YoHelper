from subprocess import Popen, PIPE
from PyQt5.QtCore import QObject, pyqtSignal
import threading

class ProcessLauncher(QObject):
    process_output = pyqtSignal(str, str)

    def __init__(self, parent=None, command=None):
        super().__init__(parent)
        self.command = command or []

    def launch_process(self):
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def _run(self):
        try:
            # Лучше: передаём список аргументов и shell=False
            proc = Popen(self.command, shell=False, stdout=PIPE, stderr=PIPE, text=True, encoding='cp866')
            stdout, stderr = proc.communicate()  # блокирует только фоновый поток
            self.process_output.emit(stdout, stderr)
        except Exception as e:
            self.process_output.emit("", f"Ошибка: {e}")
