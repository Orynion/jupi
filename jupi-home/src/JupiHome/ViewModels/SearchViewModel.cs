using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using System.Windows.Input;
using JupiHome.Services;

namespace JupiHome.ViewModels
{
    /// <summary>
    /// ViewModel for the Search workspace - allows searching across all conversations
    /// </summary>
    public class SearchViewModel : INotifyPropertyChanged
    {
        private readonly ConversationSearchService _searchService;
        private readonly Logger _logger;

        private string _searchQuery = string.Empty;
        private bool _isSearching;
        private string _statusMessage = "Enter a search term to find conversations";

        public event PropertyChangedEventHandler? PropertyChanged;
        public event EventHandler<Guid>? ConversationSelected;

        public ObservableCollection<SearchResult> Results { get; }

        public ICommand SearchCommand { get; }
        public ICommand ClearCommand { get; }
        public ICommand SelectResultCommand { get; }

        public SearchViewModel(ConversationSearchService searchService, Logger logger)
        {
            _searchService = searchService ?? throw new ArgumentNullException(nameof(searchService));
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));

            Results = new ObservableCollection<SearchResult>();

            SearchCommand = new RelayCommand(async () => await ExecuteSearchAsync(), () => !IsSearching && !string.IsNullOrWhiteSpace(SearchQuery));
            ClearCommand = new RelayCommand(ExecuteClear);
            SelectResultCommand = new RelayCommand<SearchResult>(SelectResult);
        }

        public string SearchQuery
        {
            get => _searchQuery;
            set
            {
                if (_searchQuery != value)
                {
                    _searchQuery = value;
                    OnPropertyChanged();
                    ((RelayCommand)SearchCommand).RaiseCanExecuteChanged();
                }
            }
        }

        public bool IsSearching
        {
            get => _isSearching;
            set
            {
                if (_isSearching != value)
                {
                    _isSearching = value;
                    OnPropertyChanged();
                    ((RelayCommand)SearchCommand).RaiseCanExecuteChanged();
                }
            }
        }

        public string StatusMessage
        {
            get => _statusMessage;
            set
            {
                if (_statusMessage != value)
                {
                    _statusMessage = value;
                    OnPropertyChanged();
                }
            }
        }

        public bool HasResults => Results.Count > 0;

        private async Task ExecuteSearchAsync()
        {
            if (string.IsNullOrWhiteSpace(SearchQuery))
                return;

            IsSearching = true;
            StatusMessage = $"Searching for '{SearchQuery}'...";

            try
            {
                var results = await _searchService.SearchAsync(SearchQuery);

                Results.Clear();
                foreach (var result in results)
                {
                    Results.Add(result);
                }

                StatusMessage = results.Count > 0
                    ? $"Found {results.Count} conversation(s)"
                    : "No conversations found";

                OnPropertyChanged(nameof(HasResults));
                _logger.Log($"Search completed: {results.Count} results for '{SearchQuery}'");
            }
            catch (Exception ex)
            {
                StatusMessage = "Search failed. Please try again.";
                _logger.LogError($"Search error for '{SearchQuery}'", ex);
            }
            finally
            {
                IsSearching = false;
            }
        }

        private void ExecuteClear()
        {
            SearchQuery = string.Empty;
            Results.Clear();
            StatusMessage = "Enter a search term to find conversations";
            OnPropertyChanged(nameof(HasResults));
            _logger.Log("Search cleared");
        }

        private void SelectResult(SearchResult? result)
        {
            if (result != null)
            {
                _logger.Log($"Opening conversation from search: {result.Title}");
                ConversationSelected?.Invoke(this, result.ConversationId);
            }
        }

        protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }
}
