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
        /// <summary>
        /// Set by ThemeManager when the theme changes. The converter is static
        /// and cached by WPF, so this flag tells it which palette to use.
        /// </summary>
        public static bool IsDarkMode { get; set; }

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

            Color codeBackgroundColor;
            Color codeBorderColor;
            Color inlineBackgroundColor;
            Color inlineForegroundColor;

            if (IsDarkMode)
            {
                codeBackgroundColor = Color.FromRgb(0x2D, 0x28, 0x25);
                codeBorderColor = Color.FromRgb(0x3D, 0x38, 0x33);
                inlineBackgroundColor = Color.FromRgb(0x33, 0x2E, 0x2A);
                inlineForegroundColor = Color.FromRgb(0xE5, 0x73, 0x73);
            }
            else
            {
                codeBackgroundColor = Color.FromRgb(0xF8, 0xF8, 0xF8);
                codeBorderColor = Color.FromRgb(0xE0, 0xE0, 0xE0);
                inlineBackgroundColor = Color.FromRgb(0xF0, 0xF0, 0xF0);
                inlineForegroundColor = Color.FromRgb(0xC8, 0x00, 0x00);
            }

            var codeBackground = new SolidColorBrush(codeBackgroundColor);
            var codeBorder = new SolidColorBrush(codeBorderColor);
            var inlineBackground = new SolidColorBrush(inlineBackgroundColor);
            var inlineForeground = new SolidColorBrush(inlineForegroundColor);

            foreach (var section in document.Blocks.OfType<Section>().ToList())
            {
                // Style sections that look like code blocks
                if (section.Background != null)
                {
                    section.Background = codeBackground;
                    section.BorderBrush = codeBorder;
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
                        inline.Background = inlineBackground;
                        inline.Foreground = inlineForeground;
                    }
                }

                // Style code block paragraphs
                if (para.Background != null && para.FontFamily?.Source.Contains("Consolas") == true)
                {
                    para.Background = codeBackground;
                    para.BorderBrush = codeBorder;
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
