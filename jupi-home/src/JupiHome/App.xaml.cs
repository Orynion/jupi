using System.Windows;
using JupiHome.Configuration;
using JupiHome.Services;

namespace JupiHome
{
    /// <summary>
    /// Application entry point. Loads the persisted theme before the
    /// MainWindow is constructed so DynamicResource lookups resolve.
    /// </summary>
    public partial class App : Application
    {
        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);

            var settings = AppSettings.Load();
            ThemeManager.ApplyTheme(settings.ThemeMode);
        }
    }
}
