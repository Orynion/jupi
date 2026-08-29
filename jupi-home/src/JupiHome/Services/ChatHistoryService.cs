using System;
using System.Collections.ObjectModel;
using System.IO;
using System.Text.Json;
using System.Threading.Tasks;
using JupiHome.Models;

namespace JupiHome.Services
{
    public class ChatHistoryService
    {
        private readonly string _historyFilePath;
        private readonly Logger _logger;

        public ChatHistoryService(Logger logger, string historyDirectory)
        {
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));

            if (!Directory.Exists(historyDirectory))
            {
                Directory.CreateDirectory(historyDirectory);
            }

            _historyFilePath = Path.Combine(historyDirectory, "chat_history.json");
        }

        public async Task<ObservableCollection<ChatMessage>> LoadHistoryAsync()
        {
            var messages = new ObservableCollection<ChatMessage>();

            try
            {
                if (File.Exists(_historyFilePath))
                {
                    var json = await File.ReadAllTextAsync(_historyFilePath);
                    var loadedMessages = JsonSerializer.Deserialize<ChatMessage[]>(json);

                    if (loadedMessages != null)
                    {
                        foreach (var message in loadedMessages)
                        {
                            messages.Add(message);
                        }
                        _logger.Log($"Loaded {messages.Count} messages from history");
                    }
                }
                else
                {
                    _logger.Log("No chat history file found, starting fresh");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError("Failed to load chat history", ex);
            }

            return messages;
        }

        public async Task SaveHistoryAsync(ObservableCollection<ChatMessage> messages)
        {
            try
            {
                var json = JsonSerializer.Serialize(messages, new JsonSerializerOptions
                {
                    WriteIndented = true
                });

                await File.WriteAllTextAsync(_historyFilePath, json);
                _logger.Log($"Saved {messages.Count} messages to history");
            }
            catch (Exception ex)
            {
                _logger.LogError("Failed to save chat history", ex);
            }
        }
    }
}
