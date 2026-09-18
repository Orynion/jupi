using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Threading;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.Wpf;
using JupiHome.Models;

namespace JupiHome.Services
{
    public class MusicPlayerService
    {
        private readonly Logger _logger;
        private readonly string _htmlFolder;
        private WebView2? _webView;
        private List<MusicTrack> _playlist = new List<MusicTrack>();
        private int _currentIndex = -1;
        private bool _isConfigured;

        public MusicTrack? CurrentTrack => (_currentIndex >= 0 && _currentIndex < _playlist.Count) ? _playlist[_currentIndex] : null;
        public bool IsPlaying { get; private set; }
        public bool IsPaused { get; private set; }

        public event EventHandler? TrackChanged;
        public event EventHandler? PlaybackStateChanged;
        public event EventHandler<string>? PlaybackFailed;

        public MusicPlayerService(Logger logger)
        {
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
            _htmlFolder = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "wwwroot");
        }

        public void AttachWebView(WebView2 webView)
        {
            if (_webView?.CoreWebView2 != null && _isConfigured)
            {
                try
                {
                    _webView.CoreWebView2.WebMessageReceived -= OnWebMessageReceived;
                }
                catch
                {
                    // Ignore cleanup errors on previous instance
                }
            }
            _webView = webView;
            _isConfigured = false;
        }

        public async Task SetPlaylistAsync(List<MusicTrack> tracks, int startIndex = 0)
        {
            _playlist = tracks ?? new List<MusicTrack>();
            _currentIndex = (startIndex >= 0 && startIndex < _playlist.Count) ? startIndex : 0;
            await PlayCurrentTrackAsync();
        }

