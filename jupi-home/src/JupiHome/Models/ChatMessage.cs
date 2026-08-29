using System;

namespace JupiHome.Models
{
    public class ChatMessage
    {
        public string Role { get; set; } = string.Empty;
        public string Content { get; set; } = string.Empty;
        public DateTime Timestamp { get; set; }
        public bool IsError { get; set; }

        public ChatMessage()
        {
            Timestamp = DateTime.Now;
        }

        public ChatMessage(string role, string content, bool isError = false)
        {
            Role = role;
            Content = content;
            Timestamp = DateTime.Now;
            IsError = isError;
        }

        public bool IsUser => Role == "user";
        public bool IsAssistant => Role == "assistant";
    }
}
