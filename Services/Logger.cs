using System;
using System.IO;
using System.Text;

namespace AIOrIsIt.Services
{
    /// <summary>
    /// Provides logging functionality for the application.
    /// Supports multiple log levels and file-based logging.
    /// </summary>
    public class Logger
    {
        private static Logger _instance;
        private static readonly object _lock = new object();
        private readonly string _logFilePath;
        private readonly object _fileLock = new object();

        public enum LogLevel
        {
            Debug,
            Info,
            Warning,
            Error,
            Critical
        }

        private Logger()
        {
            string logDirectory = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "AIOrIsIt",
                "Logs"
            );

            if (!Directory.Exists(logDirectory))
            {
                Directory.CreateDirectory(logDirectory);
            }

            string timestamp = DateTime.Now.ToString("yyyyMMdd");
            _logFilePath = Path.Combine(logDirectory, $"saturnia_{timestamp}.log");
        }

        /// <summary>
        /// Gets the singleton instance of the Logger.
        /// </summary>
        public static Logger Instance
        {
            get
            {
                if (_instance == null)
                {
                    lock (_lock)
                    {
                        if (_instance == null)
                        {
                            _instance = new Logger();
                        }
                    }
                }
                return _instance;
            }
        }

        /// <summary>
        /// Logs a debug message.
        /// </summary>
        public void Debug(string message)
        {
            Log(LogLevel.Debug, message);
        }

        /// <summary>
        /// Logs an informational message.
        /// </summary>
        public void Info(string message)
        {
            Log(LogLevel.Info, message);
        }

        /// <summary>
        /// Logs a warning message.
        /// </summary>
        public void Warning(string message)
        {
            Log(LogLevel.Warning, message);
        }

        /// <summary>
        /// Logs an error message.
        /// </summary>
        public void Error(string message)
        {
            Log(LogLevel.Error, message);
        }

        /// <summary>
        /// Logs an error message with exception details.
        /// </summary>
        public void Error(string message, Exception ex)
        {
            string fullMessage = $"{message}\nException: {ex.GetType().Name}\nMessage: {ex.Message}\nStackTrace: {ex.StackTrace}";
            Log(LogLevel.Error, fullMessage);
        }

        /// <summary>
        /// Logs a critical error message.
        /// </summary>
        public void Critical(string message)
        {
            Log(LogLevel.Critical, message);
        }

        /// <summary>
        /// Logs a critical error message with exception details.
        /// </summary>
        public void Critical(string message, Exception ex)
        {
            string fullMessage = $"{message}\nException: {ex.GetType().Name}\nMessage: {ex.Message}\nStackTrace: {ex.StackTrace}";
            Log(LogLevel.Critical, fullMessage);
        }

        /// <summary>
        /// Core logging method that writes to file and optionally to console.
        /// </summary>
        private void Log(LogLevel level, string message)
        {
            try
            {
                string timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff");
                string logEntry = $"[{timestamp}] [{level.ToString().ToUpper()}] {message}";

                // Write to console for debugging
#if DEBUG
                Console.WriteLine(logEntry);
#endif

                // Write to file
                lock (_fileLock)
                {
                    File.AppendAllText(_logFilePath, logEntry + Environment.NewLine, Encoding.UTF8);
                }
            }
            catch (Exception ex)
            {
                // If logging fails, write to console as fallback
                Console.WriteLine($"Logger error: {ex.Message}");
            }
        }

        /// <summary>
        /// Gets the current log file path.
        /// </summary>
        public string GetLogFilePath()
        {
            return _logFilePath;
        }

        /// <summary>
        /// Clears old log files older than the specified number of days.
        /// </summary>
        public void CleanOldLogs(int daysToKeep = 7)
        {
            try
            {
                string logDirectory = Path.GetDirectoryName(_logFilePath);
                if (Directory.Exists(logDirectory))
                {
                    var files = Directory.GetFiles(logDirectory, "saturnia_*.log");
                    DateTime cutoffDate = DateTime.Now.AddDays(-daysToKeep);

                    foreach (var file in files)
                    {
                        FileInfo fileInfo = new FileInfo(file);
                        if (fileInfo.CreationTime < cutoffDate)
                        {
                            File.Delete(file);
                            Info($"Deleted old log file: {Path.GetFileName(file)}");
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Error("Failed to clean old logs", ex);
            }
        }
    }
}
