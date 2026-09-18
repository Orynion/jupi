using System;
using System.Collections.Specialized;
using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Animation;
using Microsoft.Web.WebView2.Wpf;
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
        private ConversationSearchService? _searchService;
        private YouTubeSearchService? _youtubeSearchService;
        private MusicPlayerService? _musicPlayerService;
        private MusicPlayerViewModel? _musicPlayerViewModel;
        private AppSettings _settings;
        private ChatViewModel? _chatViewModel;
        private MainViewModel? _viewModel;

        public MainWindow()
        {
            InitializeComponent();
            MusicWebView.CreationProperties = new CoreWebView2CreationProperties
            {
                AdditionalBrowserArguments = "--autoplay-policy=no-user-gesture-required"
            };
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
                _searchService = new ConversationSearchService(_conversationHistoryService, _logger);

                // Music V1: services + view model
                _youtubeSearchService = new YouTubeSearchService(_settings, _logger);
                _musicPlayerService = new MusicPlayerService(_logger);
                _musicPlayerViewModel = new MusicPlayerViewModel(_youtubeSearchService, _musicPlayerService, _logger);

                _musicPlayerService.AttachWebView(MusicWebView);

                // Eagerly initialize WebView2 when the runtime is present. Missing runtime
                // or a collapsed panel is handled gracefully; playback retries lazily.
                try
                {
                    await MusicWebView.EnsureCoreWebView2Async();
                }
                catch (Exception ex)
                {
                    _logger.LogError("WebView2 runtime unavailable; music playback will be unavailable", ex);
                }

                // V0.64: Create workspace ViewModels
                _chatViewModel = new ChatViewModel(_saturniaClient, _logger, _conversationHistoryService, _musicPlayerViewModel);
                var chatsViewModel = new ChatsViewModel(_conversationHistoryService, _logger);
                var searchViewModel = new SearchViewModel(_searchService, _logger);

                // V0.64: Create MainViewModel that coordinates workspaces
                _viewModel = new MainViewModel(_chatViewModel, chatsViewModel, searchViewModel, _musicPlayerViewModel, _logger);
                DataContext = _viewModel;

                await _viewModel.InitializeAsync();
                _chatViewModel.Messages.CollectionChanged += Messages_CollectionChanged;
                _connectionMonitor.ConnectionStatusChanged += OnConnectionStatusChanged;
                _connectionMonitor.Start();

                ScrollToBottom();
                StatusText.Text = "Ready";
                _logger.Log("Jupi Home v0.64 ready");
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
                if (_chatViewModel != null)
                {
                    _chatViewModel.IsConnected = isConnected;
                }
                _logger.Log($"Connection status: {isConnected}");
            });
        }

        private void ScrollToBottom()
        {
            ChatScrollViewer.ScrollToBottom();
        }

        // V0.6: lightweight send-button launch animation.
        // Plays alongside the send command - message sending is never delayed.
        private void SendButton_Click(object sender, RoutedEventArgs e)
        {
            PlaySendLaunchAnimation();
        }

        private void PlaySendLaunchAnimation()
        {
            var half = TimeSpan.FromMilliseconds(120);
            var full = TimeSpan.FromMilliseconds(240);
            var easeOut = new QuadraticEase { EasingMode = EasingMode.EaseOut };
            var easeInOut = new QuadraticEase { EasingMode = EasingMode.EaseInOut };

            // Scale 1 -> 1.1 -> 1
            var scale = new DoubleAnimationUsingKeyFrames();
            scale.KeyFrames.Add(new EasingDoubleKeyFrame(1.1, KeyTime.FromTimeSpan(half)) { EasingFunction = easeOut });
            scale.KeyFrames.Add(new EasingDoubleKeyFrame(1.0, KeyTime.FromTimeSpan(full)) { EasingFunction = easeInOut });
            SendScale.BeginAnimation(ScaleTransform.ScaleXProperty, scale);
            SendScale.BeginAnimation(ScaleTransform.ScaleYProperty, scale);

            // Forward movement 0 -> 10px -> 0
            var move = new DoubleAnimationUsingKeyFrames();
            move.KeyFrames.Add(new EasingDoubleKeyFrame(10, KeyTime.FromTimeSpan(half)) { EasingFunction = easeOut });
            move.KeyFrames.Add(new EasingDoubleKeyFrame(0, KeyTime.FromTimeSpan(full)) { EasingFunction = easeInOut });
            SendTranslate.BeginAnimation(TranslateTransform.XProperty, move);

            // Tiny rotation 0 -> 8 -> 0
            var tilt = new DoubleAnimationUsingKeyFrames();
            tilt.KeyFrames.Add(new EasingDoubleKeyFrame(8, KeyTime.FromTimeSpan(half)) { EasingFunction = easeOut });
            tilt.KeyFrames.Add(new EasingDoubleKeyFrame(0, KeyTime.FromTimeSpan(full)) { EasingFunction = easeInOut });
            SendRotate.BeginAnimation(RotateTransform.AngleProperty, tilt);

            var pulseOpacity = new DoubleAnimation(0.5, 0, TimeSpan.FromMilliseconds(300))
            {
                EasingFunction = easeOut
            };
            var pulseScale = new DoubleAnimation(0.7, 1.45, TimeSpan.FromMilliseconds(300))
            {
                EasingFunction = easeOut
            };
            SendPulse.BeginAnimation(UIElement.OpacityProperty, pulseOpacity);
            SendPulseScale.BeginAnimation(ScaleTransform.ScaleXProperty, pulseScale);
            SendPulseScale.BeginAnimation(ScaleTransform.ScaleYProperty, pulseScale);

            // Air streaks: brief 1 -> 0 fade with a slight left-to-right drift
            AnimateStreak(StreakTop, StreakTopTranslate);
            AnimateStreak(StreakBottom, StreakBottomTranslate);
        }

        private static void AnimateStreak(UIElement streak, TranslateTransform translate)
        {
            var life = TimeSpan.FromMilliseconds(300);
            var fade = new DoubleAnimation(1, 0, life) { EasingFunction = new QuadraticEase { EasingMode = EasingMode.EaseOut } };
            var drift = new DoubleAnimation(-4, 4, life) { EasingFunction = new QuadraticEase { EasingMode = EasingMode.EaseOut } };
            streak.BeginAnimation(UIElement.OpacityProperty, fade);
            translate.BeginAnimation(TranslateTransform.XProperty, drift);
        }

        // V0.63: Light/Dark theme toggle.
        private void ThemeToggleButton_Click(object sender, RoutedEventArgs e)
        {
            var next = ThemeManager.IsDarkMode ? ThemeManager.Light : ThemeManager.Dark;
            ThemeManager.ApplyTheme(next);
            if (ThemeToggleIcon != null)
            {
                ThemeToggleIcon.Text = ThemeManager.IsDarkMode ? "☀️" : "🌙";
            }
        }

        // V0.63: drag-and-drop attachment support.
        private void InputArea_DragOver(object sender, DragEventArgs e)
        {
            e.Effects = e.Data.GetDataPresent(DataFormats.FileDrop) ? DragDropEffects.Copy : DragDropEffects.None;
            e.Handled = true;
        }

        private void InputArea_Drop(object sender, DragEventArgs e)
        {
            if (e.Data.GetDataPresent(DataFormats.FileDrop) &&
                e.Data.GetData(DataFormats.FileDrop) is string[] files &&
                _chatViewModel != null)
            {
                foreach (var path in files)
                {
                    _chatViewModel.AddAttachmentFromPath(path);
                }
                e.Handled = true;
            }
        }

        // V0.63: attach files via file picker.
        private void AttachButton_Click(object sender, RoutedEventArgs e)
        {
            if (_chatViewModel == null)
                return;

            try
            {
                var dialog = new Microsoft.Win32.OpenFileDialog
                {
                    Title = "Attach files",
                    Multiselect = true,
                    CheckFileExists = true
                };

                if (dialog.ShowDialog(this) == true)
                {
                    foreach (var file in dialog.FileNames)
                    {
                        _chatViewModel.AddAttachmentFromPath(file);
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError("Failed to open file attachment dialog", ex);
            }
        }

        // V0.64: Navigation button handlers
        private void NewChatButton_Click(object sender, RoutedEventArgs e)
        {
            if (_chatViewModel != null)
            {
                _ = _chatViewModel.StartNewChatAsync();
            }
        }

        private void SearchResult_Click(object sender, System.Windows.Input.MouseButtonEventArgs e)
        {
            if (sender is FrameworkElement element && element.Tag is Guid conversationId && _viewModel != null)
            {
                _viewModel.SearchViewModel.SelectResultCommand.Execute(new SearchResult { ConversationId = conversationId });
            }
        }

        protected override void OnClosed(EventArgs e)
        {
            _connectionMonitor?.Stop();
            _connectionMonitor?.Dispose();
            _saturniaClient?.Dispose();
            MusicWebView.Dispose();
            _logger.Log("Jupi Home closed");
            base.OnClosed(e);
        }
    }
}