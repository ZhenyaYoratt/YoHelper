# anti_bsod_ui.py
import os
import datetime
import shutil
import subprocess
import threading
from pathlib import Path

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFileDialog, QMessageBox, QGroupBox, QGridLayout, QSpacerItem,
    QSizePolicy, QWidget
)
from modules.anti_bsod import *

"""
АнтиBSOD — UI модуль для управления драйвером NoMoreBugCheck.sys
Реализует:
 - проверку наличия службы NoMoreBugCheck и её статуса
 - кнопки: Добавить и запустить, Удалить службу
 - включение/выключение test signing (bcdedit /set testsigning on/off)
 - копирование файла драйвера из директории PyInstaller (sys._MEIPASS) или из текущей папки
 - логирование операций в текстовом поле
 - предупреждение о нестабильности системы
"""

# helper to post callables to the main thread via QApplication.postEvent
from PyQt5.QtCore import QEvent

class RunnableEvent(QEvent):
    def __init__(self, fn):
        super().__init__(QEvent.User)
        self.fn = fn

class AntiBSODWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("АнтиBSOD — NoMoreBugCheck")
        self.setMinimumSize(700, 480)

        # список активных воркеров (QThread объектов)
        self._workers = []

        if not is_windows():
            QMessageBox.warning(self, "Только Windows", "Этот модуль работает только в Windows.")

        self.driver_path = None
        self._build_ui()
        packaged = find_packaged_driver()
        if packaged:
            self.driver_path = packaged
            self.driver_path_edit.setText(packaged)
            self.log(f"Найден драйвер в упаковке: {packaged}")
        else:
            self.driver_path = None
            self.driver_path_edit.setText("(файл не найден в пакете)")
            self.log("Драйвер не найден в пакете. Можно выбрать вручную.")

        # initial refresh
        self.refresh_status()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main = QVBoxLayout()
        central.setLayout(main)

        # Header + big warning
        # header = QLabel("<b>АнтиBSOD — NoMoreBugCheck (UI)</b>")
        # header.setAlignment(Qt.AlignLeft)
        # main.addWidget(header)

        warn_box = QGroupBox("Внимание — нестабильность системы")
        wlayout = QVBoxLayout()
        warn_box.setLayout(wlayout)
        warn_label = QLabel(
            "<b>Дисклеймер:</b><br>"
            "Использование драйвера ядра для запрета BugCheck (BSOD) может привести к непредсказуемому поведению системы, "
            "ошибкам, утечкам ресурсов или невозможности корректно перезагрузиться. "
            "Не используйте на продуктивных системах без полной проверки в виртуальной машине. "
            "Включение test-signing изменяет параметры загрузки и требует перезагрузки."
        )
        warn_label.setWordWrap(True)
        warn_label.setStyleSheet("color: darkred;")
        wlayout.addWidget(warn_label)
        main.addWidget(warn_box)

        # Status area
        status_box = QGroupBox("Статус")
        status_layout = QGridLayout()
        status_box.setLayout(status_layout)

        status_layout.addWidget(QLabel("Служба (NoMoreBugCheck):"), 0, 0)
        self.service_status_label = QLabel("---")
        self.service_status_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(self.service_status_label, 0, 1)

        status_layout.addWidget(QLabel("Test Signing (testsigning):"), 1, 0)
        self.testsign_label = QLabel("---")
        self.testsign_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(self.testsign_label, 1, 1)

        # Buttons for service actions
        btn_layout = QHBoxLayout()
        self.btn_add_and_start = QPushButton(f"Добавить и запустить {SERVICE_NAME}")
        self.btn_add_and_start.clicked.connect(self.on_add_and_start)
        btn_layout.addWidget(self.btn_add_and_start)

        self.btn_delete_service = QPushButton("Удалить службу из системы")
        self.btn_delete_service.clicked.connect(self.on_delete_service)
        btn_layout.addWidget(self.btn_delete_service)

        status_layout.addItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum), 2, 0)
        status_layout.addLayout(btn_layout, 2, 1)

        main.addWidget(status_box)

        # Test signing controls
        ts_box = QGroupBox("Test Signing (режим тестовой подписи)")
        ts_layout = QHBoxLayout()
        ts_box.setLayout(ts_layout)
        self.btn_enable_testsign = QPushButton("Включить test-signing (bcdedit /set testsigning on)")
        self.btn_enable_testsign.clicked.connect(self.on_enable_testsign)
        ts_layout.addWidget(self.btn_enable_testsign)
        self.btn_disable_testsign = QPushButton("Отключить test-signing (bcdedit /set testsigning off)")
        self.btn_disable_testsign.clicked.connect(self.on_disable_testsign)
        ts_layout.addWidget(self.btn_disable_testsign)
        main.addWidget(ts_box)

        # Driver file selection and info
        df_box = QGroupBox("Драйвер")
        df_layout = QHBoxLayout()
        df_box.setLayout(df_layout)
        self.driver_path_edit = QLabel("(файл не найден в пакете)")
        df_layout.addWidget(self.driver_path_edit)
        self.btn_browse_driver = QPushButton("Выбрать другой файл драйвера...")
        self.btn_browse_driver.clicked.connect(self.on_browse_driver)
        df_layout.addWidget(self.btn_browse_driver)
        main.addWidget(df_box)

        # Log area
        log_box = QGroupBox("Лог операций")
        log_layout = QVBoxLayout()
        log_box.setLayout(log_layout)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        main.addWidget(log_box, stretch=1)

        # Footer controls
        foot = QHBoxLayout()
        self.btn_refresh = QPushButton("Обновить статус")
        self.btn_refresh.clicked.connect(self.refresh_status)
        foot.addWidget(self.btn_refresh)

        self.btn_open_drivers_dir = QPushButton("Открыть папку драйверов")
        self.btn_open_drivers_dir.clicked.connect(self.on_open_drivers_dir)
        foot.addWidget(self.btn_open_drivers_dir)

        foot.addStretch()
        main.addLayout(foot)

        # on non-windows disable buttons
        if not is_windows():
            for w in (self.btn_add_and_start, self.btn_delete_service,
                      self.btn_enable_testsign, self.btn_disable_testsign,
                      self.btn_browse_driver, self.btn_refresh, self.btn_open_drivers_dir):
                w.setEnabled(False)

    # ---------- UI helpers ----------
    def log(self, text):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.append(f"[{ts}] {text}")

    def set_service_status_label(self, status_text, color="black"):
        self.service_status_label.setText(status_text)
        self.service_status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def set_testsign_label(self, text, color="black"):
        self.testsign_label.setText(text)
        self.testsign_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    # ---------- system operations ----------
    def refresh_status(self):
        """Обновить статус службы и тестовой подписи."""
        if not is_windows():
            self.set_service_status_label("Не-Windows", "gray")
            self.set_testsign_label("Не применимо", "gray")
            return

        t = threading.Thread(target=self._refresh_status_worker, daemon=True)
        t.start()

    def _refresh_status_worker(self):
        # service
        rc, out, err = run_cmd(["sc", "query", SERVICE_NAME])
        if rc != 0:
            # report absent
            if "The specified service does not exist" in err or "The specified service does not exist" in out or "ERROR 1060" in err:
                self.post_to_main(lambda: self.set_service_status_label("Отсутствует", "red"))
                self.log("Служба не установлена в системе.")
                self.post_to_main(lambda: self.btn_add_and_start.setEnabled(True))
                self.post_to_main(lambda: self.btn_delete_service.setEnabled(False))
            else:
                self.post_to_main(lambda: self.set_service_status_label("Ошибка проверки", "red"))
                self.log(f"Ошибка при запросе статуса службы: rc={rc} out={out} err={err}")
                self.post_to_main(lambda: self.btn_add_and_start.setEnabled(True))
                self.post_to_main(lambda: self.btn_delete_service.setEnabled(True))
        else:
            # parse STATE: RUNNING or STOPPED
            if "RUNNING" in out:
                self.post_to_main(lambda: self.set_service_status_label("Запущена", "green"))
                self.log("Служба установлена и запущена.")
                self.post_to_main(lambda: self.btn_add_and_start.setEnabled(False))
                self.post_to_main(lambda: self.btn_delete_service.setEnabled(True))
            elif "STOPPED" in out:
                self.post_to_main(lambda: self.set_service_status_label("Установлена (остановлена)", "orange"))
                self.log("Служба установлена, но остановлена.")
                self.post_to_main(lambda: self.btn_add_and_start.setEnabled(True))
                self.post_to_main(lambda: self.btn_delete_service.setEnabled(True))
            else:
                self.post_to_main(lambda: self.set_service_status_label("Неизвестно", "black"))
                self.log(f"Статус сервиса: {out}")
                self.post_to_main(lambda: self.btn_add_and_start.setEnabled(True))
                self.post_to_main(lambda: self.btn_delete_service.setEnabled(True))

        # test signing (bcdedit)
        rc2, out2, err2 = run_cmd(["bcdedit", "/enum"])
        if rc2 == 0:
            lower = (out2 or "").lower()
            if "testsigning" in lower:
                for line in (out2.splitlines()):
                    if "testsigning" in line.lower():
                        val = line.split()[-1].strip()
                        if val.lower().startswith("yes"):
                            self.post_to_main(lambda: self.set_testsign_label("Включено", "darkgreen"))
                            self.log("Test-signing: Включено.")
                        else:
                            self.post_to_main(lambda: self.set_testsign_label("Отключено", "gray"))
                            self.log("Test-signing: Отключено.")
                        break
                else:
                    self.post_to_main(lambda: self.set_testsign_label("Не обнаружено", "gray"))
            else:
                self.post_to_main(lambda: self.set_testsign_label("Не обнаружено", "gray"))
        else:
            self.post_to_main(lambda: self.set_testsign_label("Ошибка", "red"))
            self.log(f"Ошибка при проверке bcdedit: rc={rc2} err={err2}")

    def post_to_main(self, fn):
        QApplication.instance().postEvent(self, RunnableEvent(fn))

    # ---------- Button callbacks ----------
    def on_browse_driver(self):
        p, _ = QFileDialog.getOpenFileName(self, "Выберите файл драйвера (*.sys)", "", "SYS files (*.sys);;All files (*.*)")
        if p:
            self.driver_path = p
            self.driver_path_edit.setText(p)
            self.log(f"Выбран драйвер: {p}")

    def on_open_drivers_dir(self):
        if not os.path.isdir(SYSTEM_DRIVERS_DIR):
            QMessageBox.warning(self, "Ошибка", f"Папка драйверов не найдена: {SYSTEM_DRIVERS_DIR}")
            return
        try:
            subprocess.Popen(['explorer', SYSTEM_DRIVERS_DIR])
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть папку: {e}")
        
    def _start_worker(self, worker: WorkerThread, result_handler=None):
        """
        Centralized worker start:
         - сохраняет ссылку в self._workers
         - подключает finished -> _on_worker_finished
         - если передан result_handler, подключает result_signal к нему
         - запускает воркер
        """
        # держим ссылку, чтобы QThread не был уничтожен раньше времени
        self._workers.append(worker)
        worker.setParent(self)  # привязать объект к окну для безопасности

        def _finished_cleanup():
            try:
                # удаляем из списка, безопасно
                if worker in self._workers:
                    self._workers.remove(worker)
            except Exception:
                pass
            try:
                # отложенное удаление QObject (аккуратно в GUI-потоке)
                worker.deleteLater()
            except Exception:
                pass

        worker.finished_signal.connect(_finished_cleanup)
        if result_handler:
            worker.result_signal.connect(result_handler)
        # также подключаем общий обработчик ошибок/лога
        worker.result_signal.connect(self._on_worker_generic_result)
        worker.start()

    def _on_worker_generic_result(self, res):
        # generic logging for workers, optional
        rc, out, err = res
        if rc != 0:
            self.log(f"[worker] завершился с ошибкой: rc={rc} err={err or out}")
        else:
            self.log(f"[worker] успешно: {out}")

    def on_add_and_start(self):
        if not is_windows():
            return
        
        testsigning_on = False
        # test signing (bcdedit)
        rc2, out2, err2 = run_cmd(["bcdedit", "/enum"])
        if rc2 == 0:
            lower = (out2 or "").lower()
            if "testsigning" in lower:
                for line in (out2.splitlines()):
                    if "testsigning" in line.lower():
                        val = line.split()[-1].strip()
                        if val.lower().startswith("yes"):
                            testsigning_on = True
                        break

        ans = QMessageBox.question(self, "Подтвердите", "Добавить драйвер в систему и запустить службу NoMoreBugCheck?" +
                                                ("\n" + "Стисема должна быть перезагружена, чтобы драйвер заработал." if not testsigning_on else ""),
                                   QMessageBox.Yes | QMessageBox.No)
        if ans != QMessageBox.Yes:
            return
        w = WorkerThread(self._install_and_start_worker)
        # используем централизованный запуск
        self._start_worker(w, result_handler=self._on_worker_result)

    def _install_and_start_worker(self):
        self.log("Начинаю установку драйвера...")
        dp = getattr(self, "driver_path", None) or find_packaged_driver()
        if not dp or not os.path.isfile(dp):
            msg = "Файл драйвера не найден. Выберите файл NoMoreBugCheck.sys в пакете или вручную."
            self.log(msg)
            return (-1, "", msg)
        try:
            target = TARGET_DRIVER_PATH
            self.log(f"Копирование драйвера в {target} ...")
            shutil.copy2(dp, target)
        except Exception as e:
            err = f"Не удалось скопировать драйвер: {e}"
            self.log(err)
            return (-1, "", err)

        testsigning_on = False
        # test signing (bcdedit)
        rc2, out2, err2 = run_cmd(["bcdedit", "/enum"])
        if rc2 == 0:
            lower = (out2 or "").lower()
            if "testsigning" in lower:
                for line in (out2.splitlines()):
                    if "testsigning" in line.lower():
                        val = line.split()[-1].strip()
                        if val.lower().startswith("yes"):
                            testsigning_on = True
                        break

        if not testsigning_on:            
            w = WorkerThread(self._bcdedit_worker, "on")
            self._start_worker(w, result_handler=self._on_worker_result_bcdedit)

            # Ensure any existing service removed first (try stop/delete quietly)
            run_cmd(["sc", "stop", SERVICE_NAME])
            run_cmd(["sc", "delete", SERVICE_NAME])
            
            create_cmd_str = f"sc create {SERVICE_NAME} type= kernel binPath= \"{target}\" start= auto"
            rc, out, err = run_cmd(create_cmd_str, shell=True)
            if rc != 0:
                self.log(f"sc create вернул ошибку: rc={rc} out={out} err={err}")
                return (rc, out, err)

            self.log("Драйвер установлен. Требуется перегрузка.")
            self.refresh_status()
            subprocess.Popen(["shutdown", "/r", "/t", "5", "/c", "После перезагрузки системы, драйвер будет автоматически запущен."], shell=True)

            return (0, "OK", "")
        else:
            # Ensure any existing service removed first (try stop/delete quietly)
            run_cmd(["sc", "stop", SERVICE_NAME])
            run_cmd(["sc", "delete", SERVICE_NAME])

            create_cmd_str = f"sc create {SERVICE_NAME} type= kernel binPath= \"{target}\" start= auto"
            rc, out, err = run_cmd(create_cmd_str, shell=True)
            if rc != 0:
                self.log(f"sc create вернул ошибку: rc={rc} out={out} err={err}")
                return (rc, out, err)

            rc2, out2, err2 = run_cmd(["sc", "start", SERVICE_NAME])
            if rc2 != 0:
                self.log(f"Не удалось запустить службу: rc={rc2} out={out2} err={err2}")
                return (rc2, out2, err2)

            self.log("Драйвер установлен и служба запущена.")
            self.refresh_status()
            return (0, "OK", "")

    def _on_worker_result(self, res):
        rc, out, err = res
        if rc == 0:
            QMessageBox.information(self, "Готово", "Операция успешно завершена.")
        else:
            QMessageBox.warning(self, "Ошибка", f"Операция вернула ошибку:\n{err or out}")

    def on_delete_service(self):
        if not is_windows():
            return
        ans = QMessageBox.question(self, "Подтвердите", "Остановить и удалить службу NoMoreBugCheck и удалить файл драйвера?",
                                   QMessageBox.Yes | QMessageBox.No)
        if ans != QMessageBox.Yes:
            return
        w = WorkerThread(self._delete_service_worker)
        self._start_worker(w, result_handler=self._on_worker_result)

    def _delete_service_worker(self):
        self.log("Удаление службы...")
        run_cmd(["sc", "stop", SERVICE_NAME])
        rc, out, err = run_cmd(["sc", "delete", SERVICE_NAME])
        if rc != 0:
            msg = f"sc delete вернул ошибку (возможно служба не установлена): rc={rc} out={out} err={err}"
            self.log(msg)
        try:
            if os.path.isfile(TARGET_DRIVER_PATH):
                os.remove(TARGET_DRIVER_PATH)
                self.log(f"Удалён файл драйвера: {TARGET_DRIVER_PATH}")
            else:
                self.log("Файл драйвера в System32 не найден.")
        except Exception as e:
            msg = f"Не удалось удалить файл драйвера: {e}"
            self.log(msg)
            return (-1, "", msg)
        self.refresh_status()
        return (0, "OK", "")

    def on_enable_testsign(self):
        if not is_windows():
            return
        ans = QMessageBox.question(self, "Включить test-signing?",
                                   "Включить режим test-signing. Это изменит параметры загрузки и потребует перезагрузки. Продолжить?",
                                   QMessageBox.Yes | QMessageBox.No)
        if ans != QMessageBox.Yes:
            return
        w = WorkerThread(self._bcdedit_worker, "on")
        self._start_worker(w, result_handler=self._on_worker_result_bcdedit)

    def on_disable_testsign(self):
        if not is_windows():
            return
        ans = QMessageBox.question(self, "Отключить test-signing?",
                                   "Отключить режим test-signing. Это изменит параметры загрузки и потребует перезагрузки. Продолжить?",
                                   QMessageBox.Yes | QMessageBox.No)
        if ans != QMessageBox.Yes:
            return
        w = WorkerThread(self._bcdedit_worker, "off")
        self._start_worker(w, result_handler=self._on_worker_result_bcdedit)

    def _bcdedit_worker(self, mode):
        cmd = ["bcdedit", "/set", "testsigning", "on" if mode == "on" else "off"]
        rc, out, err = run_cmd(cmd)
        if rc == 0:
            self.log(f"bcdedit: test-signing set to {mode}. Требуется перезагрузка для применения.")
            self.refresh_status()
            return (0, out, err)
        else:
            self.log(f"Ошибка при выполнении bcdedit: rc={rc} out={out} err={err}")
            return (rc, out, err)

    def _on_worker_result_bcdedit(self, res):
        rc, out, err = res
        if rc == 0:
            QMessageBox.information(self, "Готово", "Команда выполнена. Перезагрузите систему для применения изменений.")
        else:
            QMessageBox.warning(self, "Ошибка", f"Команда bcdedit завершилась ошибкой:\n{err or out}")

    # customEvent обработка для RunnableEvent
    def customEvent(self, event):
        if isinstance(event, RunnableEvent):
            try:
                event.fn()
            except Exception:
                pass
        else:
            super().customEvent(event)
    
    # ---------------- safe close: дождаться воркеров ----------------
    def closeEvent(self, event):
        """
        При закрытии окна корректно дождёмся завершения активных воркеров.
        Поведение:
         - даём каждому воркеру до 3 секунд на завершение (wait).
         - если после этого кто-то всё ещё жив, вызываем terminate() и ждём ещё 1 сек.
         - затем продолжаем закрытие.
        """
        if self._workers:
            self.log("Окно закрывается: ожидаю завершения фоновых задач...")
        # копия списка, т.к. обработчики могут удалять элементы
        workers_copy = list(self._workers)
        for w in workers_copy:
            try:
                # даём рабочему немного времени завершиться естественно
                if w.isRunning():
                    self.log(f"Ожидание воркера ({w})...")
                    w.wait(3000)  # 3 сек
            except Exception:
                pass

        # повторно проверяем и в крайнем случае terminate
        for w in list(self._workers):
            try:
                if w.isRunning():
                    self.log(f"Принудительное завершение воркера ({w}) ...")
                    try:
                        w.terminate()
                        w.wait(1000)
                    except Exception:
                        pass
            except Exception:
                pass

        # небольшая пауза, чтобы finished_signal сработали и объекты удалились
        QApplication.processEvents()
        super().closeEvent(event)
