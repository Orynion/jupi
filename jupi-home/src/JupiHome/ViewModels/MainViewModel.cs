using System;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using System.Windows.Input;
using JupiHome.Models;
using JupiHome.Services;

namespace JupiHome.ViewModels
{
    /// <summary>
    /// Main ViewModel for Jupi Home v0.64 - coordinates all workspaces
    /// </summary>
    public class MainViewModel : INotifyPropertyChanged
    {
        private readonly WorkspaceCoordinator _coordinator;
        private readonly Logger _logger;

        private WorkspaceType _currentWorkspace = WorkspaceType.Chat;

        public event PropertyChangedEventHandler? PropertyChanged;

        // Workspace ViewModels
        public ChatViewModel ChatViewModel { get; }
        public ChatsViewModel ChatsViewModel { get; }
        public SearchViewModel SearchViewModel { get; }
        public MusicPlayerViewModel? MusicViewModel { get; }

        // Navigation Commands
        public ICommand NavigateToChatCommand { get; }
        public ICommand NavigateToChatsCommand { get; }
        public ICommand NavigateToSearchCommand { get; }
        public ICommand NavigateToMusicCommand { get; }
        public ICommand NavigateToSettingsCommand { get; }

        public MainViewModel(
            ChatViewModel chatViewModel,
            ChatsViewModel chatsViewModel,
            SearchViewModel searchViewModel,
            MusicPlayerViewModel? musicViewModel,
            Logger logger)
        {
            ChatViewModel = chatViewModel ?? throw new ArgumentNullException(nameof(chatViewModel));
            ChatsViewModel = chatsViewModel ?? throw new ArgumentNullException(nameof(chatsViewModel));
            SearchViewModel = searchViewModel ?? throw new ArgumentNullException(nameof(searchViewModel));
            MusicViewModel = musicViewModel;
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));

            _coordinator = new WorkspaceCoordinator();

            // Register workspaces
            _coordinator.RegisterWorkspace(WorkspaceType.Chat, ChatViewModel);
            _coordinator.RegisterWorkspace(WorkspaceType.Chats, ChatsViewModel);
            _coordinator.RegisterWorkspace(WorkspaceType.Search, SearchViewModel);
            if (MusicViewModel != null)
            {
                _coordinator.RegisterWorkspace(WorkspaceType.Music, MusicViewModel);
            }

            // Wire up navigation events
            ChatsViewModel.ConversationSelected += OnChatsConversationSelected;
            ChatsViewModel.NewChatRequested += OnNewChatRequested;
            SearchViewModel.ConversationSelected += OnSearchConversationSelected;

            // Navigation commands
            NavigateToChatCommand = new RelayCommand(() => NavigateTo(WorkspaceType.Chat));
            NavigateToChatsCommand = new RelayCommand(() => NavigateTo(WorkspaceType.Chats));
            NavigateToSearchCommand = new RelayCommand(() => NavigateTo(WorkspaceType.Search));
            NavigateToMusicCommand = new RelayCommand(() => NavigateTo(WorkspaceType.Music));
            NavigateToSettingsCommand = new RelayCommand(() => NavigateTo(WorkspaceType.Settings));

            // Subscribe to coordinator navigation
            _coordinator.NavigationRequested += OnNavigationRequested;
        }

        public WorkspaceType CurrentWorkspace
        {
            get => _currentWorkspace;
            private set
            {
                if (_currentWorkspace != value)
                {
                    _currentWorkspace = value;
                    OnPropertyChanged();
                    OnPropertyChanged(nameof(IsChatWorkspace));
                    OnPropertyChanged(nameof(IsChatsWorkspace));
                    OnPropertyChanged(nameof(IsSearchWorkspace));
                    OnPropertyChanged(nameof(IsMusicWorkspace));
                    OnPropertyChanged(nameof(IsSettingsWorkspace));
                }
            }
        }

        // Properties for UI binding
        public bool IsChatWorkspace => CurrentWorkspace == WorkspaceType.Chat;
        public bool IsChatsWorkspace => CurrentWorkspace == WorkspaceType.Chats;
        public bool IsSearchWorkspace => CurrentWorkspace == WorkspaceType.Search;
        public bool IsMusicWorkspace => CurrentWorkspace == WorkspaceType.Music;
        public bool IsSettingsWorkspace => CurrentWorkspace == WorkspaceType.Settings;

        public void NavigateTo(WorkspaceType workspace)
        {
            _logger.Log($"Navigating to {workspace} workspace");

            // Special handling for workspace-specific initialization
            if (workspace == WorkspaceType.Chats)
            {
                _ = ChatsViewModel.RefreshConversationsAsync();
            }

            CurrentWorkspace = workspace;
            _coordinator.NavigateTo(workspace);
        }

        private void OnNavigationRequested(object? sender, WorkspaceNavigationRequest request)
        {
            if (request.ConversationId.HasValue)
            {
                // Navigate to conversation in Chat workspace
                ChatViewModel.NavigateToConversation(request.ConversationId.Value);
            }

            CurrentWorkspace = request.TargetWorkspace;
        }

        private void OnChatsConversationSelected(object? sender, Guid conversationId)
        {
            _logger.Log($"Conversation selected from Chats workspace: {conversationId}");
            ChatViewModel.NavigateToConversation(conversationId);
            NavigateTo(WorkspaceType.Chat);
        }

        private void OnSearchConversationSelected(object? sender, Guid conversationId)
        {
            _logger.Log($"Conversation selected from Search: {conversationId}");
            ChatViewModel.NavigateToConversation(conversationId);
            NavigateTo(WorkspaceType.Chat);
        }

        private void OnNewChatRequested(object? sender, EventArgs e)
        {
            _logger.Log("New chat requested from Chats workspace");
            _ = ChatViewModel.StartNewChatAsync();
            NavigateTo(WorkspaceType.Chat);
        }

        public async Task InitializeAsync()
        {
            // Load initial conversation list for Chats workspace
            await ChatsViewModel.RefreshConversationsAsync();
            _logger.Log("MainViewModel initialized");
        }

        protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }
}
