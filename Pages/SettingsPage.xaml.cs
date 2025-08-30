using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;
using Microsoft.UI.Xaml.Data;
using Microsoft.UI.Xaml.Input;
using Microsoft.UI.Xaml.Media;
using Microsoft.UI.Xaml.Navigation;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices.WindowsRuntime;
using Windows.Foundation;
using Windows.Foundation.Collections;
using Windows.Storage;
using YoHelper.Utilities;
using YoHelper.Models;

// To learn more about WinUI, the WinUI project structure,
// and more about our project templates, see: http://aka.ms/winui-project-info.

namespace YoHelper.Pages
{
    /// <summary>
    /// An empty page that can be used on its own or navigated to within a Frame.
    /// </summary>
    public sealed partial class SettingsPage : Page
    {
        readonly List<LanguageItem> _languages = new()
        {
            new LanguageItem("", "Использовать системный"),
            new LanguageItem("en-US", "English"),
            new LanguageItem("ru", "Русский")
            // добавляй другие языки тут
        };

        public SettingsPage()
        {
            this.InitializeComponent();
            Loaded += SettingsPage_Loaded;
        }

        private void SettingsPage_Loaded(object sender, RoutedEventArgs e)
        {
            // привязываем список языков
            //LanguageCombo.ItemsSource = _languages;

            // выставляем текущую выбранную тему (как было)
            switch (App.Settings.Theme)
            {
                case "Light": ThemeRadio.SelectedIndex = 1; break;
                case "Dark": ThemeRadio.SelectedIndex = 2; break;
                default: ThemeRadio.SelectedIndex = 0; break;
            }

            // выставляем выбранный язык по коду — SelectedValue ожидает значение Code
            var currentCode = App.Settings.Language ?? "";
        }

        private void ThemeRadio_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            var chosen = ThemeRadio.SelectedIndex switch
            {
                1 => "Light",
                2 => "Dark",
                _ => "Default"
            };

            App.Settings.Theme = chosen;
            SettingsService.Save(App.Settings);

            if (App.MainWindow?.Content is FrameworkElement root)
            {
                root.RequestedTheme = chosen switch
                {
                    "Light" => ElementTheme.Light,
                    "Dark" => ElementTheme.Dark,
                    _ => ElementTheme.Default
                };
            }
        }

        //private void LanguageCombo_SelectionChanged(object sender, SelectionChangedEventArgs e)
        //{
        //    // Получаем код выбранного языка напрямую через SelectedValue
        //    //var code = LanguageCombo.SelectedValue as string ?? "";

        //    // если язык не изменился — выходим
        //    if ((App.Settings.Language ?? "") == code) return;

        //    App.Settings.Language = code;
        //    SettingsService.Save(App.Settings);

        //    try
        //    {
        //        if (string.IsNullOrEmpty(code))
        //            Windows.Globalization.ApplicationLanguages.PrimaryLanguageOverride = "";
        //        else
        //            Windows.Globalization.ApplicationLanguages.PrimaryLanguageOverride = code;
        //    }
        //    catch
        //    {
        //        // игнорируем ошибки установки
        //    }

        //    // Перезапуск приложения (как и раньше) — чтобы новые ресурсы подхватились
        //    var exePath = Environment.ProcessPath ?? Process.GetCurrentProcess().MainModule?.FileName
        //                  ?? System.Reflection.Assembly.GetEntryAssembly()?.Location;

        //    try
        //    {
        //        if (!string.IsNullOrEmpty(exePath))
        //        {
        //            var psi = new ProcessStartInfo
        //            {
        //                FileName = exePath,
        //                UseShellExecute = true
        //            };
        //            Process.Start(psi);
        //        }
        //    }
        //    catch
        //    {
        //        // ignore
        //    }

        //    Environment.Exit(0);
        //}
    }
}
