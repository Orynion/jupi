using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using System.Windows.Input;
using JupiHome.Models;
using JupiHome.Services;

namespace JupiHome.ViewModels
{
    /// <summary>
    /// ViewModel for the Chats workspace - proper conversation browser
    /// </summary>
    public class ChatsViewModel : INotifyPropertyChanged
    {
        private readonly ConversationHistoryService _historyService;
        private readonly Logger _logger;
        private ConversationSummary? _selectedConversation;
        private bool _isLoading;

        public event PropertyChangedEventHandler? PropertyChanged;
        public event EventHandler<Guid>? ConversationSelected;
        public event EventHandler? NewChatRequested;

        public ObservableCollection<ConversationSummary> Conversations { get; }

        public ICommand NewChatCommand { get; }
        public ICommand SelectConversationCommand { get; }
        public ICommand RefreshCommand { get; }
        public ICommand DeleteConversationCommand { get; }

        public ChatsViewModel(ConversationHistoryService historyService, Logger logger)
        {
            _historyService = historyService ?? throw new ArgumentNullException(nameof(historyService));
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));

            Conversations = new ObservableCollection<ConversationSummary>();

            NewChatCommand = new RelayCommand(ExecuteNewChat);
            SelectConversationCommand = new RelayCommand<ConversationSummary>(SelectConversation);
            RefreshCommand = new RelayCommand(async () => await RefreshConversationsAsync());
            DeleteConversationCommand = new RelayCommand<ConversationSummary>(async (conv) => await DeleteConversationAsync(conv));
        }

        public ConversationSummary? SelectedConversation
        {
            get => _selectedConversation;
            set
            {
                if (_selectedConversation != value)
                {
                    _selectedConversation = value;
                    OnPropertyChanged();
                }
            }
        }

        public bool IsLoading
        {
            get => _isLoading;
            set
            {
                if (_isLoading != value)
                {
                    _isLoading = value;
                    OnPropertyChanged();
                }
            }
        }

        public bool HasConversations => Conversations.Count > 0;

        public async Task RefreshConversationsAsync()
        {
            IsLoading = true;

            try
            {
                var summaries = await _historyService.LoadAllConversationsAsync();
                Conversations.Clear();

                foreach (var summary in summaries)
                {
                    Conversations.Add(summary);
                }

                OnPropertyChanged(nameof(HasConversations));
                _logger.Log($"Loaded {Conversations.Count} conversations");
            }
            catch (Exception ex)
            {
                _logger.LogError("Failed to refresh conversations", ex);
            }
            finally
            {
                IsLoading = false;
            }
        }

        private void ExecuteNewChat()
        {
            _logger.Log("New chat requested from Chats workspace");
            NewChatRequested?.Invoke(this, EventArgs.Empty);
        }

        private void SelectConversation(ConversationSummary? conversation)
        {
            if (conversation != null)
            {
                SelectedConversation = conversation;
                _logger.Log($"Conversation selected: {conversation.Title}");
                ConversationSelected?.Invoke(this, conversation.Id);
            }
        }

        private async Task DeleteConversationAsync(ConversationSummary? conversation)
        {
            if (conversation == null)
                return;

            try
            {
                await _historyService.DeleteConversationAsync(conversation.Id);
                Conversations.Remove(conversation);
                OnPropertyChanged(nameof(HasConversations));
                _logger.Log($"Deleted conversation: {conversation.Title}");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Failed to delete conversation {conversation.Id}", ex);
            }
        }

        protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }
}