        private void EnsurePlayerHtmlExists()
        {
            try
            {
                if (!Directory.Exists(_htmlFolder))
                {
                    Directory.CreateDirectory(_htmlFolder);
                }

                var filePath = Path.Combine(_htmlFolder, "player.html");
                var htmlContent = @"<!DOCTYPE html>
<html>
<head>
    <meta charset=""utf-8"">
    <meta name=""viewport"" content=""width=device-width, initial-scale=1.0"">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html, body { width: 100%; height: 100%; overflow: hidden; background: #000; }
        #player-wrapper { width: 100%; height: 100%; }
        #player-container, iframe { width: 100% !important; height: 100% !important; border: 0; display: block; }
    </style>
</head>
<body>
    <div id=""player-wrapper"">
        <div id=""player-container""></div>
    </div>
    <script src=""https://www.youtube.com/iframe_api""></script>
    <script>
        const params = new URLSearchParams(window.location.search);
        let currentVideoId = params.get('v') || '';
        let player = null;
        let isApiReady = false;
        let retryCount = 0;

        function notifyNative(msg) {
            try {
                if (window.chrome && window.chrome.webview) {
                    window.chrome.webview.postMessage(msg);
                }
            } catch (e) {
                console.warn('postMessage error:', e);
            }
        }

        window.onYouTubeIframeAPIReady = function() {
            isApiReady = true;
            if (currentVideoId) {
                initPlayer(currentVideoId);
            }
        };

        function initPlayer(videoId) {
            currentVideoId = videoId;
            if (player && typeof player.destroy === 'function') {
                try { player.destroy(); } catch (e) {}
                player = null;
            }
            const wrapper = document.getElementById('player-wrapper');
            if (wrapper) {
                wrapper.innerHTML = '<div id=""player-container""></div>';
            }
            player = new YT.Player('player-container', {
                width: '100%',
                height: '100%',
                videoId: videoId,
                playerVars: {
                    autoplay: 1,
                    playsinline: 1,
                    rel: 0,
                    controls: 1,
                    enablejsapi: 1,
                    origin: 'https://jupi.local'
                },
                events: {
                    'onReady': onPlayerReady,
                    'onStateChange': onPlayerStateChange,
                    'onError': onPlayerError
                }
            });
        }

        function onPlayerReady(event) {
            notifyNative({ type: 'ready' });
            event.target.playVideo();
        }

        function onPlayerStateChange(event) {
            if (event.data === YT.PlayerState.ENDED) {
                notifyNative({ type: 'ended' });
            } else if (event.data === YT.PlayerState.PLAYING) {
                notifyNative({ type: 'playing' });
            } else if (event.data === YT.PlayerState.PAUSED) {
                notifyNative({ type: 'paused' });
            } else if (event.data === YT.PlayerState.BUFFERING) {
                notifyNative({ type: 'buffering' });
            }
        }

        function onPlayerError(event) {
            var code = event.data;
            // Transient errors (153 client identification, 2 invalid param, 5 HTML5 player
            // error) are often fixed by re-creating the player once. Permanent embed
            // restrictions (100/101/150) are reported to the host so it can skip the track.
            if ((code === 153 || code === 2 || code === 5) && retryCount < 1) {
                retryCount++;
                notifyNative({ type: 'retrying', code: code });
                setTimeout(function () { initPlayer(currentVideoId); }, 1500);
                return;
            }
            notifyNative({ type: 'error', code: code });
        }

        window.loadTrack = function(videoId) {
            currentVideoId = videoId;
            retryCount = 0;
            if (player && typeof player.loadVideoById === 'function') {
                player.loadVideoById(videoId);
            } else if (isApiReady) {
                initPlayer(videoId);
            } else {
                window.location.search = '?v=' + encodeURIComponent(videoId);
            }
        };

        window.playTrack = function() {
            if (player && typeof player.playVideo === 'function') {
                player.playVideo();
            }
        };

        window.pauseTrack = function() {
            if (player && typeof player.pauseVideo === 'function') {
                player.pauseVideo();
            }
        };

        window.stopTrack = function() {
            if (player && typeof player.stopVideo === 'function') {
                player.stopVideo();
            }
        };
    </script>
</body>
</html>";
                File.WriteAllText(filePath, htmlContent);
            }
            catch (Exception ex)
            {
                _logger.LogError("Failed to write player.html", ex);
            }
        }

        public async Task PlayCurrentTrackAsync()
        {
            var track = CurrentTrack;
            if (track == null) return;

            IsPlaying = true;
            IsPaused = false;
            _logger.Log($"Playing track: {track.Title} ({track.VideoId})");

            TrackChanged?.Invoke(this, EventArgs.Empty);
            PlaybackStateChanged?.Invoke(this, EventArgs.Empty);

            if (_webView == null)
            {
                _logger.LogError("WebView2 player is not attached; playback unavailable");
                PlaybackFailed?.Invoke(this, "Playback unavailable: the video player is not initialized.");
                return;
            }

            try
            {
                await EnsureWebViewReadyAsync();
                if (_webView.CoreWebView2 == null)
                {
                    throw new InvalidOperationException("WebView2 did not finish initializing.");
                }

                var currentUri = _webView.Source?.ToString() ?? string.Empty;
                if (currentUri.StartsWith("https://jupi.local/player.html", StringComparison.OrdinalIgnoreCase))
                {
                    await _webView.ExecuteScriptAsync($"window.loadTrack?.('{Uri.EscapeDataString(track.VideoId)}');");
                }
                else
                {
                    _webView.CoreWebView2.Navigate($"https://jupi.local/player.html?v={Uri.EscapeDataString(track.VideoId)}");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError("Failed to initialize or navigate WebView2 for playback", ex);
                PlaybackFailed?.Invoke(this,
                    "Playback failed: the Microsoft Edge WebView2 runtime may be missing or failed to initialize. " +
                    "Please install it from https://developer.microsoft.com/microsoft-edge/webview2/ and restart Jupi Home.");
            }
        }

        public async Task PauseAsync()
        {
            if (!IsPlaying || IsPaused) return;

            IsPaused = true;
            _logger.Log("Pausing playback");
            PlaybackStateChanged?.Invoke(this, EventArgs.Empty);

            if (_webView == null) return;

            try
            {
                await EnsureWebViewReadyAsync();
                if (_webView.CoreWebView2 != null)
                {
                    await _webView.ExecuteScriptAsync("window.pauseTrack?.();");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError("Failed to pause video in WebView2", ex);
            }
        }

        public async Task ResumeAsync()
        {
            if (!IsPaused && IsPlaying) return;

            IsPlaying = true;
            IsPaused = false;
            _logger.Log("Resuming playback");
            PlaybackStateChanged?.Invoke(this, EventArgs.Empty);

            if (_webView == null) return;

            try
            {
                await EnsureWebViewReadyAsync();
                if (_webView.CoreWebView2 != null)
                {
                    await _webView.ExecuteScriptAsync("window.playTrack?.();");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError("Failed to resume video in WebView2", ex);
            }
        }

        public async Task StopAsync()
        {
            IsPlaying = false;
            IsPaused = false;
            _logger.Log("Stopping playback");
            PlaybackStateChanged?.Invoke(this, EventArgs.Empty);

            if (_webView == null) return;

            try
            {
                await EnsureWebViewReadyAsync();
                if (_webView.CoreWebView2 != null)
                {
                    await _webView.ExecuteScriptAsync("window.stopTrack?.();");
                    _webView.CoreWebView2.Navigate("https://jupi.local/player.html");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError("Failed to stop video in WebView2", ex);
            }
        }

        public async Task SkipAsync()
        {
            if (_playlist.Count == 0) return;

            _currentIndex++;
            if (_currentIndex >= _playlist.Count)
            {
                _currentIndex = 0;
            }

            await PlayCurrentTrackAsync();
        }

        private async Task RemoveCurrentAndSkipAsync()
        {
            if (_playlist.Count == 0) return;

            var failedTrack = CurrentTrack;
            if (_currentIndex >= 0 && _currentIndex < _playlist.Count)
            {
                _logger.Log($"Removing unplayable track at index {_currentIndex}: {failedTrack?.Title}");
                _playlist.RemoveAt(_currentIndex);
            }

            if (_playlist.Count == 0)
            {
                IsPlaying = false;
                IsPaused = false;
                _currentIndex = -1;
                TrackChanged?.Invoke(this, EventArgs.Empty);
                PlaybackStateChanged?.Invoke(this, EventArgs.Empty);
                return;
            }

            if (_currentIndex >= _playlist.Count)
            {
                _currentIndex = 0;
            }

            await PlayCurrentTrackAsync();
        }

        private async Task EnsureWebViewReadyAsync()
        {
            if (_webView == null) return;

            if (_webView.CoreWebView2 == null)
            {
                try
                {
                    await _webView.EnsureCoreWebView2Async();
                }
                catch (Exception ex)
                {
                    // The music panel may be collapsed so the WebView2 has no HWND yet.
                    // Yield to the dispatcher so the panel can be laid out, then retry.
                    _logger.LogError("WebView2 initialization deferred; retrying after layout", ex);
                    await Dispatcher.Yield(DispatcherPriority.ApplicationIdle);

                    if (_webView.CoreWebView2 == null)
                    {
                        await _webView.EnsureCoreWebView2Async();
                    }
                }
            }

            if (_webView.CoreWebView2 != null && !_isConfigured)
            {
                try
                {
                    EnsurePlayerHtmlExists();

                    _webView.CoreWebView2.SetVirtualHostNameToFolderMapping(
                        "jupi.local",
                        _htmlFolder,
                        CoreWebView2HostResourceAccessKind.Allow);

                    _webView.CoreWebView2.WebMessageReceived += OnWebMessageReceived;

                    _isConfigured = true;
                    _logger.Log("MusicPlayerService WebView2 virtual host and player event handlers configured successfully");
                }
                catch (Exception ex)
                {
                    _logger.LogError("Failed to configure WebView2 virtual host or player events", ex);
                }
            }
        }

        private void OnWebMessageReceived(object? sender, CoreWebView2WebMessageReceivedEventArgs args)
        {
            try
            {
                var json = args.WebMessageAsJson;
                if (string.IsNullOrEmpty(json)) return;

                using var doc = JsonDocument.Parse(json);
                if (!doc.RootElement.TryGetProperty("type", out var typeProp)) return;

                var type = typeProp.GetString();
                _logger.Log($"YouTube Player event received: {type}");

                var dispatcher = Application.Current?.Dispatcher ?? Dispatcher.CurrentDispatcher;
                dispatcher.InvokeAsync(async () =>
                {
                    switch (type)
                    {
                        case "ended":
                            _logger.Log("YouTube track ended; skipping to next track");
                            await SkipAsync();
                            break;

                        case "playing":
                            if (!IsPlaying || IsPaused)
                            {
                                IsPlaying = true;
                                IsPaused = false;
                                PlaybackStateChanged?.Invoke(this, EventArgs.Empty);
                            }
                            break;

                        case "paused":
                            if (!IsPaused)
                            {
                                IsPaused = true;
                                PlaybackStateChanged?.Invoke(this, EventArgs.Empty);
                            }
                            break;

                        case "error":
                            int errorCode = doc.RootElement.TryGetProperty("code", out var codeProp) ? codeProp.GetInt32() : -1;
                            _logger.LogError($"YouTube Player error: code {errorCode}");
                            if (errorCode == 101 || errorCode == 150)
                            {
                                PlaybackFailed?.Invoke(this, "The video owner restricts embedding on third-party websites. Skipping to next track...");
                                await RemoveCurrentAndSkipAsync();
                            }
                            else if (errorCode == 100)
                            {
                                PlaybackFailed?.Invoke(this, "The video is unavailable or private. Skipping to next track...");
                                await RemoveCurrentAndSkipAsync();
                            }
                            else if (errorCode == 153 || errorCode == 2 || errorCode == 5)
                            {
                                // Transient errors are auto-retried once in player.html; reaching
                                // here means the retry failed too, so move on to the next track.
                                PlaybackFailed?.Invoke(this, $"YouTube player error (code {errorCode}). Skipping to next track...");
                                await RemoveCurrentAndSkipAsync();
                            }
                            break;
                    }
                });
            }
            catch (Exception ex)
            {
                _logger.LogError("Error handling YouTube player WebMessage", ex);
            }
        }
    }
}
