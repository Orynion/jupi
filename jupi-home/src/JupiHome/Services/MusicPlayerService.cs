using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using System.Windows.Threading;
using Microsoft.Web.WebView2.Wpf;
using JupiHome.Models;

namespace JupiHome.Services
{
    public class MusicPlayerService
    {
        private readonly Logger _logger;
        private WebView2? _webView;
        private List<MusicTrack> _playlist = new List<MusicTrack>();
        private int _currentIndex = -1;

        public MusicTrack? CurrentTrack => (_currentIndex >= 0 && _currentIndex < _playlist.Count) ? _playlist[_currentIndex] : null;
        public bool IsPlaying { get; private set; }
        public bool IsPaused { get; private set; }

        public event EventHandler? TrackChanged;
        public event EventHandler? PlaybackStateChanged;
        public event EventHandler<string>? PlaybackFailed;

        public MusicPlayerService(Logger logger)
        {
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
        }

        public void AttachWebView(WebView2 webView)
        {
            _webView = webView;
        }

        public async Task SetPlaylistAsync(List<MusicTrack> tracks, int startIndex = 0)
        {
            _playlist = tracks ?? new List<MusicTrack>();
            _currentIndex = (startIndex >= 0 && startIndex < _playlist.Count) ? startIndex : 0;
            await PlayCurrentTrackAsync();
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

                var request = _webView.CoreWebView2.Environment.CreateWebResourceRequest(
                    track.EmbedUrl,
                    "GET",
                    null,
                    "Referer: https://www.youtube.com/\r\n");
                _webView.CoreWebView2.NavigateWithWebResourceRequest(request);
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
                    await _webView.ExecuteScriptAsync("document.querySelector('video')?.pause();");
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
                    await _webView.ExecuteScriptAsync("document.querySelector('video')?.play();");
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
                    await _webView.ExecuteScriptAsync("document.querySelector('video')?.pause();");
                    _webView.CoreWebView2.Navigate("about:blank");
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

        private async Task EnsureWebViewReadyAsync()
        {
            if (_webView == null || _webView.CoreWebView2 != null) return;

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
    }
}
