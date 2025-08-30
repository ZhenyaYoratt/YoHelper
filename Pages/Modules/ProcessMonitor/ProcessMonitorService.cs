using Microsoft.Win32;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Management; // Требует System.Management NuGet / reference
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;

namespace YoHelper.Pages.Modules.ProcessMonitor
{
    /// <summary>
    /// Служба, которая: запускает процесс, отслеживает дочерние процессы через WMI,
    /// отслеживает создание/удаление файлов в корнях логических дисков через FileSystemWatcher,
    /// и базово отслеживает изменение реестра (HKCU/HKLM) через P/Invoke.
    /// 
    /// Примечание: полностью идентифицировать, какой процесс совершил определённый файловый/реестровый вызов,
    /// без использования ETW/TraceEvent или драйвера — сложно. Здесь реализована рабочая и понятная приближённая логика:
    /// - процессы (запуск/завершение) отслеживаются и логируются с PID
    /// - файловые события логируются глобально (с отметкой времени)
    /// - изменения в реестре логируются как событие изменения ключа
    /// 
    /// Для продакшн-уровня атрибуции рекомендуется интеграция с ETW / Windows Event Tracing.
    /// </summary>
    public class ProcessMonitorService
    {
        // События могут быть отсутствующими — помечаем nullable
        public event Action<LogEntry>? LogGenerated;
        public event Action<string>? StatusChanged;

        // Поля, которые инициализируются при старте
        private Process? _rootProcess;
        private int _rootPid;
        private readonly HashSet<int> _trackedPids = new HashSet<int>();

        private ManagementEventWatcher? _procStartWatcher;
        private ManagementEventWatcher? _procStopWatcher;

        private readonly List<FileSystemWatcher> _fsWatchers = new List<FileSystemWatcher>();
        private CancellationTokenSource? _cts;

        private RegistryWatcher? _registryWatcherHKCU;
        private RegistryWatcher? _registryWatcherHKLM;

        public async Task StartAsync(string exePath)
        {
            // Инициализируем CTS здесь — раньше он мог быть null
            _cts = new CancellationTokenSource();

            StatusChanged?.Invoke("Запуск...");

            var psi = new ProcessStartInfo(exePath)
            {
                UseShellExecute = false,
                WorkingDirectory = Path.GetDirectoryName(exePath)
            };

            try
            {
                _rootProcess = Process.Start(psi);
            }
            catch (System.ComponentModel.Win32Exception wex)
            {
                // Частая причина — отказ в доступе или блокировка запуска процесса
                var msg = $"Win32Exception при запуске процесса: {wex.Message}";
                StatusChanged?.Invoke("Ошибка");
                Log(msg, "Ошибка");
                throw;
            }
            catch (Exception ex)
            {
                var msg = $"Ошибка при запуске процесса: {ex.Message}";
                StatusChanged?.Invoke("Ошибка");
                Log(msg, "Ошибка");
                throw;
            }

            if (_rootProcess == null)
            {
                throw new InvalidOperationException("Не удалось запустить процесс.");
            }

            _rootPid = _rootProcess.Id;
            _trackedPids.Add(_rootPid);

            try
            {
                _rootProcess.EnableRaisingEvents = true;
                _rootProcess.Exited += (s, e) => OnProcessExited(_rootPid);
            }
            catch { }

            Log($"Процесс запущен (PID={_rootPid})", "Процесс запущен");
            StatusChanged?.Invoke($"Мониторинг PID={_rootPid}");

            SetupProcessWatchers();
            SetupFileSystemWatchers();
            SetupRegistryWatchers();

            // Поддерживаем работу пока root процесс жив
            await Task.Run(() =>
            {
                try
                {
                    _rootProcess?.WaitForExit();
                }
                catch { }
            }, _cts.Token);

            // Когда процесс завершился — остановим всё
            Stop();
        }

        public void Stop()
        {
            try
            {
                _cts?.Cancel();
                _cts = null;
            }
            catch { }

            try { _procStartWatcher?.Stop(); _procStartWatcher?.Dispose(); } catch { }
            try { _procStopWatcher?.Stop(); _procStopWatcher?.Dispose(); } catch { }

            foreach (var w in _fsWatchers)
            {
                try { w.EnableRaisingEvents = false; w.Dispose(); } catch { }
            }
            _fsWatchers.Clear();

            try { _registryWatcherHKCU?.Dispose(); } catch { }
            try { _registryWatcherHKLM?.Dispose(); } catch { }

            StatusChanged?.Invoke("Остановлено");
        }

        private void SetupProcessWatchers()
        {
            // Процессы: наблюдаем создание/удаление процессов в системе и фильтруем по ParentProcessId
            try
            {
                var startQuery = new WqlEventQuery("SELECT * FROM __InstanceCreationEvent WITHIN 1 WHERE TargetInstance ISA 'Win32_Process'");
                _procStartWatcher = new ManagementEventWatcher(startQuery);
                _procStartWatcher.EventArrived += ProcStart_EventArrived;
                _procStartWatcher.Start();

                var stopQuery = new WqlEventQuery("SELECT * FROM __InstanceDeletionEvent WITHIN 1 WHERE TargetInstance ISA 'Win32_Process'");
                _procStopWatcher = new ManagementEventWatcher(stopQuery);
                _procStopWatcher.EventArrived += ProcStop_EventArrived;
                _procStopWatcher.Start();
            }
            catch (Exception ex)
            {
                Log($"Не удалось запустить WMI watchers: {ex.Message}", "Ошибка");
            }
        }

