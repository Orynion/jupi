using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Windows.Media;

namespace JupiHome.Controls
{
    /// <summary>
    /// Adorner that adds a Copy button to code blocks
    /// </summary>
    public class CodeBlockAdorner : Adorner
    {
        private readonly Button _copyButton;
        private readonly string _codeText;
        private readonly VisualCollection _visualChildren;

        public CodeBlockAdorner(UIElement adornedElement, string codeText) : base(adornedElement)
        {
            _codeText = codeText;
            _visualChildren = new VisualCollection(this);

            // Create copy button
            _copyButton = new Button
            {
                Content = "Copy",
                Width = 60,
                Height = 24,
                FontSize = 11,
                Background = new SolidColorBrush(Color.FromRgb(91, 140, 133)), // AccentBrush
                Foreground = Brushes.White,
                BorderThickness = new Thickness(0),
                Cursor = System.Windows.Input.Cursors.Hand,
                Opacity = 0.9
            };

            _copyButton.Click += CopyButton_Click;
            _visualChildren.Add(_copyButton);
        }

        private void CopyButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                Clipboard.SetText(_codeText);
                _copyButton.Content = "✓ Copied";

                // Reset button text after 2 seconds
                var timer = new System.Windows.Threading.DispatcherTimer
                {
                    Interval = TimeSpan.FromSeconds(2)
                };
                timer.Tick += (s, args) =>
                {
                    _copyButton.Content = "Copy";
                    timer.Stop();
                };
                timer.Start();
            }
            catch
            {
                _copyButton.Content = "Failed";
            }
        }

        protected override int VisualChildrenCount => _visualChildren.Count;

        protected override Visual GetVisualChild(int index)
        {
            return _visualChildren[index];
        }

        protected override Size ArrangeOverride(Size finalSize)
        {
            // Position button in top-right corner of the code block
            var adornedRect = new Rect(AdornedElement.RenderSize);
            var buttonRect = new Rect(
                adornedRect.Right - _copyButton.Width - 8,
                adornedRect.Top + 8,
                _copyButton.Width,
                _copyButton.Height
            );

            _copyButton.Arrange(buttonRect);
            return finalSize;
        }
    }
}
