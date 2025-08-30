using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices.WindowsRuntime;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;
using Microsoft.UI.Xaml.Data;
using Microsoft.UI.Xaml.Input;
using Microsoft.UI.Xaml.Media;
using Microsoft.UI.Xaml.Navigation;
using Microsoft.UI.Xaml.Shapes;
using Windows.ApplicationModel;
using Windows.ApplicationModel.Activation;
using Windows.Foundation;
using Windows.Foundation.Collections;
using YoHelper.Models;
using YoHelper.Utilities;

// To learn more about WinUI, the WinUI project structure,
// and more about our project templates, see: http://aka.ms/winui-project-info.

namespace YoHelper
{
    /// <summary>
    /// Provides application-specific behavior to supplement the default Application class.
    /// </summary>
    public partial class App : Application
    {
        public static Window? MainWindow { get; private set; }
        public static AppSettings Settings { get; private set; } = new AppSettings();

        /// <summary>
        /// Initializes the singleton application object.  This is the first line of authored code
        /// executed, and as such is the logical equivalent of main() or WinMain().
        /// </summary>
        public App()
        {
            // Загружаем настройки прямо при старте (unpackaged — просто файл)
            Settings = SettingsService.Load();

            // Если пользователь выбрал язык — применяем PrimaryLanguageOverride до создания UI,
            // чтобы ресурсы загрузились сразу.
            if (!string.IsNullOrEmpty(Settings.Language))
            {
                try
                {
                    Windows.Globalization.ApplicationLanguages.PrimaryLanguageOverride = Settings.Language;
                }
                catch
                {
                    // игнорируем, если по какой-то причине не удалось
                }
            }

            InitializeComponent();
        }

        /// <summary>
        /// Invoked when the application is launched.
        /// </summary>
        /// <param name="args">Details about the launch request and process.</param>
        protected override void OnLaunched(Microsoft.UI.Xaml.LaunchActivatedEventArgs args)
        {
            MainWindow = new MainWindow();

            // Применяем тему к корневому элементу, когда Content создан
            // Предполагаем, что в MainWindow.Content есть FrameworkElement (Grid/Root)
            if (MainWindow.Content is FrameworkElement root)
            {
                root.RequestedTheme = Settings.Theme switch
                {
                    "Light" => ElementTheme.Light,
                    "Dark" => ElementTheme.Dark,
                    _ => ElementTheme.Default
                };
            }

            MainWindow.Activate();
        }
    }
}
