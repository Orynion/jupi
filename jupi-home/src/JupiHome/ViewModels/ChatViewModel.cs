using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Input;
using JupiHome.Models;
using JupiHome.Services;

namespace JupiHome.ViewModels
{
    public class ChatViewModel : INotifyPropertyChanged
    {
        private readonly SaturniaClient _saturniaClient;
        private readonly Logger _logger;
        private readonly ConversationHistoryService _conversationHistoryService;
        private readonly MusicPlayerViewModel? _musicPlayerViewModel;
        private readonly MusicIntentParser _musicIntentParser = new MusicIntentParser();

        private string _inputText = string.Empty;
        private bool _isSending;
        private string _connectionStatus = "Disconnected";
        private bool _isConnected;
        private Conversation? _currentConversation;
        private ConversationSummary? _selectedConversation;

        public ObservableCollection<ConversationMessage> Messages { get; }
        public ObservableCollection<ConversationSummary> Conversations { get; }

        /// <summary>
        /// Files the user has attached to the next message. The UI shows these
        /// clearly; Saturnia only ever receives their file names as text
        /// references (the backend cannot read file contents today).
        /// </summary>
        public ObservableCollection<FileAttachment> PendingAttachments { get; }

        public bool HasPendingAttachments => PendingAttachments.Count > 0;

        public MusicPlayerViewModel? MusicPlayer => _musicPlayerViewModel;

        public ICommand SendMessageCommand { get; }
        public ICommand NewChatCommand { get; }
        public ICommand CopyMessageCommand { get; }
        public ICommand EditMessageCommand { get; }
        public ICommand RemoveAttachmentCommand { get; }

        public event PropertyChangedEventHandler? PropertyChanged;
        public event EventHandler<Guid>? ConversationSelected;

        public ChatViewModel(SaturniaClient saturniaClient, Logger logger, ConversationHistoryService conversationHistoryService, MusicPlayerViewModel? musicPlayerViewModel = null)
        {
            _saturniaClient = saturniaClient ?? throw new ArgumentNullException(nameof(saturniaClient));
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
            _conversationHistoryService = conversationHistoryService ?? throw new ArgumentNullException(nameof(conversationHistoryService));
            _musicPlayerViewModel = musicPlayerViewModel;

            Messages = new ObservableCollection<ConversationMessage>();
            Conversations = new ObservableCollection<ConversationSummary>();
            PendingAttachments = new ObservableCollection<FileAttachment>();
            PendingAttachments.CollectionChanged += (_, __) => OnPropertyChanged(nameof(HasPendingAttachments));
            Messages.CollectionChanged += (_, __) => OnPropertyChanged(nameof(HasMessages));

            SendMessageCommand = new RelayCommand(async () => await SendMessageAsync(), CanSendMessage);
            NewChatCommand = new RelayCommand(async () => await StartNewChatAsync());
            CopyMessageCommand = new RelayCommand<ConversationMessage>(CopyMessage);
            EditMessageCommand = new RelayCommand<ConversationMessage>(EditMessage);
            RemoveAttachmentCommand = new RelayCommand<FileAttachment>(RemoveAttachment);

            // Start with a new conversation
            _currentConversation = _conversationHistoryService.CreateConversation();
        }

        public string InputText
        {
            get => _inputText;
            set
            {
                if (_inputText != value)
                {
                    _inputText = value;
                    OnPropertyChanged();
                    ((RelayCommand)SendMessageCommand).RaiseCanExecuteChanged();
                }
            }
        }

        public bool IsSending
        {
            get => _isSending;
            set
            {
                if (_isSending != value)
                {
                    _isSending = value;
                    OnPropertyChanged();
                    ((RelayCommand)SendMessageCommand).RaiseCanExecuteChanged();
                }
            }
        }

        public bool HasMessages => Messages.Count > 0;

        public string ConnectionStatus
        {
            get => _connectionStatus;
            set
            {
                if (_connectionStatus != value)
                {
                    _connectionStatus = value;
                    OnPropertyChanged();
                }
            }
        }

