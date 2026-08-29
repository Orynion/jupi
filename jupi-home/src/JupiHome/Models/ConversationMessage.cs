using System;

namespace JupiHome.Models
{
    /// <summary>
    /// Represents a single message in a conversation
    /// </summary>
    public class ConversationMessage
    {
        public Guid Id { get; set; }
        public string Role { get; set; } = string.Empty;
        public string Content { get; set; } = string.Empty;
        public DateTime Timestamp { get; set; }
        public bool IsError { get; set; }

        public ConversationMessage()
        {
            Id = Guid.NewGuid();
            Timestamp = DateTime.Now;
        }

        public ConversationMessage(string role, string content, bool isError = false)
        {
            Id = Guid.NewGuid();
            Role = role;
            Content = content;
            Timestamp = DateTime.Now;
            IsError = isError;
        }

        // Helper properties for UI binding
        public bool IsUser => Role == "user";
        public bool IsAssistant => Role == "assistant";
    }
}
