using System;
using System.Runtime.InteropServices;
using Microsoft.Win32;
using System.Threading;

namespace YoHelper.Pages.Modules.ProcessMonitor
{
    // Минимальный наблюдатель реестра с использованием RegNotifyChangeKeyValue.
    // Отслеживает любое изменение в выбранном корневом разделе (HKCU/HKLM) — сигнализирует о смене.
    public class RegistryWatcher : IDisposable
    {
        private readonly RegistryHive _hive;
        private readonly Action<string> _onChange;
        private CancellationTokenSource _cts;

        public RegistryWatcher(RegistryHive hive, Action<string> onChange)
        {
            _hive = hive;
            _onChange = onChange;
        }

        public void Start()
        {
            _cts = new CancellationTokenSource();
            var t = new Thread(() => WatchLoop(_cts.Token)) { IsBackground = true };
            t.Start();
        }

        public void Dispose()
        {
            try { _cts?.Cancel(); } catch { }
        }

        private void WatchLoop(CancellationToken token)
        {
            IntPtr hKey = IntPtr.Zero;
            uint result = RegOpenKeyEx((UIntPtr)_hive, "", 0, KEY_READ, out hKey);
            if (result != 0)
            {
                _onChange?.Invoke($"Не удалось открыть корень реестра {_hive} — код {result}");
                return;
            }

            try
            {
                while (!token.IsCancellationRequested)
                {
                    var waitRes = RegNotifyChangeKeyValue(hKey, true, REG_NOTIFY_CHANGE_NAME | REG_NOTIFY_CHANGE_LAST_SET, IntPtr.Zero, false);
                    // Когда возращается — отправим уведомление
                    _onChange?.Invoke($"Обнаружено изменение в реестре: {_hive}");
                    Thread.Sleep(500); // предотвращаем спам
                }
            }
            finally
            {
                if (hKey != IntPtr.Zero) RegCloseKey(hKey);
            }
        }

        #region PInvoke
        private const uint KEY_READ = 0x20019;
        private const uint REG_NOTIFY_CHANGE_NAME = 0x00000001;
        private const uint REG_NOTIFY_CHANGE_ATTRIBUTES = 0x00000002;
        private const uint REG_NOTIFY_CHANGE_LAST_SET = 0x00000004;

        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        private static extern uint RegOpenKeyEx(UIntPtr hKey, string lpSubKey, uint ulOptions, uint samDesired, out IntPtr phkResult);

        [DllImport("advapi32.dll", SetLastError = true)]
        private static extern uint RegNotifyChangeKeyValue(IntPtr hKey, bool bWatchSubtree, uint dwNotifyFilter, IntPtr hEvent, bool fAsynchronous);

        [DllImport("advapi32.dll", SetLastError = true)]
        private static extern uint RegCloseKey(IntPtr hKey);
        #endregion
    }
}
