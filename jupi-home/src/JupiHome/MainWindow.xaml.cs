using System;
using System.Collections.Specialized;
using System.Windows;
using JupiHome.Services;
using JupiHome.Configuration;
using JupiHome.ViewModels;

namespace JupiHome
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        private Logger _logger;
        private SaturniaClient? _saturniaClient;
        private ConnectionMonitor? _connectionMonitor;
        private ConversationHistoryService? _conversationHistoryService;
        private AppSettings _settings;
        private ChatViewModel? _viewModel;

        public MainWindow()
        {
            InitializeComponent();
            _logger = new Logger();
            _settings = AppSettings.Load();
            _logger.Log("Jupi Home started");
        }

        private async void Window_Loaded(object sender, RoutedEventArgs e)
        {
            try
            {
                _saturniaClient = new SaturniaClient(_settings.SaturniaBaseUrl, _logger);
                _connectionMonitor = new ConnectionMonitor(_saturniaClient, _logger);
                _conversationHistoryService = new ConversationHistoryService(_logger);

                _viewModel = new ChatViewModel(_saturniaClient, _logger, _conversationHistoryService);
                DataContext = _viewModel;

                await _viewModel.RefreshConversationsListAsync();
                _viewModel.Messages.CollectionChanged += Messages_CollectionChanged;
                _connectionMonitor.ConnectionStatusChanged += OnConnectionStatusChanged;
                _connectionMonitor.Start();

                ScrollToBottom();
                StatusText.Text = "Ready";
                _logger.Log("Jupi Home ready");
            }
            catch (Exception ex)
            {
                _logger.LogError("Error during initialization", ex);
                StatusText.Text = $"Initialization error: {ex.Message}";
            }
        }

        private void Messages_CollectionChanged(object? sender, NotifyCollectionChangedEventArgs e)
        {
            Dispatcher.Invoke(() => ScrollToBottom());
        }

        private void OnConnectionStatusChanged(object? sender, bool isConnected)
        {
            Dispatcher.Invoke(() =>
            {
                if (_viewModel != null)
                {
                    _viewModel.IsConnected = isConnected;
                }
                _logger.Log($"Connection status: {isConnected}");
            });
        }

        private void ScrollToBottom()
        {
            ChatScrollViewer.ScrollToBottom();
        }

        protected override void OnClosed(EventArgs e)
        {
            _connectionMonitor?.Stop();
            _connectionMonitor?.Dispose();
            _saturniaClient?.Dispose();
            _logger.Log("Jupi Home closed");
            base.OnClosed(e);
        }
    }
}
