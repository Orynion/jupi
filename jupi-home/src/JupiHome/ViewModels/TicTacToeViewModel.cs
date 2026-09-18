using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Windows.Input;

namespace JupiHome.ViewModels
{
    public sealed class TicTacToeViewModel : INotifyPropertyChanged
    {
        private static readonly int[][] WinningLines =
        {
            new[] { 0, 1, 2 }, new[] { 3, 4, 5 }, new[] { 6, 7, 8 },
            new[] { 0, 3, 6 }, new[] { 1, 4, 7 }, new[] { 2, 5, 8 },
            new[] { 0, 4, 8 }, new[] { 2, 4, 6 }
        };

        private readonly string[] _board = new string[9];
        private readonly Random _random = new();
        private string _status = "Your turn. You are X.";
        private bool _isGameOver;

        public ObservableCollection<TicTacToeCell> Cells { get; } = new();
        public ICommand CellCommand { get; }
        public ICommand NewGameCommand { get; }

        public event PropertyChangedEventHandler? PropertyChanged;

        public TicTacToeViewModel()
        {
            for (var index = 0; index < 9; index++)
            {
                Cells.Add(new TicTacToeCell(index));
            }

            CellCommand = new RelayCommand<int>(PlayCell, CanPlayCell);
            NewGameCommand = new RelayCommand(NewGame);
            NewGame();
        }

        public string Status
        {
            get => _status;
            private set
            {
                if (_status != value)
                {
                    _status = value;
                    OnPropertyChanged();
                }
            }
        }

        public bool IsGameOver
        {
            get => _isGameOver;
            private set
            {
                if (_isGameOver != value)
                {
                    _isGameOver = value;
                    OnPropertyChanged();
                    ((RelayCommand<int>)CellCommand).RaiseCanExecuteChanged();
                }
            }
        }

        public void NewGame()
        {
            Array.Fill(_board, string.Empty);
            foreach (var cell in Cells)
            {
                cell.Mark = string.Empty;
            }

            IsGameOver = false;
            Status = "Your turn. You are X.";
            ((RelayCommand<int>)CellCommand).RaiseCanExecuteChanged();
        }

        private bool CanPlayCell(int index)
        {
            return !IsGameOver && index >= 0 && index < _board.Length && string.IsNullOrEmpty(_board[index]);
        }

        private void PlayCell(int index)
        {
            if (!CanPlayCell(index))
            {
                return;
            }

            SetCell(index, "X");
            if (FinishIfNeeded("You win! Jupi is defeated this round."))
            {
                return;
            }

            Status = "Jupi is thinking...";
            var move = ChooseJupiMove();
            if (move >= 0)
            {
                SetCell(move, "O");
            }

            FinishIfNeeded("Jupi wins this round. Ask for a rematch.");
            if (!IsGameOver)
            {
                Status = "Your turn. You are X.";
            }
        }

        private void SetCell(int index, string mark)
        {
            _board[index] = mark;
            Cells[index].Mark = mark;
        }

        private bool FinishIfNeeded(string winMessage)
        {
            if (HasWinner("X"))
            {
                IsGameOver = true;
                Status = winMessage;
                return true;
            }

            if (HasWinner("O"))
            {
                IsGameOver = true;
                Status = winMessage;
                return true;
            }

            if (_board.All(cell => !string.IsNullOrEmpty(cell)))
            {
                IsGameOver = true;
                Status = "A draw. The board is perfectly stubborn.";
                return true;
            }

            return false;
        }

        private bool HasWinner(string mark)
        {
            return WinningLines.Any(line => line.All(index => _board[index] == mark));
        }

        private int ChooseJupiMove()
        {
            var winningMove = FindFinishingMove("O");
            if (winningMove >= 0)
            {
                return winningMove;
            }

            var blockingMove = FindFinishingMove("X");
            if (blockingMove >= 0)
            {
                return blockingMove;
            }

            if (string.IsNullOrEmpty(_board[4]))
            {
                return 4;
            }

            var availableCorners = new[] { 0, 2, 6, 8 }.Where(index => string.IsNullOrEmpty(_board[index])).ToArray();
            if (availableCorners.Length > 0)
            {
                return availableCorners[_random.Next(availableCorners.Length)];
            }

            var available = Enumerable.Range(0, 9).Where(index => string.IsNullOrEmpty(_board[index])).ToArray();
            return available.Length > 0 ? available[0] : -1;
        }

        private int FindFinishingMove(string mark)
        {
            foreach (var index in Enumerable.Range(0, 9))
            {
                if (!string.IsNullOrEmpty(_board[index]))
                {
                    continue;
                }

                _board[index] = mark;
                var wins = HasWinner(mark);
                _board[index] = string.Empty;
                if (wins)
                {
                    return index;
                }
            }

            return -1;
        }

        private void OnPropertyChanged([CallerMemberName] string? propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }

    public sealed class TicTacToeCell : INotifyPropertyChanged
    {
        private string _mark = string.Empty;

        public TicTacToeCell(int index)
        {
            Index = index;
        }

        public int Index { get; }

        public string Mark
        {
            get => _mark;
            set
            {
                if (_mark != value)
                {
                    _mark = value;
                    PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(Mark)));
                }
            }
        }

        public event PropertyChangedEventHandler? PropertyChanged;
    }
}
