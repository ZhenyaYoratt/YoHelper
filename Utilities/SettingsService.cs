using System;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using YoHelper.Models;

namespace YoHelper.Utilities
{
    [JsonSerializable(typeof(AppSettings))]
    [JsonSourceGenerationOptions(PropertyNamingPolicy = JsonKnownNamingPolicy.CamelCase)] // опционально
    internal partial class AppSettingsJsonContext : JsonSerializerContext
    {
    }

    public static class SettingsService
    {
        static readonly string SettingsFilePath =
            Path.Combine(AppContext.BaseDirectory, "settings.json");

        static readonly object _lock = new object();

        // Общие опции с TypeInfoResolver
        static readonly JsonSerializerOptions _options;

        static SettingsService()
        {
            _options = new JsonSerializerOptions
            {
                WriteIndented = true
            };
            // Включаем резолвер типов (разрешает сериализацию без reflection)
            _options.TypeInfoResolver = new DefaultJsonTypeInfoResolver();
        }

        public static AppSettings Load()
        {
            lock (_lock)
            {
                try
                {
                    if (!File.Exists(SettingsFilePath))
                        return new AppSettings();

                    var json = File.ReadAllText(SettingsFilePath);
                    return JsonSerializer.Deserialize<AppSettings>(json, _options) ?? new AppSettings();
                }
                catch
                {
                    return new AppSettings();
                }
            }
        }

        public static void Save(AppSettings settings)
        {
            lock (_lock)
            {
                var json = JsonSerializer.Serialize(settings, _options);
                Directory.CreateDirectory(Path.GetDirectoryName(SettingsFilePath) ?? AppContext.BaseDirectory);
                File.WriteAllText(SettingsFilePath, json);
            }
        }
    }

}
