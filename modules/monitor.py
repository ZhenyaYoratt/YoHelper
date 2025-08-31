import os
import time
import threading
import ctypes
import psutil
import datetime

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QBrush

# -------------------------
# Хелперы
# -------------------------
def now_str():
    return datetime.datetime.now().strftime("%H:%M:%S")

def seconds_since(start_ts):
    return max(0.0, time.time() - start_ts)

def requires_elevation_exe(path):
    """Эвристика: поиск manifest token'ов в первых байтах .exe"""
    try:
        with open(path, "rb") as f:
            data = f.read(1024 * 1024)
            if b"requireAdministrator" in data or b"requestedExecutionLevel" in data:
                return True
    except Exception:
        pass
    return False

def compute_risk_percent(action, path):
    """Эвристическая оценка риска (0..100)."""
    p = (path or "").lower()
    score = 10
    WINDIR = os.environ.get("WINDIR", r"C:\Windows").lower()
    PROGRAMFILES = os.environ.get("PROGRAMFILES", r"C:\Program Files").lower()
    SYSTEM_DIRS = [WINDIR, os.path.join(WINDIR, "System32").lower(), PROGRAMFILES]

    if "run" in action.lower() or "autostart" in action.lower() or "установлено значение" in action.lower():
        score = 95
    elif action.lower().startswith("создан процесс"):
        if p.endswith(".exe"):
            if any(p.startswith(sd) for sd in SYSTEM_DIRS):
                score = 90
            else:
                score = 70
        else:
            score = 60
    elif "создан файл" in action.lower() or "создана папка" in action.lower():
        if p.endswith(".exe"):
            score = 95
        elif any(p.startswith(sd) for sd in SYSTEM_DIRS):
            score = 90
        elif "startup" in p or "run" in p:
            score = 80
        elif "desktop" in p:
            score = 50
        elif "temp" in p or "tmp" in p:
            score = 30
        else:
            score = 25
    elif action.lower().startswith("переименование"):
        score = 30
    elif action.lower().startswith("удал"):
        score = 10
    else:
        score = 20
    return max(0, min(100, int(score)))

def risk_brush(percent):
    """Фон ячейки по уровню риска."""
    if percent <= 0:
        return QBrush(Qt.transparent)
    if percent <= 50:
        alpha = int((percent / 50.0) * 120)
        color = QColor(255, 255, 0, alpha)
    else:
        alpha = int((percent / 100.0) * 140)
        t = (percent - 50) / 50.0
        r = 255
        g = int(255 * (1 - t))
        b = 0
        color = QColor(r, g, b, alpha)
    return QBrush(color)

