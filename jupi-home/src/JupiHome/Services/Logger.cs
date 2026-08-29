using System;
using System.IO;

namespace JupiHome.Services
{
    public class Logger
    {
        private readonly string _logDirectory;
        private readonly string _logFilePath;
        private static readonly object _logLock = new object();

        public Logger()
        {
            _logDirectory = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "logs");
            _logFilePath = Path.Combine(_logDirectory, $"jupihome_{DateTime.Now:yyyy-MM-dd}.log");

            if (!Directory.Exists(_logDirectory))
            {
                Directory.CreateDirectory(_logDirectory);
            }
        }

        public void Log(string message)
        {
            try
            {
                var timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
                var logEntry = $"[{timestamp}] {message}";

                lock (_logLock)
                {
                    File.AppendAllText(_logFilePath, logEntry + Environment.NewLine);
                }

                System.Diagnostics.Debug.WriteLine(logEntry);
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Logging error: {ex.Message}");
            }
        }

        public void LogError(string message, Exception? ex = null)
        {
            var errorMessage = ex != null
                ? $"ERROR: {message} - {ex.Message}"
                : $"ERROR: {message}";
            Log(errorMessage);
        }
    }
}
