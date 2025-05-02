import os
import winreg
import pythoncom
import win32com.client
import wmi
import datetime
from .logger import log, ERROR

# Constants for registry paths and startup folders
RUN_SUBKEYS = [
    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"),
]
RUNONCE_SUBKEYS = [
    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce"),
]
WINLOGON_SUBKEYS = {
    'x64': (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"),
    'x86': (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows NT\CurrentVersion\Winlogon"),
}

# Helper functions

def load_offline_hive(drive, mount_name="OFFLINE_SOFTWARE"):
    """
    Load the SOFTWARE hive from an offline Windows installation on specified drive.
    Returns mount_name if loaded, else None.
    """
    hive_path = rf"{drive}\Windows\System32\config\SOFTWARE"
    if os.path.exists(hive_path):
        try:
            winreg.LoadKey(winreg.HKEY_LOCAL_MACHINE, mount_name, hive_path)
            return mount_name
        except PermissionError:
            pass
    return None


def unload_offline_hive(mount_name):
    try:
        winreg.UnloadKey(winreg.HKEY_LOCAL_MACHINE, mount_name)
    except Exception:
        pass


def read_registry_values(root, subkey):
    """Read all values under root\subkey."""
    entries = []
    try:
        key = winreg.OpenKey(root, subkey, 0, winreg.KEY_READ)
    except FileNotFoundError:
        return entries
    i = 0
    while True:
        try:
            name, data, typ = winreg.EnumValue(key, i)
            entries.append((name, data, typ, subkey))
            i += 1
        except OSError:
            break
    winreg.CloseKey(key)
    return entries

def get_startup_folders():
    folders = {}
    base = r"C:\Users"
    if os.path.isdir(base):
        for user in os.listdir(base):
            path = os.path.join(base, user, r"AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup")
            if os.path.isdir(path):
                folders[user] = path
    all_users = r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp"
    if os.path.isdir(all_users):
        folders['All Users'] = all_users
    return folders

def read_registry_values(root, subkey):
    entries = []
    try:
        key = winreg.OpenKey(root, subkey, 0, winreg.KEY_READ)
    except FileNotFoundError:
        return entries
    i = 0
    while True:
        try:
            name, data, typ = winreg.EnumValue(key, i)
            entries.append((name, data, typ, subkey))
            i += 1
        except OSError:
            break
    winreg.CloseKey(key)
    return entries

def write_registry_value(root, subkey, name, data, typ):
    key = winreg.CreateKeyEx(root, subkey, 0, winreg.KEY_WRITE)
    winreg.SetValueEx(key, name, 0, typ, data)
    winreg.CloseKey(key)

def delete_registry_value(root, subkey, name):
    key = winreg.OpenKey(root, subkey, 0, winreg.KEY_SET_VALUE)
    winreg.DeleteValue(key, name)
    winreg.CloseKey(key)

def get_autorun_registry(runonce=False, drive='C:'):
    """
    Return list of autorun entries from registry. If drive != 'C:', temporarily loads offline hive.
    Each entry: { name, data, type, location, hive, runonce }
    """
    prefix = None
    mount = None
    if drive.upper().rstrip(':') != os.environ.get('SYSTEMDRIVE', 'C').rstrip(':'):
        mount = load_offline_hive(drive)
        if mount:
            prefix = mount
    subkeys = RUNONCE_SUBKEYS if runonce else RUN_SUBKEYS
    results = []
    for hive, sub in subkeys:
        root = hive
        path = sub
        if prefix:
            root = winreg.HKEY_LOCAL_MACHINE
            path = prefix + '\\' + sub
        for name, data, typ, loc in read_registry_values(root, path):
            results.append({
                'name': name,
                'data': data,
                'type': typ,
                'location': loc,
                'hive': root,
                'runonce': runonce
            })
    if mount:
        unload_offline_hive(mount)
    return results

def add_autorun_registry(name, data, typ, hive, subkey, runonce=False):
    write_registry_value(hive, subkey, name, data, typ)

def remove_autorun_registry(entries):
    for e in entries:
        delete_registry_value(e['hive'], e['location'], e['name'])

def edit_autorun_registry(old, new):
    if old['name'] != new['name'] or old['location'] != new['location'] or old['hive'] != new['hive']:
        delete_registry_value(old['hive'], old['location'], old['name'])
    write_registry_value(new['hive'], new['location'], new['name'], new['data'], new['type'])

def get_startup_folder_entries():
    out = {}
    for user, folder in get_startup_folders().items():
        items = []
        for fname in os.listdir(folder):
            full = os.path.join(folder, fname)
            if os.path.isfile(full):
                stat = os.stat(full)
                items.append({
                    'file': fname,
                    'created': datetime.datetime.fromtimestamp(stat.st_ctime),
                    'accessed': datetime.datetime.fromtimestamp(stat.st_atime),
                    'modified': datetime.datetime.fromtimestamp(stat.st_mtime),
                    'path': full,
                    'user': user
                })
        out[user] = items
    return out

def add_startup_file(folder, name, src_path):
    dst = os.path.join(folder, name)
    with open(dst, 'w'):
        pass

def remove_startup_files(entries):
    for e in entries:
        try:
            os.remove(e['path'])
        except OSError:
            pass

def edit_startup_file(entry, new_name, new_folder):
    old = entry['path']
    new = os.path.join(new_folder, new_name)
    os.rename(old, new)

def get_scheduled_tasks():
    tasks = []
    try:
        pythoncom.CoInitialize()
        scheduler = win32com.client.Dispatch('Schedule.Service')
        scheduler.Connect()
        TASK_STATE = {0: 'Неизвестно', 1: 'Отключено', 2: 'В очереди', 3: 'Готов к работе', 4: 'Выполняется'}
        folders = [scheduler.GetFolder('\\')]
        while folders:
            folder = folders.pop(0)
            folders += list(folder.GetFolders(0))
            for task in folder.GetTasks(1):
                tasks.append({
                    'name': task.Name,
                    'state': TASK_STATE.get(task.State, 'Неизвестно'),
                    'path': task.Path,
                    'last_run': task.LastRunTime,
                    'last_result': task.LastTaskResult
                })
    except Exception as e:
        log('Не удалось подключиться к службе Планировщик задач', ERROR)
    return tasks

def get_winlogon_entries(drive='C:'):
    """
    Return list of Winlogon Shell/Userinit entries. Loads offline hive if needed.
    Each entry: { name, data, type, location, hive, arch }
    """
    prefix = None
    mount = None
    if drive.upper().rstrip(':') != os.environ.get('SYSTEMDRIVE', 'C').rstrip(':'):
        mount = load_offline_hive(drive)
        if mount:
            prefix = mount
    results = []
    for arch, (hive, sub) in WINLOGON_SUBKEYS.items():
        root = hive
        path = sub
        if prefix:
            root = winreg.HKEY_LOCAL_MACHINE
            path = prefix + '\\' + sub
        for name, data, typ, loc in read_registry_values(root, path):
            if name.lower() in ('shell', 'userinit'):
                results.append({
                    'name': name,
                    'data': data,
                    'type': typ,
                    'location': loc,
                    'hive': root,
                    'arch': arch
                })
    if mount:
        unload_offline_hive(mount)
    return results

_wmi_conn = wmi.WMI()
def get_services():
    services = []
    for svc in _wmi_conn.Win32_Service():
        services.append({
            'name': svc.Name,
            'display_name': svc.DisplayName,
            'state': svc.State,
            'start_mode': svc.StartMode,
            'description': svc.Description
        })
    return services