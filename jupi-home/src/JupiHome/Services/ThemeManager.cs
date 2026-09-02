using System;
using System.Linq;
using System.Windows;
using JupiHome.Configuration;
using JupiHome.Converters;

namespace JupiHome.Services
{
    /// <summary>
    /// Applies the Light or warm Dark theme at runtime by swapping the
    /// active theme ResourceDictionary in Application resources.
    /// Persists the choice through the existing AppSettings mechanism.
    /// </summary>
    public static class ThemeManager
    {
        public const string Light = "light";
        public const string Dark = "dark";

        public static string CurrentTheme { get; private set; } = Light;

        public static bool IsDarkMode => CurrentTheme == Dark;

        public static void ApplyTheme(string mode)
        {
            CurrentTheme = string.Equals(mode, Dark, StringComparison.OrdinalIgnoreCase) ? Dark : Light;

            var dictionaries = Application.Current.Resources.MergedDictionaries;

            var existingLight = dictionaries
                .FirstOrDefault(d => d.Source?.OriginalString?.Contains("LightTheme", StringComparison.OrdinalIgnoreCase) == true);
            var existingDark = dictionaries
                .FirstOrDefault(d => d.Source?.OriginalString?.Contains("DarkTheme", StringComparison.OrdinalIgnoreCase) == true);

            if (existingLight != null) dictionaries.Remove(existingLight);
            if (existingDark != null) dictionaries.Remove(existingDark);

            var themeFile = CurrentTheme == Dark ? "DarkTheme.xaml" : "LightTheme.xaml";
            var theme = new ResourceDictionary { Source = new Uri($"Themes/{themeFile}", UriKind.Relative) };
            dictionaries.Add(theme);

            // Future Markdown/code conversions use theme-appropriate colors.
            MarkdownToFlowDocumentConverter.IsDarkMode = IsDarkMode;

            var settings = AppSettings.Load();
            settings.ThemeMode = CurrentTheme;
            settings.Save();
        }
    }
}