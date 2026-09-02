using System;
using System.IO;
using System.Text.Json;

namespace JupiHome.Configuration
{
    public class AppSettings
    {
        public string ApplicationName { get; set; } = "JupiHome";
        public string Version { get; set; } = "v0.5";
        public bool EnableLogging { get; set; } = true;
        public string LogPath { get; set; } = "logs";
        public string ThemeMode { get; set; } = "light";
        public bool ShowWelcomeScreen { get; set; } = true;
        public string SaturniaBaseUrl { get; set; } = "http://127.0.0.1:5000";
        public string YouTubeApiKey { get; set; } = string.Empty;

        public static AppSettings Load()
        {
            var settingsPath = GetSettingsFilePath();

            if (!File.Exists(settingsPath))
            {
                return new AppSettings();
            }

            try
            {
                var json = File.ReadAllText(settingsPath);
                return JsonSerializer.Deserialize<AppSettings>(json) ?? new AppSettings();
            }
            catch
            {
                return new AppSettings();
            }
        }

        public void Save()
        {
            var settingsPath = GetSettingsFilePath();
            var directory = Path.GetDirectoryName(settingsPath);

            if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
            {
                Directory.CreateDirectory(directory);
            }

            var json = JsonSerializer.Serialize(this, new JsonSerializerOptions { WriteIndented = true });
            File.WriteAllText(settingsPath, json);
        }

        public static string GetSettingsFilePath()
        {
            var appDataPath = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            var jupiHomePath = Path.Combine(appDataPath, "JupiHome");
            return Path.Combine(jupiHomePath, "appsettings.json");
        }
    }
}
