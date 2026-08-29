using System;
using System.Threading;
using System.Threading.Tasks;

namespace JupiHome.Services
{
    public class ConnectionMonitor : IDisposable
    {
        private readonly SaturniaClient _client;
        private readonly Logger _logger;
        private readonly TimeSpan _checkInterval;
        private CancellationTokenSource? _cancellationTokenSource;
        private Task? _monitorTask;
        private bool _disposed;

        public bool IsConnected { get; private set; }
        public event EventHandler<bool>? ConnectionStatusChanged;

        public ConnectionMonitor(SaturniaClient client, Logger logger, TimeSpan? checkInterval = null)
        {
            _client = client ?? throw new ArgumentNullException(nameof(client));
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
            _checkInterval = checkInterval ?? TimeSpan.FromSeconds(10);
        }

        public void Start()
        {
            if (_monitorTask != null)
            {
                _logger.Log("Connection monitor already running");
                return;
            }

            _cancellationTokenSource = new CancellationTokenSource();
            _monitorTask = MonitorConnectionAsync(_cancellationTokenSource.Token);
            _logger.Log("Connection monitor started");
        }

        public void Stop()
        {
            if (_cancellationTokenSource != null)
            {
                _cancellationTokenSource.Cancel();
                _cancellationTokenSource = null;
            }

            _monitorTask = null;
            _logger.Log("Connection monitor stopped");
        }

        private async Task MonitorConnectionAsync(CancellationToken cancellationToken)
        {
            while (!cancellationToken.IsCancellationRequested)
            {
                try
                {
                    var connected = await _client.CheckConnectionAsync(cancellationToken);

                    if (connected != IsConnected)
                    {
                        IsConnected = connected;
                        _logger.Log($"Connection status changed: {(connected ? "Connected" : "Disconnected")}");
                        ConnectionStatusChanged?.Invoke(this, connected);
                    }

                    await Task.Delay(_checkInterval, cancellationToken);
                }
                catch (TaskCanceledException)
                {
                    // Normal cancellation, exit gracefully
                    break;
                }
                catch (Exception ex)
                {
                    _logger.LogError("Error in connection monitor", ex);
                    await Task.Delay(_checkInterval, cancellationToken);
                }
            }
        }

        public void Dispose()
        {
            if (_disposed) return;

            Stop();
            _cancellationTokenSource?.Dispose();
            _disposed = true;
        }
    }
}
