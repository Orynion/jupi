using System.Windows;
using System.Windows.Controls;
using JupiHome.Models;
using JupiHome.ViewModels;

namespace JupiHome
{
    /// <summary>
    /// Selects the appropriate DataTemplate based on the current workspace type
    /// </summary>
    public class WorkspaceTemplateSelector : DataTemplateSelector
    {
        public DataTemplate? ChatWorkspaceTemplate { get; set; }
        public DataTemplate? ChatsWorkspaceTemplate { get; set; }
        public DataTemplate? SearchWorkspaceTemplate { get; set; }
        public DataTemplate? MusicWorkspaceTemplate { get; set; }
        public DataTemplate? SettingsWorkspaceTemplate { get; set; }

        public override DataTemplate? SelectTemplate(object item, DependencyObject container)
        {
            if (container is FrameworkElement element && element.DataContext is MainViewModel mainViewModel)
            {
                return mainViewModel.CurrentWorkspace switch
                {
                    WorkspaceType.Chat => ChatWorkspaceTemplate,
                    WorkspaceType.Chats => ChatsWorkspaceTemplate,
                    WorkspaceType.Search => SearchWorkspaceTemplate,
                    WorkspaceType.Music => MusicWorkspaceTemplate,
                    WorkspaceType.Settings => SettingsWorkspaceTemplate,
                    _ => ChatWorkspaceTemplate
                };
            }

            return base.SelectTemplate(item, container);
        }
    }
}
