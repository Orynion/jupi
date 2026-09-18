using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Shapes;

namespace JupiHome.Controls
{
    /// <summary>
    /// Shows fractions with up to 20 parts as a pie and uses an interactive
    /// hundred-chart for larger denominators (up to 100 parts).
    /// </summary>
    public sealed class FractionPieChart : UserControl
    {
        private const double ChartSize = 156;
        private const double Radius = 68;

        private readonly Canvas _chartCanvas;
        private readonly TextBlock _fractionLabel;
        private readonly TextBlock _descriptionLabel;
        private int _selectedSlices;
        private int _initialNumerator;

        public static readonly DependencyProperty NumeratorProperty = DependencyProperty.Register(
            nameof(Numerator), typeof(int), typeof(FractionPieChart), new PropertyMetadata(1, OnFractionChanged));

        public static readonly DependencyProperty DenominatorProperty = DependencyProperty.Register(
            nameof(Denominator), typeof(int), typeof(FractionPieChart), new PropertyMetadata(2, OnFractionChanged));

        public int Numerator
        {
            get => (int)GetValue(NumeratorProperty);
            set => SetValue(NumeratorProperty, value);
        }

        public int Denominator
        {
            get => (int)GetValue(DenominatorProperty);
            set => SetValue(DenominatorProperty, value);
        }

        public FractionPieChart()
        {
            var card = new Border
            {
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(8),
                Padding = new Thickness(14),
                Margin = new Thickness(0, 10, 0, 2)
            };
            card.SetResourceReference(Border.BackgroundProperty, "SurfaceBrush");
            card.SetResourceReference(Border.BorderBrushProperty, "BorderBrush");

            var layout = new Grid();
            layout.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(ChartSize) });
            layout.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            _chartCanvas = new Canvas { Width = ChartSize, Height = ChartSize, Cursor = Cursors.Hand };
            Grid.SetColumn(_chartCanvas, 0);
            layout.Children.Add(_chartCanvas);

            var details = new StackPanel
            {
                Margin = new Thickness(14, 6, 4, 4),
                VerticalAlignment = VerticalAlignment.Center,
                MinWidth = 145
            };
            Grid.SetColumn(details, 1);

            _fractionLabel = new TextBlock { FontSize = 26, FontWeight = FontWeights.SemiBold };
            _fractionLabel.SetResourceReference(TextBlock.ForegroundProperty, "TextPrimaryBrush");
            details.Children.Add(_fractionLabel);

            _descriptionLabel = new TextBlock
            {
                FontSize = 12,
                TextWrapping = TextWrapping.Wrap,
                Width = 155,
                Margin = new Thickness(0, 4, 0, 10)
            };
            _descriptionLabel.SetResourceReference(TextBlock.ForegroundProperty, "TextSecondaryBrush");
            details.Children.Add(_descriptionLabel);

            var resetButton = new Button
            {
                Content = "Reset",
                Padding = new Thickness(10, 5, 10, 5),
                HorizontalAlignment = HorizontalAlignment.Left,
                Cursor = Cursors.Hand
            };
            resetButton.SetResourceReference(Button.BackgroundProperty, "SelectionBrush");
            resetButton.SetResourceReference(Button.ForegroundProperty, "TextPrimaryBrush");
            resetButton.SetResourceReference(Button.BorderBrushProperty, "BorderBrush");
            resetButton.Click += (_, __) =>
            {
                _selectedSlices = _initialNumerator;
                DrawChart();
            };
            details.Children.Add(resetButton);

            layout.Children.Add(details);
            card.Child = layout;
            Content = card;

