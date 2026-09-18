using System;

namespace JupiHome.Models
{
    /// <summary>
    /// Defines the available workspace types in Jupi Home
    /// </summary>
    public enum WorkspaceType
    {
        Chat,
        Chats,
        Search,
        Music,
        Settings
    }

    /// <summary>
    /// Navigation request for workspace switching
    /// </summary>
    public class WorkspaceNavigationRequest
    {
        public WorkspaceType TargetWorkspace { get; set; }
        public Guid? ConversationId { get; set; }
        public string? SearchQuery { get; set; }
    }
}
