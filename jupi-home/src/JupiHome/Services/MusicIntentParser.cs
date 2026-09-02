using System;
using System.Text.RegularExpressions;
using JupiHome.Models;

namespace JupiHome.Services
{
    public class MusicIntentParser
    {
        public MusicIntent Parse(string input)
        {
            if (string.IsNullOrWhiteSpace(input))
            {
                return new MusicIntent { CommandType = MusicCommandType.Unknown };
            }

            string text = input.Trim().ToLowerInvariant();

            // Strip optional conversational prefixes like "hey jupi,", "jupi,", "please"
            text = Regex.Replace(text, @"^(hey\s+jupi|jupi|please)\s*,?\s*", "");

            if (text == "pause")
            {
                return new MusicIntent { CommandType = MusicCommandType.Pause };
            }

            if (text == "resume" || text == "unpause")
            {
                return new MusicIntent { CommandType = MusicCommandType.Resume };
            }

            if (text == "stop")
            {
                return new MusicIntent { CommandType = MusicCommandType.Stop };
            }

            if (text == "skip" || text == "next" || text == "next song")
            {
                return new MusicIntent { CommandType = MusicCommandType.Skip };
            }

            if (text == "play me some music" ||
                text == "play something random" ||
                text == "play music" ||
                text == "play me music" ||
                text == "play random" ||
                text == "play")
            {
                return new MusicIntent { CommandType = MusicCommandType.PlayRandom };
            }

            if (text.StartsWith("play "))
            {
                // Preserve original query casing from raw input if possible
                int playIndex = input.IndexOf("play ", StringComparison.OrdinalIgnoreCase);
                string query = playIndex >= 0 ? input.Substring(playIndex + 5).Trim() : string.Empty;

                string lowerQuery = query.ToLowerInvariant();
                if (lowerQuery == "me some music" || lowerQuery == "something random" || lowerQuery == "random" || lowerQuery == "music")
                {
                    return new MusicIntent { CommandType = MusicCommandType.PlayRandom };
                }

                if (!string.IsNullOrWhiteSpace(query))
                {
                    return new MusicIntent
                    {
                        CommandType = MusicCommandType.PlayQuery,
                        Query = query
                    };
                }
            }

            return new MusicIntent { CommandType = MusicCommandType.Unknown };
        }
    }
}