        public bool IsConnected
        {
            get => _isConnected;
            set
            {
                if (_isConnected != value)
                {
                    _isConnected = value;
                    OnPropertyChanged();
                    ConnectionStatus = value ? "Connected" : "Disconnected";
                    ((RelayCommand)SendMessageCommand).RaiseCanExecuteChanged();
                }
            }
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

                    if (value != null)
                    {
                        _ = LoadConversationAsync(value.Id);
                    }
                }
            }
        }

        private bool CanSendMessage()
        {
            if (IsSending)
                return false;

            var hasText = !string.IsNullOrWhiteSpace(InputText);
            var hasAttachments = PendingAttachments.Count > 0;

            if (!hasText && !hasAttachments)
                return false;

            var intent = _musicIntentParser.Parse(InputText);
            if (intent.IsMusicCommand)
                return true;

            return IsConnected;
        }

        private async Task SendMessageAsync()
        {
            if (!CanSendMessage() || _currentConversation == null)
                return;

            // Capture attachments before clearing so they survive the async send.
            var attachmentsToSend = PendingAttachments.ToList();

            var messageText = InputText.Trim();
            InputText = string.Empty;

            // When files are attached, clearly reference them ahead of the text.
            // Saturnia receives only these references today (it cannot read files).
            if (attachmentsToSend.Count > 0)
            {
                var lines = attachmentsToSend
                    .Select(a => $"[attached file: {a.FileName}]")
                    .ToList();
                if (!string.IsNullOrWhiteSpace(messageText))
                {
                    lines.Add(messageText);
                }
                messageText = string.Join("\n", lines);
            }

            PendingAttachments.Clear();
            IsSending = true;

            try
            {
                // Add user message
                var userMessage = new ConversationMessage("user", messageText);
                Messages.Add(userMessage);
                _currentConversation.Messages.Add(userMessage);
                _logger.Log($"User: {messageText}");

                // Generate title from first message if needed
                if (_currentConversation.Messages.Count == 1)
                {
                    _currentConversation.GenerateTitle();
                }

                var intent = _musicIntentParser.Parse(messageText);
                if (intent.IsMusicCommand && _musicPlayerViewModel != null)
                {
                    string responseText = string.Empty;
                    switch (intent.CommandType)
                    {
                        case MusicCommandType.PlayRandom:
                            responseText = await _musicPlayerViewModel.PlayRandomAsync();
                            break;
                        case MusicCommandType.PlayQuery:
                            responseText = await _musicPlayerViewModel.PlayQueryAsync(intent.Query);
                            break;
                        case MusicCommandType.Pause:
                            await _musicPlayerViewModel.PauseAsync();
                            responseText = "⏸ Music paused.";
                            break;
                        case MusicCommandType.Resume:
                            await _musicPlayerViewModel.ResumeAsync();
                            responseText = "▶ Music resumed.";
                            break;
                        case MusicCommandType.Stop:
                            await _musicPlayerViewModel.StopAsync();
                            responseText = "⏹ Music stopped.";
                            break;
                        case MusicCommandType.Skip:
                            await _musicPlayerViewModel.SkipAsync();
                            responseText = "⏭ Skipped to next track.";
                            break;
                    }

                    bool isError = _musicPlayerViewModel.HasError;
                    var assistantMessage = new ConversationMessage("assistant", responseText, isError: isError);
                    Messages.Add(assistantMessage);
                    _currentConversation.Messages.Add(assistantMessage);
                    _logger.Log($"Assistant (Music): {responseText}");
                }
                else
                {
                    // Send to Saturnia
                    var response = await _saturniaClient.SendMessageAsync(messageText);

                    if (response != null)
                    {
                        // Add assistant response
                        var assistantMessage = new ConversationMessage("assistant", response);
                        Messages.Add(assistantMessage);
                        _currentConversation.Messages.Add(assistantMessage);
                        _logger.Log($"Assistant: {response}");
                    }
                    else
                    {
                        // Add error message
                        var errorMessage = new ConversationMessage("assistant", "Failed to get response from Saturnia. Please check the connection.", isError: true);
                        Messages.Add(errorMessage);
                        _currentConversation.Messages.Add(errorMessage);
                        _logger.LogError("Failed to get response from Saturnia");
                    }
                }

                // Save conversation
                await _conversationHistoryService.SaveConversationAsync(_currentConversation);
                await RefreshConversationsListAsync();
            }
            catch (Exception ex)
            {
                _logger.LogError("Error sending message", ex);
                var errorMessage = new ConversationMessage("assistant", $"Error: {ex.Message}", isError: true);
                Messages.Add(errorMessage);
            }
            finally
            {
                IsSending = false;
            }
        }

        private async Task StartNewChatAsync()
        {
            try
            {
                // Save current conversation if it has messages
                if (_currentConversation != null && _currentConversation.Messages.Count > 0)
                {
                    await _conversationHistoryService.SaveConversationAsync(_currentConversation);
                }

                // Create new conversation
                _currentConversation = _conversationHistoryService.CreateConversation();
                Messages.Clear();

                await RefreshConversationsListAsync();
                _logger.Log("Started new conversation");
            }
            catch (Exception ex)
            {
                _logger.LogError("Error starting new chat", ex);
            }
        }

        private void CopyMessage(ConversationMessage? message)
        {
            if (message != null)
            {
                try
                {
                    Clipboard.SetText(message.Content);
                    _logger.Log($"Copied message to clipboard");
                }
                catch (Exception ex)
                {
                    _logger.LogError("Failed to copy message", ex);
                }
            }
        }

        private void EditMessage(ConversationMessage? message)
        {
            if (message != null && message.IsUser)
            {
                // For V1: Load message content into input box for local editing
                // This does not mutate backend conversation or regenerate responses
                InputText = message.Content;
                _logger.Log("Loaded message for editing (local only)");
            }
        }

        // V0.63: file attachment support.
        public void AddAttachmentFromPath(string path)
        {
            if (string.IsNullOrWhiteSpace(path))
                return;

            try
            {
                var attachment = FileAttachment.FromPath(path);

                // Avoid duplicate attachments of the same file.
                if (PendingAttachments.Any(a => string.Equals(a.FilePath, path, StringComparison.OrdinalIgnoreCase)))
                    return;

                PendingAttachments.Add(attachment);
                _logger.Log($"Attachment added: {attachment.FileName}");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Failed to add attachment '{path}'", ex);
            }
        }

        private void RemoveAttachment(FileAttachment? attachment)
        {
            if (attachment != null)
            {
                PendingAttachments.Remove(attachment);
                _logger.Log($"Attachment removed: {attachment.FileName}");
            }
        }

        public async Task LoadConversationAsync(Guid id)
        {
            try
            {
                // Save current conversation first
                if (_currentConversation != null && _currentConversation.Messages.Count > 0)
                {
                    await _conversationHistoryService.SaveConversationAsync(_currentConversation);
                }

                var conversation = await _conversationHistoryService.LoadConversationAsync(id);
                if (conversation != null)
                {
                    _currentConversation = conversation;
                    Messages.Clear();
                    foreach (var message in conversation.Messages)
                    {
                        Messages.Add(message);
                    }
                    _logger.Log($"Loaded conversation: {conversation.Title}");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Failed to load conversation {id}", ex);
            }
        }

        public async Task RefreshConversationsListAsync()
        {
            try
            {
                var summaries = await _conversationHistoryService.LoadAllConversationsAsync();
                Conversations.Clear();
                foreach (var summary in summaries)
                {
                    Conversations.Add(summary);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError("Failed to refresh conversations list", ex);
            }
        }

        protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }

    // Enhanced RelayCommand to support generic parameters
    public class RelayCommand : ICommand
    {
        private readonly Func<Task>? _executeAsync;
        private readonly Func<bool>? _canExecute;
        private readonly Action? _executeSync;

        public event EventHandler? CanExecuteChanged;

        public RelayCommand(Func<Task> executeAsync, Func<bool>? canExecute = null)
        {
            _executeAsync = executeAsync ?? throw new ArgumentNullException(nameof(executeAsync));
            _canExecute = canExecute;
        }

        public RelayCommand(Action executeSync, Func<bool>? canExecute = null)
        {
            _executeSync = executeSync ?? throw new ArgumentNullException(nameof(executeSync));
            _canExecute = canExecute;
        }

        public bool CanExecute(object? parameter)
        {
            return _canExecute?.Invoke() ?? true;
        }

        public async void Execute(object? parameter)
        {
            if (_executeAsync != null)
            {
                await _executeAsync();
            }
            else if (_executeSync != null)
            {
                _executeSync();
            }
        }

        public void RaiseCanExecuteChanged()
        {
            CanExecuteChanged?.Invoke(this, EventArgs.Empty);
        }
    }

    public class RelayCommand<T> : ICommand
    {
        private readonly Action<T?> _execute;
        private readonly Func<T?, bool>? _canExecute;

        public event EventHandler? CanExecuteChanged;

        public RelayCommand(Action<T?> execute, Func<T?, bool>? canExecute = null)
        {
            _execute = execute ?? throw new ArgumentNullException(nameof(execute));
            _canExecute = canExecute;
        }

        public bool CanExecute(object? parameter)
        {
            return _canExecute?.Invoke((T?)parameter) ?? true;
        }

        public void Execute(object? parameter)
        {
            _execute((T?)parameter);
        }

        public void RaiseCanExecuteChanged()
        {
            CanExecuteChanged?.Invoke(this, EventArgs.Empty);
        }
    }
}
