using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using JupiHome.Models;

namespace JupiHome.ViewModels
{
    /// <summary>
    /// Coordinates workspace navigation and state management for Jupi Home v0.64
    /// </summary>
    public class WorkspaceCoordinator : INotifyPropertyChanged
    {
        private WorkspaceType _currentWorkspace = WorkspaceType.Chat;
        private readonly Dictionary<WorkspaceType, object> _workspaceViewModels;

        public event PropertyChangedEventHandler? PropertyChanged;
        public event EventHandler<WorkspaceNavigationRequest>? NavigationRequested;

        public WorkspaceCoordinator()
        {
            _workspaceViewModels = new Dictionary<WorkspaceType, object>();
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
                    OnPropertyChanged(nameof(CurrentWorkspaceViewModel));
                }
            }
        }

        public object? CurrentWorkspaceViewModel =>
            _workspaceViewModels.ContainsKey(CurrentWorkspace)
                ? _workspaceViewModels[CurrentWorkspace]
                : null;

        public void RegisterWorkspace(WorkspaceType type, object viewModel)
        {
            _workspaceViewModels[type] = viewModel;
        }

        public void NavigateTo(WorkspaceType workspace, Guid? conversationId = null, string? searchQuery = null)
        {
            var request = new WorkspaceNavigationRequest
            {
                TargetWorkspace = workspace,
                ConversationId = conversationId,
                SearchQuery = searchQuery
            };

            NavigationRequested?.Invoke(this, request);
            CurrentWorkspace = workspace;
        }

        public T? GetWorkspaceViewModel<T>(WorkspaceType type) where T : class
        {
            return _workspaceViewModels.ContainsKey(type)
                ? _workspaceViewModels[type] as T
                : null;
        }

        protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }
}
