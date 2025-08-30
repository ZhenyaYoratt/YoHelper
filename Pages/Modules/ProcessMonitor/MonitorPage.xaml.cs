using Microsoft.UI.Dispatching;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using System;
using System.Collections.ObjectModel;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading.Tasks;
using System.Xml.Linq;
using Windows.ApplicationModel.DataTransfer;
using Windows.Storage.Pickers;
using Windows.System;
using Windows.UI.Core;
using WinRT.Interop;

// To learn more about WinUI, the WinUI project structure,
// and more about our project templates, see: http://aka.ms/winui-project-info.

namespace YoHelper.Pages.Modules.ProcessMonitor
{
    /// <summary>
    /// An empty page that can be used on its own or navigated to within a Frame.
    /// </summary>
    public sealed partial class MonitorPage : Page
    {
        private readonly ObservableCollection<LogEntry> _logs = new ObservableCollection<LogEntry>();
        private ProcessMonitorService? _monitorService;
        private bool _requiresElevation = false;

        public MonitorPage()
        {
            this.InitializeComponent();
            LogsListView.ItemsSource = _logs;
        }

        private async void Browse_Click(object sender, RoutedEventArgs e)
        {
            var picker = new FileOpenPicker();
            try
            {
                var hwnd = WindowNative.GetWindowHandle(App.MainWindow);
                InitializeWithWindow.Initialize(picker, hwnd);
            }
            catch { }

            picker.FileTypeFilter.Add(".exe");
            var file = await picker.PickSingleFileAsync();
            if (file != null)
            {
                ExePathTextBox.Text = file.Path;
                await UpdateElevationIconAsync(file.Path);
            }
        }

        // Обработчик изменения текста — обновляет иконку в реальном времени
        private void ExePathTextBox_TextChanged(object sender, TextChangedEventArgs e)
        {
            var path = ExePathTextBox.Text?.Trim();
            if (!string.IsNullOrEmpty(path) && File.Exists(path))
            {
                _ = UpdateElevationIconAsync(path);
            }
            else
            {
                UACIcon.Visibility = Visibility.Collapsed;
                _requiresElevation = false;
            }
        }

        // Метод, который показывает/скрывает UAC-иконку (вызывается асинхронно)
        private async Task UpdateElevationIconAsync(string path)
        {
            try
            {
                _requiresElevation = await Task.Run(() => RequiresElevationByManifest(path));
                DispatcherQueue.TryEnqueue(() => UACIcon.Visibility = _requiresElevation ? Visibility.Visible : Visibility.Collapsed);
            }
            catch
            {
                DispatcherQueue.TryEnqueue(() => UACIcon.Visibility = Visibility.Collapsed);
            }
        }

        private async void Start_Click(object sender, RoutedEventArgs e)
        {
            var path = ExePathTextBox.Text?.Trim();
            if (string.IsNullOrEmpty(path) || !File.Exists(path))
            {
                StatusText.Text = "Путь не указан или файл не найден.";
                return;
            }

            // Блокируем элементы управления выбора
            ExePathTextBox.IsEnabled = false;
            BrowseButton.IsEnabled = false;
            StartButton.IsEnabled = false;
            StopButton.IsEnabled = true;

            StatusText.Text = "Запуск процесса...";

            _monitorService = new ProcessMonitorService();
            _monitorService.LogGenerated += MonitorService_LogGenerated;
            _monitorService.StatusChanged += (s) => DispatcherQueue.TryEnqueue(() => StatusText.Text = s);

            //try
            //{
                if (_requiresElevation)
                {
                    // Подтверждение пользователю
                    var cd = new ContentDialog
                    {
                        Title = "Требуется повышение",
                        Content = "Этот файл требует запуска с повышенными правами. Запустить от имени администратора?",
                        PrimaryButtonText = "Да",
                        CloseButtonText = "Нет"
                    };

                    // Установим XamlRoot — из текущей страницы, либо из окна, если XamlRoot страницы ещё null
                    cd.XamlRoot = this.XamlRoot ?? ((FrameworkElement)App.MainWindow.Content).XamlRoot;

                    var res = await cd.ShowAsync();
                    if (res != ContentDialogResult.Primary)
                    {
                        StatusText.Text = "Запуск отменён пользователем.";

                        // Разблокируем элементы управления
                        ExePathTextBox.IsEnabled = true;
                        BrowseButton.IsEnabled = true;
                        StartButton.IsEnabled = true;
                        StopButton.IsEnabled = false;
                        return;
                    }

                    var psi = new ProcessStartInfo(path)
                    {
                        UseShellExecute = true,
                        Verb = "runas",
                        WorkingDirectory = Path.GetDirectoryName(path)
                    };

                    try
                    {
                        var proc = Process.Start(psi);
                        if (proc == null)
                        {
                            throw new InvalidOperationException("Не удалось запустить процесс с повышением.");
                        }

                        // Небольшая пауза, чтобы процесс успел появиться в системе, затем подключаемся к нему
                        await Task.Delay(500);
                        await _monitorService.MonitorExistingProcessAsync(proc);
                    }
                    catch (System.ComponentModel.Win32Exception wex)
                    {
                        _monitorService = null;
                        StatusText.Text = "Win32Exception при запуске процесса: " + wex.Message;

                        // Разблокируем элементы управления
                        ExePathTextBox.IsEnabled = true;
                        BrowseButton.IsEnabled = true;
                        StartButton.IsEnabled = true;
                        StopButton.IsEnabled = false;
                        return;
                    }
                }
                else
                {
                    await _monitorService.StartAsync(path);
                }
            //}
            //catch (Exception ex)
            //{
            //    _monitorService = null;
            //    StatusText.Text = "Ошибка: " + ex.Message;

            //    // Разблокируем элементы управления
            //    ExePathTextBox.IsEnabled = true;
            //    BrowseButton.IsEnabled = true;
            //    StartButton.IsEnabled = true;
            //    StopButton.IsEnabled = false;
            //}
        }

