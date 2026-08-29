using System;
using System.Linq;
using System.Windows;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Media;
using Markdig;
using Markdig.Wpf;

namespace JupiHome.Converters
{
    /// <summary>
    /// Converts Markdown text to a FlowDocument for display in WPF
    /// </summary>
    public class MarkdownToFlowDocumentConverter : IValueConverter
    {
        private static readonly MarkdownPipeline _pipeline = new MarkdownPipelineBuilder()
            .UseSupportedExtensions()
            .Build();

        public object Convert(object value, Type targetType, object parameter, System.Globalization.CultureInfo culture)
        {
            if (value is string markdown && !string.IsNullOrWhiteSpace(markdown))
            {
                try
                {
                    // Ensure proper encoding for emojis and special characters
                    var encodedMarkdown = System.Text.Encoding.UTF8.GetString(
                        System.Text.Encoding.UTF8.GetBytes(markdown));
                    
                    var document = Markdig.Wpf.Markdown.ToFlowDocument(encodedMarkdown, _pipeline);

                    if (document != null)
                    {
                        // Style the document for better readability
                        document.PagePadding = new Thickness(0);
                        document.FontFamily = new System.Windows.Media.FontFamily("Segoe UI");
                        document.FontSize = 14;

                        // Style code blocks (without adding UI elements)
                        StyleCodeBlocks(document);

                        return document;
                    }
                }
                catch (ArgumentException argEx)
                {
                    System.Diagnostics.Debug.WriteLine($"Argument error in markdown conversion: {argEx.Message}");
                    return CreatePlainTextDocument(markdown);
                }
                catch (OutOfMemoryException memEx)
                {
                    System.Diagnostics.Debug.WriteLine($"Out of memory error in markdown conversion: {memEx.Message}");
                    return CreatePlainTextDocument(markdown);
                }
                catch (Exception ex)
                {
                    // If markdown parsing fails, fall back to plain text
                    System.Diagnostics.Debug.WriteLine($"Markdown conversion error: {ex.GetType().Name} - {ex.Message}");
                    return CreatePlainTextDocument(markdown);
                }
            }

            return CreatePlainTextDocument(value?.ToString() ?? string.Empty);
        }

        public object ConvertBack(object value, Type targetType, object parameter, System.Globalization.CultureInfo culture)
        {
            throw new NotImplementedException();
        }

        private void StyleCodeBlocks(FlowDocument document)
        {
            // Style code blocks that Markdig.Wpf creates
            // Note: We can't add UI elements (buttons) here because converters
            // can be called from non-UI threads which causes crashes

            foreach (var section in document.Blocks.OfType<Section>().ToList())
            {
                // Style sections that look like code blocks
                if (section.Background != null)
                {
                    section.Background = new SolidColorBrush(Color.FromRgb(248, 248, 248));
                    section.BorderBrush = new SolidColorBrush(Color.FromRgb(224, 224, 224));
                    section.BorderThickness = new Thickness(1);
                    section.Padding = new Thickness(12, 8, 12, 8);
                    section.Margin = new Thickness(0, 8, 0, 8);
                }
            }

            // Style paragraphs with monospace font (inline code)
            foreach (var para in document.Blocks.OfType<Paragraph>().ToList())
            {
                foreach (var inline in para.Inlines.OfType<Run>().ToList())
                {
                    // Check if this is inline code (monospace font)
                    if (inline.FontFamily != null && inline.FontFamily.Source.Contains("Consolas"))
                    {
                        inline.Background = new SolidColorBrush(Color.FromRgb(240, 240, 240));
                        inline.Foreground = new SolidColorBrush(Color.FromRgb(200, 0, 0));
                    }
                }

                // Style code block paragraphs
                if (para.Background != null && para.FontFamily?.Source.Contains("Consolas") == true)
                {
                    para.Background = new SolidColorBrush(Color.FromRgb(248, 248, 248));
                    para.BorderBrush = new SolidColorBrush(Color.FromRgb(224, 224, 224));
                    para.BorderThickness = new Thickness(1);
                    para.Padding = new Thickness(12, 8, 12, 8);
                    para.Margin = new Thickness(0, 8, 0, 8);
                    para.FontFamily = new FontFamily("Consolas, Courier New, monospace");
                    para.FontSize = 13;
                }
            }
        }

        private FlowDocument CreatePlainTextDocument(string text)
        {
            var document = new FlowDocument(new Paragraph(new Run(text)))
            {
                PagePadding = new Thickness(0),
                FontFamily = new System.Windows.Media.FontFamily("Segoe UI"),
                FontSize = 14
            };
            return document;
        }
    }
}
