// ThemeSelectorService.cs
using Microsoft.UI.Xaml;
using Windows.Storage;

namespace YoHelper.Utilities
{
    public static class ThemeSelectorService
    {
        const string Key = "AppTheme"; // "Default"|"Light"|"Dark"

        public static void Initialize()
        {
            var val = ApplicationData.Current.LocalSettings.Values[Key] as string ?? "Default";

            // Если вы хотите применить глобально до отображения UI:
            if (val == "Light")
            {
                Application.Current.RequestedTheme = ApplicationTheme.Light; // ТОЛЬКО при старте до Activate
            }
            else if (val == "Dark")
            {
                Application.Current.RequestedTheme = ApplicationTheme.Dark; // ТОЛЬКО при старте до Activate
            }
            // else — оставить системную (по умолчанию)

            // Также можно применить к уже созданному корневому элементу:
            if (App.MainWindow?.Content is FrameworkElement root)
            {
                root.RequestedTheme = val switch
                {
                    "Light" => ElementTheme.Light,
                    "Dark" => ElementTheme.Dark,
                    _ => ElementTheme.Default
                };
            }
        }
    }

}