# -------------------------
# Монитор-нитка
# -------------------------
class MonitorThread(QThread):
    event_signal = pyqtSignal(dict)   # структурированное событие -> GUI
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, exe_path, args="", require_elevate=False, watch_dirs=None, poll_interval=0.25):
        super().__init__()
        self.exe_path = exe_path
        self.args = args or ""
        self.require_elevate = require_elevate
        self.watch_dirs = watch_dirs or []
        self.poll_interval = poll_interval

        self._stop = threading.Event()
        self.main_pid = None
        self.start_ts = None

        self.tracked_pids = set()
        self.known_open_files = {}  # pid -> set(paths)
        self.known_scanned_files = set()
        self.folder_owner = {}  # path_norm -> pid

        # threads for watchers
        self._fs_threads = []
        self._reg_thread = None
        self._proc_watch_thread = None

        # ctypes handles / funcs
        self._kernel32 = ctypes.windll.kernel32
        self._advapi32 = ctypes.windll.advapi32

    # --- small helpers ---
    def stop(self):
        self._stop.set()

    def _emit(self, action, path="", pid=None, extra=None):
        ev = {
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "since": round(max(0.0, time.time() - self.start_ts), 3) if self.start_ts else 0.000,
            "action": action,
            "path": path or "",
            "pid": pid,
            "extra": extra or {},
            "risk": compute_risk_percent(action, path or "")
        }
        # thread-safe signal
        self.event_signal.emit(ev)

    def _norm(self, p):
        try:
            return os.path.normcase(os.path.abspath(p))
        except Exception:
            return p

    # --- attribution methods (same order as раньше) ---
    def _attribute_by_open_files(self, path_norm):
        for pid in list(self.tracked_pids):
            try:
                p = psutil.Process(pid)
                try:
                    of = p.open_files()
                except Exception:
                    of = []
                for fh in of:
                    try:
                        if os.path.normcase(fh.path) == path_norm:
                            return pid
                    except Exception:
                        continue
            except Exception:
                continue
        return None

    def _attribute_by_folder_owner(self, path_norm):
        p = path_norm
        while True:
            if p in self.folder_owner:
                return self.folder_owner[p]
            parent = os.path.dirname(p)
            if not parent or parent == p:
                break
            p = parent
        return None

    def _attribute_by_cwd_or_exe(self, path_norm):
        for pid in list(self.tracked_pids):
            try:
                p = psutil.Process(pid)
                try:
                    cwd = p.cwd()
                except Exception:
                    cwd = None
                try:
                    exe = p.exe()
                except Exception:
                    exe = None
                if cwd and path_norm.startswith(self._norm(cwd)):
                    return pid
                if exe:
                    exedir = self._norm(os.path.dirname(exe))
                    if path_norm.startswith(exedir):
                        return pid
            except Exception:
                continue
        return None

    def _attribute_by_time(self, path, path_ctime):
        candidate = None
        min_delta = 9999
        for pid in list(self.tracked_pids):
            try:
                p = psutil.Process(pid)
                pt = p.create_time()
                delta = abs(pt - path_ctime)
                if delta < min_delta and delta < 6.0:
                    min_delta = delta
                    candidate = pid
            except Exception:
                continue
        return candidate

    def _attribute_path(self, path, is_dir=False):
        path_norm = self._norm(path)
        pid = self._attribute_by_open_files(path_norm)
        if pid:
            return pid, "open_files"
        pid = self._attribute_by_folder_owner(path_norm)
        if pid:
            return pid, "folder_owner"
        pid = self._attribute_by_cwd_or_exe(path_norm)
        if pid:
            return pid, "cwd/exe"
        try:
            ctime = os.path.getctime(path)
            pid = self._attribute_by_time(path, ctime)
            if pid:
                return pid, "time"
        except Exception:
            pass
        return (self.main_pid, "fallback")

    # ---------------------------
    # ReadDirectoryChangesW watcher
    # ---------------------------
    def _start_fs_watchers(self):
        # spawn a thread per directory (blocking ReadDirectoryChangesW)
        for d in self.watch_dirs:
            if not d or not os.path.exists(d):
                continue
            t = threading.Thread(target=self._fs_watch_loop, args=(d,), daemon=True)
            t.start()
            self._fs_threads.append(t)

    def _fs_watch_loop(self, directory):
        # WinAPI constants
        FILE_LIST_DIRECTORY = 0x0001
        FILE_SHARE_READ = 0x00000001
        FILE_SHARE_WRITE = 0x00000002
        FILE_SHARE_DELETE = 0x00000004
        OPEN_EXISTING = 3
        FILE_FLAG_BACKUP_SEMANTICS = 0x02000000

        FILE_NOTIFY_CHANGE_FILE_NAME = 0x00000001
        FILE_NOTIFY_CHANGE_DIR_NAME  = 0x00000002
        FILE_NOTIFY_CHANGE_ATTRIBUTES = 0x00000004
        FILE_NOTIFY_CHANGE_SIZE = 0x00000008
        FILE_NOTIFY_CHANGE_LAST_WRITE = 0x00000010
        FILE_NOTIFY_CHANGE_CREATION = 0x00000040
        flags = FILE_NOTIFY_CHANGE_FILE_NAME | FILE_NOTIFY_CHANGE_DIR_NAME | FILE_NOTIFY_CHANGE_ATTRIBUTES | FILE_NOTIFY_CHANGE_SIZE | FILE_NOTIFY_CHANGE_LAST_WRITE | FILE_NOTIFY_CHANGE_CREATION

        # open directory handle
        CreateFileW = self._kernel32.CreateFileW
        CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
        CreateFileW.restype = ctypes.c_void_p

        ReadDirectoryChangesW = self._kernel32.ReadDirectoryChangesW
        ReadDirectoryChangesW.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.c_void_p, ctypes.c_void_p]
        ReadDirectoryChangesW.restype = ctypes.c_int

        hDir = CreateFileW(directory,
                           FILE_LIST_DIRECTORY,
                           FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                           None,
                           OPEN_EXISTING,
                           FILE_FLAG_BACKUP_SEMANTICS,
                           None)
        if not hDir or hDir == ctypes.c_void_p(-1).value:
            # cannot open directory (permissions) => skip
            return

        BUFFER_SIZE = 64 * 1024
        while not self._stop.is_set():
            buffer = ctypes.create_string_buffer(BUFFER_SIZE)
            bytes_returned = ctypes.c_uint32(0)
            ok = ReadDirectoryChangesW(hDir, ctypes.byref(buffer), BUFFER_SIZE, True, flags, ctypes.byref(bytes_returned), None, None)
            if not ok:
                # short sleep to avoid busy loop; could be permission or handle closed
                time.sleep(0.2)
                continue
            # parse FILE_NOTIFY_INFORMATION entries
            data = buffer.raw[:bytes_returned.value]
            offset = 0
            while offset < len(data):
                # DWORD NextEntryOffset, DWORD Action, DWORD FileNameLength, WCHAR FileName[...]
                if offset + 12 > len(data):
                    break
                next_offset = int.from_bytes(data[offset:offset+4], 'little')
                action = int.from_bytes(data[offset+4:offset+8], 'little')
                name_len = int.from_bytes(data[offset+8:offset+12], 'little')
                name_offset = offset + 12
                name_bytes = data[name_offset:name_offset+name_len]
                try:
                    filename = name_bytes.decode('utf-16le')
                except Exception:
                    filename = ""
                full_path = os.path.join(directory, filename)
                # map action
                if action == 1:
                    act = "Создан файл"
                elif action == 2:
                    act = "Удалён файл"
                elif action == 3:
                    act = "Изменён файл"
                elif action == 4:
                    act = "Переименование_старое"
                elif action == 5:
                    act = "Переименование_новое"
                else:
                    act = f"Action_{action}"
                # For rename we will see two events: old and new; handle as rename if we can pair them later.
                # Attribute the path
                try:
                    is_dir = os.path.isdir(full_path)
                except Exception:
                    is_dir = False
                pid, method = self._attribute_path(full_path, is_dir=is_dir)
                # emit
                if act.startswith("Переименование"):
                    # we emit generic "Переименование (partial)" with indicator
                    self._emit("Переименование (частичное)", path=f"{full_path}", pid=pid, extra={"action_code": action, "method": method})
                else:
                    # normalize path and emit
                    self._emit("Создана папка" if is_dir else "Создан файл", path=self._norm(full_path), pid=pid, extra={"method": method, "source":"ReadDirectoryChangesW"})
                if next_offset == 0:
                    break
                offset += next_offset
        # close handle
        try:
            ctypes.windll.kernel32.CloseHandle(hDir)
        except Exception:
            pass

    # ---------------------------
    # Registry watcher using RegNotifyChangeKeyValue
    # ---------------------------
    def _start_registry_watcher(self):
        t = threading.Thread(target=self._reg_watch_loop, daemon=True)
        t.start()
        self._reg_thread = t

    def _reg_watch_loop(self):
        # watch a few key paths: HKCU\...\Run, HKLM\...\Run and Uninstall branches under HKLM/HKCU
        watch_specs = [
            (ctypes.c_void_p(0x80000001), r"Software\Microsoft\Windows\CurrentVersion\Run"),    # HKCU
            (ctypes.c_void_p(0x80000002), r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),    # HKLM
            (ctypes.c_void_p(0x80000002), r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (ctypes.c_void_p(0x80000002), r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (ctypes.c_void_p(0x80000001), r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]
        # helper wrappers
        RegOpenKeyExW = self._advapi32.RegOpenKeyExW
        RegOpenKeyExW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p)]
        RegOpenKeyExW.restype = ctypes.c_int
        RegNotifyChangeKeyValue = self._advapi32.RegNotifyChangeKeyValue
        RegNotifyChangeKeyValue.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_int]
        RegNotifyChangeKeyValue.restype = ctypes.c_int
        RegCloseKey = self._advapi32.RegCloseKey
        RegCloseKey.argtypes = [ctypes.c_void_p]
        # flags
        REG_NOTIFY_CHANGE_NAME = 0x00000001
        REG_NOTIFY_CHANGE_ATTRIBUTES = 0x00000002
        REG_NOTIFY_CHANGE_LAST_SET = 0x00000004
        while not self._stop.is_set():
            for hroot, subkey in watch_specs:
                if self._stop.is_set():
                    break
                hkey = ctypes.c_void_p()
                res = RegOpenKeyExW(hroot, subkey, 0, 0x20019, ctypes.byref(hkey))  # KEY_READ | KEY_NOTIFY approximate
                if res != 0:
                    # cannot open - skip
                    continue
                # block until change or timeout-ish: RegNotifyChangeKeyValue blocks, so call and rely on stop flag to break after it returns (we use short timeout by using a separate thread per key would be better)
                try:
                    # Wait for change (blocking)
                    rc = RegNotifyChangeKeyValue(hkey, True, REG_NOTIFY_CHANGE_NAME | REG_NOTIFY_CHANGE_LAST_SET, None, False)
                    # when returns, enumerate differences by reading values (we simply emit a generic event)
                    # We try to detect added/removed by snapshotting quickly (but here simple)
                    self._emit("Изменён реестр", path=f"{subkey}", pid=self.main_pid, extra={"root": int(hroot)})
                except Exception:
                    pass
                try:
                    RegCloseKey(hkey)
                except Exception:
                    pass
            # small sleep to avoid busy loop
            time.sleep(0.1)

    # ---------------------------
    # Process creation watcher (fast poll)
    # ---------------------------
    def _start_process_watcher(self):
        t = threading.Thread(target=self._proc_watch_loop, daemon=True)
        t.start()
        self._proc_watch_thread = t

    def _proc_watch_loop(self):
        """
        Следим за появлением новых процессов, но добавляем в tracked_pids ТОЛЬКО
        те процессы, у которых в цепочке родителей есть self.main_pid.
        Это предотвращает слежение за всеми процессами системы.
        """
        seen = set()
        # инициализация: запомним текущие PID, но не добавляем их в tracked_pids (кроме main_pid)
        try:
            for p in psutil.process_iter(['pid']):
                seen.add(p.pid)
        except Exception:
            pass

        # хелпер: проверяет, является ли candidate_pid потомком main_pid
        def _is_descendant_of_main(candidate_pid):
            try:
                cur = psutil.Process(candidate_pid)
            except Exception:
                return False
            # пробегаем цепочку родителей вверх, пока не дойдём до 0 или найден main_pid
            depth = 0
            max_depth = 40  # safety
            while depth < max_depth:
                try:
                    ppid = cur.ppid()
                except Exception:
                    return False
                if not ppid or ppid == 0:
                    return False
                if ppid == self.main_pid:
                    return True
                # try move one level up
                try:
                    cur = psutil.Process(ppid)
                except psutil.NoSuchProcess:
                    return False
                except Exception:
                    return False
                depth += 1
            return False

        while not self._stop.is_set():
            try:
                current = set()
                # we iterate процессы быстро, но не добавляем в tracked_pids все подряд
                for p in psutil.process_iter(['pid','exe','create_time','cwd','cmdline','ppid']):
                    pid = p.info.get('pid')
                    current.add(pid)
                    if pid not in seen:
                        # новый процесс появился — проверяем, связан ли он с нашим main_pid
                        try:
                            parent_pid = p.info.get('ppid', None)
                        except Exception:
                            parent_pid = None

                        is_related = False
                        # Быстрая проверка: если непосредственным родителем является tracked pid -> добавим
                        if parent_pid and parent_pid in self.tracked_pids:
                            is_related = True
                        else:
                            # Иначе проверяем цепочку предков до main_pid (без дорогостоящего полного подъёма для всех)
                            if self.main_pid:
                                # только при наличии main_pid имеет смысл
                                try:
                                    if _is_descendant_of_main(pid):
                                        is_related = True
                                except Exception:
                                    is_related = False

                        if is_related:
                            # считаем это дочерним — добавляем в tracked set и инициализируем known_open_files
                            self.tracked_pids.add(pid)
                            self.known_open_files.setdefault(pid, set())
                            # попытаемся получить exe/cwd для логирования
                            try:
                                exe = p.info.get('exe') or (p.exe() if hasattr(p, 'exe') else "")
                            except Exception:
                                exe = ""
                            try:
                                cwd = p.info.get('cwd') or ""
                            except Exception:
                                cwd = ""
                            # регистрация folder_owner если есть cwd в temp
                            try:
                                if cwd:
                                    normcwd = os.path.normcase(os.path.abspath(cwd))
                                    self.folder_owner[normcwd] = pid
                            except Exception:
                                pass
                            # эмит события о создании дочернего процесса
                            self._emit("Создан процесс (дочерний)", path=exe, pid=pid, extra={"ppid": parent_pid})
                seen = current
            except Exception:
                # молча игнорируем редкие ошибки psutil
                pass
            time.sleep(0.35)  # немного увеличил интервал, чтобы снизить нагрузку


    # ---------------------------
    # scanning fallback for directories (limited depth)
    # ---------------------------
    def _scan_candidate_dirs(self, since_ts):
        results = []
        for root in self.watch_dirs:
            if not root or not os.path.exists(root):
                continue
            try:
                with os.scandir(root) as it:
                    for entry in it:
                        try:
                            full = os.path.join(root, entry.name)
                            if full in self.known_scanned_files:
                                continue
                            try:
                                ctime = os.path.getctime(full)
                            except Exception:
                                ctime = 0
                            if ctime > since_ts:
                                results.append((full, entry.is_dir()))
                                self.known_scanned_files.add(full)
                            # one-level deep scan
                            if entry.is_dir():
                                try:
                                    with os.scandir(full) as it2:
                                        for e2 in it2:
                                            try:
                                                full2 = os.path.join(full, e2.name)
                                                if full2 in self.known_scanned_files:
                                                    continue
                                                try:
                                                    ctime2 = os.path.getctime(full2)
                                                except Exception:
                                                    ctime2 = 0
                                                if ctime2 > since_ts:
                                                    results.append((full2, e2.is_dir()))
                                                    self.known_scanned_files.add(full2)
                                            except Exception:
                                                continue
                                except Exception:
                                    pass
                        except Exception:
                            continue
            except Exception:
                continue
        return results

    # ---------------------------
    # main run (process start + spawn watchers)
    # ---------------------------
    def run(self):
        try:
            self.status_signal.emit("Запуск процесса...")
            # start process (elevate if needed) - reuse existing logic you had before
            pid = None
            if self.require_elevate:
                class SHELLEXECUTEINFO(ctypes.Structure):
                    _fields_ = [
                        ('cbSize', ctypes.c_ulong),
                        ('fMask', ctypes.c_ulong),
                        ('hwnd', ctypes.c_void_p),
                        ('lpVerb', ctypes.c_wchar_p),
                        ('lpFile', ctypes.c_wchar_p),
                        ('lpParameters', ctypes.c_wchar_p),
                        ('lpDirectory', ctypes.c_wchar_p),
                        ('nShow', ctypes.c_int),
                        ('hInstApp', ctypes.c_void_p),
                        ('lpIDList', ctypes.c_void_p),
                        ('lpClass', ctypes.c_wchar_p),
                        ('hkeyClass', ctypes.c_void_p),
                        ('dwHotKey', ctypes.c_ulong),
                        ('hIcon', ctypes.c_void_p),
                        ('hProcess', ctypes.c_void_p)
                    ]
                SEE_MASK_NOCLOSEPROCESS = 0x00000040
                SW_SHOWNORMAL = 1
                sei = SHELLEXECUTEINFO()
                sei.cbSize = ctypes.sizeof(SHELLEXECUTEINFO)
                sei.fMask = SEE_MASK_NOCLOSEPROCESS
                sei.hwnd = None
                sei.lpVerb = "runas"
                sei.lpFile = self.exe_path
                sei.lpParameters = self.args or ""
                sei.lpDirectory = None
                sei.nShow = SW_SHOWNORMAL
                ok = ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei))
                if not ok:
                    self.status_signal.emit("Ошибка запуска (UAC)")
                    self._emit("Ошибка: не удалось запустить с повышением прав")
                    self.finished_signal.emit()
                    return
                try:
                    GetProcessId = ctypes.windll.kernel32.GetProcessId
                    GetProcessId.argtypes = [ctypes.c_void_p]
                    GetProcessId.restype = ctypes.c_ulong
                    pid = GetProcessId(sei.hProcess)
                except Exception:
                    pid = None
            else:
                proc = psutil.Popen([self.exe_path] + (self.args.split() if self.args else []))
                pid = proc.pid

            if not pid:
                # fallback find recent
                time.sleep(0.5)
                for p in psutil.process_iter(['pid','exe']):
                    try:
                        if p.info.get('exe') and os.path.normcase(p.info['exe']) == os.path.normcase(self.exe_path):
                            pid = p.info['pid']
                            break
                    except Exception:
                        continue

            if not pid:
                self._emit("Ошибка: не удалось получить PID процесса")
                self.status_signal.emit("Ошибка запуска")
                self.finished_signal.emit()
                return

            self.main_pid = pid
            self.start_ts = time.time()
            self.tracked_pids = set([self.main_pid])
            self.known_open_files.setdefault(self.main_pid, set())

            self._emit("Процесс запущен", path=self.exe_path, pid=self.main_pid)
            self.status_signal.emit("Процесс запущен")

            # initial population of open_files of main process
            try:
                pmain = psutil.Process(self.main_pid)
                try:
                    of = pmain.open_files()
                except Exception:
                    of = []
                for fh in of:
                    try:
                        self.known_open_files[self.main_pid].add(self._norm(fh.path))
                    except Exception:
                        pass
            except Exception:
                pass

            # start watchers
            self._start_fs_watchers()
            self._start_registry_watcher()
            self._start_process_watcher()

            # main loop: poll open_files + small scans + registry snapshot checking already handled in reg thread
            last_scan_time = time.time()
            while not self._stop.is_set():
                # update children mapping & known_open_files
                # (children detection is in the proc watcher which also adds to tracked_pids)
                # poll open_files to catch handles opened/closed quickly
                for pid_check in list(self.tracked_pids):
                    try:
                        p = psutil.Process(pid_check)
                    except psutil.NoSuchProcess:
                        if pid_check in self.tracked_pids:
                            self._emit("Процесс завершён", path="", pid=pid_check)
                            self.tracked_pids.discard(pid_check)
                            self.known_open_files.pop(pid_check, None)
                        continue
                    try:
                        ofiles = p.open_files()
                    except Exception:
                        ofiles = []
                    current = set()
                    for fh in ofiles:
                        try:
                            current.add(self._norm(fh.path))
                        except Exception:
                            continue
                    prev = self.known_open_files.get(pid_check, set())
                    new = current - prev
                    for nf in new:
                        action = "Создана папка" if os.path.isdir(nf) else "Создан файл"
                        self._emit(action, path=nf, pid=pid_check, extra={"method":"open_files"})
                    self.known_open_files[pid_check] = current

                # fallback small scan in watch_dirs to catch fleeting creates
                nowt = time.time()
                new_items = self._scan_candidate_dirs(last_scan_time)
                last_scan_time = nowt
                for p, is_dir in new_items:
                    pid_attr, method = self._attribute_path(p, is_dir)
                    action = "Создана папка" if is_dir else "Создан файл"
                    self._emit(action, path=self._norm(p), pid=pid_attr, extra={"method": method, "scan": True})

                # check main process exit
                try:
                    if not psutil.pid_exists(self.main_pid):
                        self._emit("Главный процесс завершён", path=self.exe_path, pid=self.main_pid)
                        break
                except Exception:
                    pass

                time.sleep(self.poll_interval)

            # cleanup: threads are daemon and will exit on stop flag
            self.status_signal.emit("Мониторинг завершён")
            self.finished_signal.emit()

        except Exception as e:
            self._emit("Ошибка монитора", path=str(e), pid=self.main_pid)
            self.status_signal.emit("Ошибка")
            self.finished_signal.emit()

    # reuse prior simple scan function (from your module)
    def _scan_candidate_dirs(self, since_ts):
        results = []
        for root in self.watch_dirs:
            if not root or not os.path.exists(root):
                continue
            try:
                with os.scandir(root) as it:
                    for entry in it:
                        try:
                            full = os.path.join(root, entry.name)
                            if full in self.known_scanned_files:
                                continue
                            try:
                                ctime = os.path.getctime(full)
                            except Exception:
                                ctime = 0
                            if ctime > since_ts:
                                results.append((full, entry.is_dir()))
                                self.known_scanned_files.add(full)
                            if entry.is_dir():
                                try:
                                    with os.scandir(full) as it2:
                                        for e2 in it2:
                                            try:
                                                full2 = os.path.join(full, e2.name)
                                                if full2 in self.known_scanned_files:
                                                    continue
                                                try:
                                                    ctime2 = os.path.getctime(full2)
                                                except Exception:
                                                    ctime2 = 0
                                                if ctime2 > since_ts:
                                                    results.append((full2, e2.is_dir()))
                                                    self.known_scanned_files.add(full2)
                                            except Exception:
                                                continue
                                except Exception:
                                    pass
                        except Exception:
                            continue
            except Exception:
                continue
        return results
