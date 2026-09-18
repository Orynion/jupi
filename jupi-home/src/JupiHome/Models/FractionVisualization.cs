using System;
using System.Text.RegularExpressions;

namespace JupiHome.Models
{
    /// <summary>
    /// The small, serializable description of a fraction graphic shown with an
    /// assistant response. Keeping this in the message means it also survives
    /// saved and reopened conversations.
    /// </summary>
    public sealed class FractionVisualization
    {
        public int Numerator { get; set; }
        public int Denominator { get; set; }

        public FractionVisualization()
        {
        }

        public FractionVisualization(int numerator, int denominator)
        {
            Numerator = numerator;
            Denominator = denominator;
        }
    }

    /// <summary>
    /// Recognizes explicit requests to see a proper fraction up to 100 parts.
    /// Ordinary fraction questions continue to receive a text-only reply.
    /// </summary>
    public static class FractionVisualizationRequest
    {
        private static readonly Regex FractionPattern = new(@"(?<!\d)(?<numerator>\d{1,2})\s*/\s*(?<denominator>100|[1-9]\d?)(?!\d)", RegexOptions.Compiled);
        private static readonly Regex VisualIntentPattern = new(@"\b(show|visuali[sz]e|visuali[sz]ation|visual|graphic|picture|draw|look(?:s)?(?:\s+like)?|representation|diagram|graph|chart|pie)\b", RegexOptions.Compiled | RegexOptions.IgnoreCase);

        public static bool TryCreate(string? message, out FractionVisualization? visualization)
        {
            visualization = null;
            if (string.IsNullOrWhiteSpace(message) || !VisualIntentPattern.IsMatch(message))
            {
                return false;
            }

            var match = FractionPattern.Match(message);
            if (!match.Success ||
                !int.TryParse(match.Groups["numerator"].Value, out var numerator) ||
                !int.TryParse(match.Groups["denominator"].Value, out var denominator) ||
                denominator < 2 || denominator > 100 || numerator < 1 || numerator >= denominator)
            {
                return false;
            }

            visualization = new FractionVisualization(numerator, denominator);
            return true;
        }
    }
}
