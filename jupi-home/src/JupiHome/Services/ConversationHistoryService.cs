using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using JupiHome.Models;

namespace JupiHome.Services
{
    /// <summary>
    /// Manages conversation history storage in local AppData
    /// </summary>
    public class ConversationHistoryService
    {
        private readonly string _conversationsDirectory;
        private readonly Logger _logger;
        private readonly JsonSerializerOptions _jsonOptions;

        public ConversationHistoryService(Logger logger)
        {
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));

            // Store in AppData/Local/JupiHome/conversations/
            var appDataPath = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            var jupiHomeDataPath = Path.Combine(appDataPath, "JupiHome");
            _conversationsDirectory = Path.Combine(jupiHomeDataPath, "conversations");

            // Create directory if it doesn't exist
            if (!Directory.Exists(_conversationsDirectory))
            {
                Directory.CreateDirectory(_conversationsDirectory);
                _logger.Log($"Created conversations directory: {_conversationsDirectory}");
            }

            _jsonOptions = new JsonSerializerOptions
            {
                WriteIndented = true
            };
        }

        /// <summary>
        /// Create a new conversation
        /// </summary>
        public Conversation CreateConversation()
        {
            var conversation = new Conversation();
            _logger.Log($"Created new conversation: {conversation.Id}");
            return conversation;
        }

        /// <summary>
        /// Save a conversation to disk
        /// </summary>
        public async Task SaveConversationAsync(Conversation conversation)
        {
            if (conversation == null)
                throw new ArgumentNullException(nameof(conversation));

            try
            {
                conversation.Touch();

                var filePath = GetConversationFilePath(conversation.Id);
                var json = JsonSerializer.Serialize(conversation, _jsonOptions);
                await File.WriteAllTextAsync(filePath, json);

                _logger.Log($"Saved conversation {conversation.Id} with {conversation.Messages.Count} messages");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Failed to save conversation {conversation.Id}", ex);
                throw;
            }
        }

        /// <summary>
        /// Load a specific conversation by ID
        /// </summary>
        public async Task<Conversation?> LoadConversationAsync(Guid id)
        {
            try
            {
                var filePath = GetConversationFilePath(id);
                if (!File.Exists(filePath))
                {
                    _logger.Log($"Conversation file not found: {id}");
                    return null;
                }

                var json = await File.ReadAllTextAsync(filePath);
                var conversation = JsonSerializer.Deserialize<Conversation>(json);

                if (conversation != null)
                {
                    _logger.Log($"Loaded conversation {id} with {conversation.Messages.Count} messages");
                }

                return conversation;
            }
            catch (Exception ex)
            {
                _logger.LogError($"Failed to load conversation {id}", ex);
                return null;
            }
        }

        /// <summary>
        /// Load all conversations (metadata only, not full messages)
        /// </summary>
        public async Task<List<ConversationSummary>> LoadAllConversationsAsync()
        {
            var summaries = new List<ConversationSummary>();

            try
            {
                var files = Directory.GetFiles(_conversationsDirectory, "*.json");
                _logger.Log($"Found {files.Length} conversation files");

                foreach (var file in files)
                {
                    try
                    {
                        var json = await File.ReadAllTextAsync(file);
                        var conversation = JsonSerializer.Deserialize<Conversation>(json);

                        if (conversation != null)
                        {
                            summaries.Add(new ConversationSummary
                            {
                                Id = conversation.Id,
                                Title = conversation.Title,
                                CreatedAt = conversation.CreatedAt,
                                UpdatedAt = conversation.UpdatedAt,
                                MessageCount = conversation.Messages.Count
                            });
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError($"Failed to load conversation from {file}", ex);
                    }
                }

                // Sort by most recently updated first
                summaries = summaries.OrderByDescending(s => s.UpdatedAt).ToList();
                _logger.Log($"Loaded {summaries.Count} conversation summaries");
            }
            catch (Exception ex)
            {
                _logger.LogError("Failed to load conversations", ex);
            }

            return summaries;
        }

        /// <summary>
        /// Delete a conversation
        /// </summary>
        public async Task DeleteConversationAsync(Guid id)
        {
            try
            {
                var filePath = GetConversationFilePath(id);
                if (File.Exists(filePath))
                {
                    await Task.Run(() => File.Delete(filePath));
                    _logger.Log($"Deleted conversation {id}");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Failed to delete conversation {id}", ex);
                throw;
            }
        }

        /// <summary>
        /// Get the file path for a conversation
        /// </summary>
        private string GetConversationFilePath(Guid id)
        {
            return Path.Combine(_conversationsDirectory, $"{id}.json");
        }
    }

    /// <summary>
    /// Summary information for a conversation (for list display)
    /// </summary>
    public class ConversationSummary
    {
        public Guid Id { get; set; }
        public string Title { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; }
        public DateTime UpdatedAt { get; set; }
        public int MessageCount { get; set; }
    }
}