        private void ProcStart_EventArrived(object sender, EventArrivedEventArgs e)
        {
            try
            {
                var mo = (ManagementBaseObject?)e.NewEvent["TargetInstance"];
                if (mo == null) return;

                var pid = Convert.ToInt32(mo["ProcessId"]);
                var ppid = Convert.ToInt32(mo["ParentProcessId"]);
                var name = mo["Name"]?.ToString() ?? string.Empty;

                // Если parent == tracked or parent is descendant, добавляем
                if (_trackedPids.Contains(ppid) || IsDescendant(ppid))
                {
                    _trackedPids.Add(pid);
                    Log($"Процесс создан: {name} (PID={pid}, PPID={ppid})", "Процесс создан");
                }
            }
            catch { }
        }

        private bool IsDescendant(int ppid)
        {
            // Быстрая проверка: если родитель уже отслеживается
            return _trackedPids.Contains(ppid);
        }

        private void ProcStop_EventArrived(object sender, EventArrivedEventArgs e)
        {
            try
            {
                var mo = (ManagementBaseObject?)e.NewEvent["TargetInstance"];
                if (mo == null) return;

                var pid = Convert.ToInt32(mo["ProcessId"]);
                var name = mo["Name"]?.ToString() ?? string.Empty;

                if (_trackedPids.Contains(pid))
                {
                    Log($"Процесс завершён: {name} (PID={pid})", "Процесс завершён");
                    _trackedPids.Remove(pid);
                }
            }
            catch { }
        }

        private void OnProcessExited(int pid)
        {
            Log($"Процесс с PID={pid} завершён", "Процесс завершён");
        }

        private void SetupFileSystemWatchers()
        {
            try
            {
                var drives = DriveInfo.GetDrives().Where(d => d.IsReady).Select(d => d.RootDirectory.FullName).ToArray();
                foreach (var root in drives)
                {
                    try
                    {
                        var fsw = new FileSystemWatcher(root)
                        {
                            IncludeSubdirectories = true,
                            EnableRaisingEvents = true,
                            NotifyFilter = NotifyFilters.FileName | NotifyFilters.DirectoryName | NotifyFilters.Size | NotifyFilters.LastWrite
                        };
                        fsw.Created += Fsw_Created;
                        fsw.Deleted += Fsw_Deleted;
                        fsw.Renamed += Fsw_Renamed;
                        _fsWatchers.Add(fsw);
                    }
                    catch (Exception ex)
                    {
                        Log($"Не удалось добавить watcher на {root}: {ex.Message}", "Ошибка");
                    }
                }
            }
            catch (Exception ex)
            {
                Log($"Ошибка при создании FileSystemWatchers: {ex.Message}", "Ошибка");
            }
        }

        private void Fsw_Created(object sender, FileSystemEventArgs e)
        {
            var isDir = Directory.Exists(e.FullPath);
            Log($"{(isDir ? "Создана папка" : "Создан файл")} — {e.FullPath}", isDir ? "Создана папка" : "Создан файл");
        }

        private void Fsw_Deleted(object sender, FileSystemEventArgs e)
        {
            Log($"Удалён — {e.FullPath}", "Удалён");
        }

        private void Fsw_Renamed(object sender, RenamedEventArgs e)
        {
            Log($"Переименован: {e.OldFullPath} -> {e.FullPath}", "Переименован");
        }

        private void SetupRegistryWatchers()
        {
            try
            {
                _registryWatcherHKCU = new RegistryWatcher(RegistryHive.CurrentUser, (entry) => Log(entry, "Установлено значение ключа / реестр"));
                _registryWatcherHKLM = new RegistryWatcher(RegistryHive.LocalMachine, (entry) => Log(entry, "Установлено значение ключа / реестр"));

                _registryWatcherHKCU.Start();
                _registryWatcherHKLM.Start();
            }
            catch (Exception ex)
            {
                Log($"Не удалось запустить наблюдение за реестром: {ex.Message}", "Ошибка");
            }
        }

        /// <summary>
        /// Подключиться к уже запущенному (возможно повышенному) процессу и начать мониторинг.
        /// </summary>
        public async Task MonitorExistingProcessAsync(Process process)
        {
            if (process == null) throw new ArgumentNullException(nameof(process));

            _cts = new CancellationTokenSource();

            _rootProcess = process;
            _rootPid = process.Id;
            _trackedPids.Add(_rootPid);

            try
            {
                _rootProcess.EnableRaisingEvents = true;
                _rootProcess.Exited += (s, e) => OnProcessExited(_rootPid);
            }
            catch { }

            Log($"Подключён к процессу (PID={_rootPid})", "Процесс запущен");
            StatusChanged?.Invoke($"Мониторинг PID={_rootPid}");

            SetupProcessWatchers();
            SetupFileSystemWatchers();
            SetupRegistryWatchers();

            await Task.Run(() =>
            {
                try
                {
                    process.WaitForExit();
                }
                catch { }
            }, _cts.Token);

            Stop();
        }

        private void Log(string message, string type = "Инфо")
        {
            LogGenerated?.Invoke(new LogEntry { Timestamp = DateTime.Now, Type = type, Message = message });
        }
    }
}