            Loaded += (_, __) => ResetFromProperties();
        }

        private static void OnFractionChanged(DependencyObject dependencyObject, DependencyPropertyChangedEventArgs args)
        {
            ((FractionPieChart)dependencyObject).ResetFromProperties();
        }

        private void ResetFromProperties()
        {
            if (!IsLoaded)
            {
                return;
            }

            var denominator = Math.Clamp(Denominator, 2, 100);
            _initialNumerator = Math.Clamp(Numerator, 1, denominator - 1);
            _selectedSlices = denominator <= 20
                ? _initialNumerator
                : Math.Clamp((int)Math.Round(100.0 * _initialNumerator / denominator), 1, 100);
            DrawChart();
        }

        private void DrawChart()
        {
            if (!IsLoaded)
            {
                return;
            }

            var denominator = Math.Clamp(Denominator, 2, 100);
            if (denominator > 20)
            {
                DrawHundredChart(denominator);
                return;
            }

            _selectedSlices = Math.Clamp(_selectedSlices, 1, denominator);
            _chartCanvas.Children.Clear();

            for (var index = 0; index < denominator; index++)
            {
                var slice = new Path
                {
                    Data = CreateSliceGeometry(index, denominator),
                    StrokeThickness = 1.5,
                    Tag = index,
                    ToolTip = $"Shade {index + 1} of {denominator} parts"
                };
                slice.SetResourceReference(Shape.StrokeProperty, "SurfaceBrush");
                slice.SetResourceReference(Shape.FillProperty, index < _selectedSlices ? "AccentBrush" : "SelectionBrush");
                slice.MouseLeftButtonUp += Slice_Click;
                _chartCanvas.Children.Add(slice);
            }

            _fractionLabel.Text = $"{_selectedSlices}/{denominator}";
            _descriptionLabel.Text = $"{_selectedSlices} of the {denominator} equal parts are shaded. Click a slice to explore.";
        }

        private void DrawHundredChart(int originalDenominator)
        {
            const int columns = 10;
            const int totalBoxes = 100;
            const double gap = 2;
            const double boxSize = (ChartSize - (gap * (columns + 1))) / columns;

            _selectedSlices = Math.Clamp(_selectedSlices, 1, totalBoxes);
            _chartCanvas.Children.Clear();

            for (var index = 0; index < totalBoxes; index++)
            {
                var row = index / columns;
                var column = index % columns;
                var box = new Rectangle
                {
                    Width = boxSize,
                    Height = boxSize,
                    RadiusX = 1.5,
                    RadiusY = 1.5,
                    StrokeThickness = 1,
                    Tag = index,
                    ToolTip = $"Shade {index + 1} of 100 boxes"
                };
                box.SetResourceReference(Shape.StrokeProperty, "SurfaceBrush");
                box.SetResourceReference(Shape.FillProperty, index < _selectedSlices ? "AccentBrush" : "SelectionBrush");
                box.MouseLeftButtonUp += Slice_Click;
                Canvas.SetLeft(box, gap + (column * (boxSize + gap)));
                Canvas.SetTop(box, gap + (row * (boxSize + gap)));
                _chartCanvas.Children.Add(box);
            }

            _fractionLabel.Text = $"{_selectedSlices}/100";
            _descriptionLabel.Text = $"Hundred chart: {Numerator}/{originalDenominator} is shown as about {_selectedSlices}/100. Click a box to explore.";
        }

        private void Slice_Click(object sender, MouseButtonEventArgs args)
        {
            if (sender is Shape { Tag: int index })
            {
                _selectedSlices = index + 1;
                DrawChart();
                args.Handled = true;
            }
        }

        private static Geometry CreateSliceGeometry(int index, int total)
        {
            var center = new Point(ChartSize / 2, ChartSize / 2);
            var startAngle = -90 + (index * 360.0 / total);
            var endAngle = -90 + ((index + 1) * 360.0 / total);
            var start = PointOnCircle(center, startAngle);
            var end = PointOnCircle(center, endAngle);

            var figure = new PathFigure { StartPoint = center, IsClosed = true, IsFilled = true };
            figure.Segments.Add(new LineSegment(start, true));
            figure.Segments.Add(new ArcSegment(end, new Size(Radius, Radius), 360.0 / total, false, SweepDirection.Clockwise, true));
            figure.Segments.Add(new LineSegment(center, true));
            return new PathGeometry(new[] { figure });
        }

        private static Point PointOnCircle(Point center, double angle)
        {
            var radians = angle * Math.PI / 180.0;
            return new Point(center.X + Radius * Math.Cos(radians), center.Y + Radius * Math.Sin(radians));
        }
    }
}
