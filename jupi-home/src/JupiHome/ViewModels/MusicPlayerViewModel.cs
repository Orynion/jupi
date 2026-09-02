using System;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using System.Windows.Input;
using JupiHome.Models;
using JupiHome.Services;

namespace JupiHome.ViewModels
{
    public class MusicPlayerViewModel : INotifyPropertyChanged
    {
        private readonly YouTubeSearchService _searchService;
        private readonly MusicPlayerService _playerService;
        private readonly Logger _logger;

        private MusicTrack? _currentTrack;
        private bool _isPlaying;
        private bool _isPaused;
        private bool _isPanelVisible;
        private string _statusText = "Ready";
        private string? _errorMessage;

        public event PropertyChangedEventHandler? PropertyChanged;

        public MusicTrack? CurrentTrack
        {
            get => _currentTrack;
            set { if (_currentTrack != value) { _currentTrack = value; OnPropChanged(); OnPropChanged(nameof(HasTrack)); OnPropChanged(nameof(TrackTitle)); OnPropChanged(nameof(ChannelTitle)); } }
        }

        public bool HasTrack => CurrentTrack != null;
        public string TrackTitle => CurrentTrack?.Title ?? "No track playing";
        public string ChannelTitle => CurrentTrack?.ChannelTitle ?? string.Empty;

        public bool IsPlaying
        {
            get => _isPlaying;
            set { if (_isPlaying != value) { _isPlaying = value; OnPropChanged(); OnPropChanged(nameof(PlayPauseButtonText)); } }
        }

        public bool IsPaused
        {
            get => _isPaused;
            set { if (_isPaused != value) { _isPaused = value; OnPropChanged(); OnPropChanged(nameof(PlayPauseButtonText)); } }
        }

        public bool IsPanelVisible
        {
            get => _isPanelVisible;
            set { if (_isPanelVisible != value) { _isPanelVisible = value; OnPropChanged(); } }
        }

        public string StatusText
        {
            get => _statusText;
            set { if (_statusText != value) { _statusText = value; OnPropChanged(); } }
        }

        public string? ErrorMessage
        {
            get => _errorMessage;
            set { if (_errorMessage != value) { _errorMessage = value; OnPropChanged(); OnPropChanged(nameof(HasError)); } }
        }

        public bool HasError => !string.IsNullOrEmpty(ErrorMessage);
        public string PlayPauseButtonText => (IsPlaying && !IsPaused) ? "⏸ Pause" : "▶ Play";

        public ICommand TogglePlayPauseCommand { get; }
        public ICommand StopCommand { get; }
        public ICommand SkipCommand { get; }
        public MusicPlayerService PlayerService => _playerService;

        public MusicPlayerViewModel(YouTubeSearchService searchService, MusicPlayerService playerService, Logger logger)
        {
            _searchService = searchService ?? throw new ArgumentNullException(nameof(searchService));
            _playerService = playerService ?? throw new ArgumentNullException(nameof(playerService));
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));

            _playerService.TrackChanged += (s, e) => {
                CurrentTrack = _playerService.CurrentTrack;
                if (CurrentTrack != null) { IsPanelVisible = true; StatusText = $"Playing: {CurrentTrack.Title}"; ErrorMessage = null; }
            };
            _playerService.PlaybackStateChanged += (s, e) => {
                IsPlaying = _playerService.IsPlaying;
                IsPaused = _playerService.IsPaused;
                StatusText = IsPaused ? "Paused" : (IsPlaying && CurrentTrack != null) ? $"Playing: {CurrentTrack.Title}" : "Stopped";
            };
            _playerService.PlaybackFailed += (s, message) => {
                ErrorMessage = message;
                StatusText = "Playback failed";
            };

            TogglePlayPauseCommand = new RelayCommand(async () => await TogglePlayPauseAsync());
            StopCommand = new RelayCommand(async () => await StopAsync());
            SkipCommand = new RelayCommand(async () => await SkipAsync());
        }

        public async Task<string> PlayQueryAsync(string query)
        {
            ErrorMessage = null;
            StatusText = $"Searching for '{query}'...";
            var (tracks, error) = await _searchService.SearchTracksAsync(query, false);
            if (!string.IsNullOrEmpty(error) || tracks.Count == 0)
            {
                ErrorMessage = error ?? "No music tracks found.";
                StatusText = "Search failed";
                return ErrorMessage;
            }
            IsPanelVisible = true;
            await _playerService.SetPlaylistAsync(tracks, 0);
            return HasError ? ErrorMessage! : $"🎵 Playing: {tracks[0].Title}";
        }

        public async Task<string> PlayRandomAsync()
        {
            ErrorMessage = null;
            StatusText = "Searching for random music...";
            var (tracks, error) = await _searchService.SearchTracksAsync(string.Empty, true);
            if (!string.IsNullOrEmpty(error) || tracks.Count == 0)
            {
                ErrorMessage = error ?? "No music tracks found.";
                StatusText = "Search failed";
                return ErrorMessage;
            }
            IsPanelVisible = true;
            await _playerService.SetPlaylistAsync(tracks, 0);
            return HasError ? ErrorMessage! : $"🎵 Playing random track: {tracks[0].Title}";
        }

        public async Task TogglePlayPauseAsync()
        {
            if (IsPlaying && !IsPaused) await PauseAsync();
            else if (IsPaused) await ResumeAsync();
            else if (CurrentTrack != null) await _playerService.PlayCurrentTrackAsync();
        }

        public async Task PauseAsync() { await _playerService.PauseAsync(); }
        public async Task ResumeAsync() { await _playerService.ResumeAsync(); }
        public async Task StopAsync() { await _playerService.StopAsync(); StatusText = "Stopped"; }
        public async Task SkipAsync() { await _playerService.SkipAsync(); }

        private void OnPropChanged([CallerMemberName] string? name = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
        }
    }
}
