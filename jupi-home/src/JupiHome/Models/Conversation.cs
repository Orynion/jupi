using System;
using System.Collections.Generic;
using System.Linq;

namespace JupiHome.Models
{
    /// <summary>
    /// Represents a conversation with multiple messages
    /// </summary>
    public class Conversation
    {
        public Guid Id { get; set; }
        public string Title { get; set; } = "New Conversation";
        public DateTime CreatedAt { get; set; }
        public DateTime UpdatedAt { get; set; }
        public List<ConversationMessage> Messages { get; set; } = new();

        public Conversation()
        {
            Id = Guid.NewGuid();
            CreatedAt = DateTime.Now;
            UpdatedAt = DateTime.Now;
        }

        /// <summary>
        /// Generate a title from the first user message
        /// </summary>
        public void GenerateTitle()
        {
            var firstUserMessage = Messages.FirstOrDefault(m => m.Role == "user");
            if (firstUserMessage != null && !string.IsNullOrWhiteSpace(firstUserMessage.Content))
            {
                // Take first 50 characters of the first user message
                Title = firstUserMessage.Content.Length > 50
                    ? firstUserMessage.Content.Substring(0, 50) + "..."
                    : firstUserMessage.Content;
            }
        }

        /// <summary>
        /// Update the UpdatedAt timestamp
        /// </summary>
        public void Touch()
        {
            UpdatedAt = DateTime.Now;
        }
    }
}