        private void MonitorService_LogGenerated(LogEntry obj)
        {
            // Обновление UI
            DispatcherQueue.TryEnqueue(() => _logs.Insert(0, obj));
        }

        private static bool RequiresElevationByManifest(string filePath)
        {
            if (!File.Exists(filePath)) return false;

            IntPtr hModule = IntPtr.Zero;
            try
            {
                const uint LOAD_LIBRARY_AS_DATAFILE = 0x00000002;
                hModule = LoadLibraryExW(filePath, IntPtr.Zero, LOAD_LIBRARY_AS_DATAFILE);
                if (hModule == IntPtr.Zero) return false;

                var res = FindResourceW(hModule, new IntPtr(1), new IntPtr(24)); // RT_MANIFEST=24, resource id=1
                if (res == IntPtr.Zero) return false;

                var size = SizeofResource(hModule, res);
                if (size == 0) return false;

                var hResData = LoadResource(hModule, res);
                if (hResData == IntPtr.Zero) return false;

                var p = LockResource(hResData);
                if (p == IntPtr.Zero) return false;

                var bytes = new byte[size];
                Marshal.Copy(p, bytes, 0, (int)size);

                string xml;
                try { xml = System.Text.Encoding.UTF8.GetString(bytes); }
                catch { xml = System.Text.Encoding.Unicode.GetString(bytes); }

                // Парсим xml
                try
                {
                    var doc = XDocument.Parse(xml);
                    var rel = doc.Descendants().FirstOrDefault(x => x.Name.LocalName == "requestedExecutionLevel");
                    var level = rel?.Attribute("level")?.Value?.ToLowerInvariant() ?? string.Empty;
                    if (string.IsNullOrEmpty(level)) return false;
                    // считаем, что asInvoker = не требует повышения, все остальное — требует/может требовать
                    return level != "asinvoker";
                }
                catch
                {
                    return false;
                }
            }
            finally
            {
                if (hModule != IntPtr.Zero) FreeLibrary(hModule);
            }
        }

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern IntPtr LoadLibraryExW(string lpFileName, IntPtr hFile, uint dwFlags);

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern IntPtr FindResourceW(IntPtr hModule, IntPtr lpName, IntPtr lpType);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern IntPtr LoadResource(IntPtr hModule, IntPtr hResInfo);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern IntPtr LockResource(IntPtr hResData);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern uint SizeofResource(IntPtr hModule, IntPtr hResInfo);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool FreeLibrary(IntPtr hModule);


        // Копирование выделенных логов в буфер обмена
        private void CopySelectedLogsToClipboard()
        {
            try
            {
                var selected = LogsListView.SelectedItems;
                if (selected == null || selected.Count == 0)
                    return;

                var sb = new StringBuilder();
                // Заголовок (опционально)
                sb.AppendLine("Timestamp	Type	Message");
                foreach (var o in selected)
                {
                    if (o is LogEntry le)
                    {
                        // Заменяем переводы строк внутри сообщения на пробелы, чтобы таблица осталась в одной строке
                        var msg = le.Message?.ReplaceLineEndings(" ") ?? string.Empty;
                        sb.AppendLine($"{le.FormattedTimestamp}	{le.Type}	{msg}");
                    }
                }

                var dp = new DataPackage();
                dp.SetText(sb.ToString());
                Clipboard.SetContent(dp);
                Clipboard.Flush();

                StatusText.Text = $"Скопировано {selected.Count} строк";
            }
            catch (Exception ex)
            {
                StatusText.Text = "Ошибка копирования: " + ex.Message;
            }
        }

        private void CopySelectedMessagesToClipboard()
        {
            try
            {
                var selected = LogsListView.SelectedItems;
                if (selected == null || selected.Count == 0)
                    return;

                var sb = new StringBuilder();
                foreach (var o in selected)
                {
                    if (o is LogEntry le)
                    {
                        sb.AppendLine(le.Message ?? string.Empty);
                    }
                }

                var dp = new DataPackage();
                dp.SetText(sb.ToString());
                Clipboard.SetContent(dp);
                Clipboard.Flush();

                StatusText.Text = $"Скопировано {selected.Count} сообщений";
            }
            catch (Exception ex)
            {
                StatusText.Text = "Ошибка копирования: " + ex.Message;
            }
        }

        private void LogsListView_KeyDown(object sender, Microsoft.UI.Xaml.Input.KeyRoutedEventArgs e)
        {
            try
            {
                if (e.Key == VirtualKey.C)
                {
                    var state = Window.Current.CoreWindow.GetKeyState(VirtualKey.Control);
                    if ((state & CoreVirtualKeyStates.Down) == CoreVirtualKeyStates.Down)
                    {
                        CopySelectedLogsToClipboard();
                        e.Handled = true;
                    }
                }
            }
            catch { }
        }

        private void CopyMenuFlyoutItem_Click(object sender, RoutedEventArgs e)
        {
            CopySelectedLogsToClipboard();
        }

        private void CopyMessageMenuFlyoutItem_Click(object sender, RoutedEventArgs e)
        {
            CopySelectedMessagesToClipboard();
        }



        private void Stop_Click(object sender, RoutedEventArgs e)
        {
            _monitorService?.Stop();
            _monitorService = null;

            StatusText.Text = "Остановлено";

            // Разблокируем элементы управления
            ExePathTextBox.IsEnabled = true;
            BrowseButton.IsEnabled = true;
            StartButton.IsEnabled = true;
            StopButton.IsEnabled = false;
        }
    }
}
