using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using JupiHome.Models;

namespace JupiHome.Services
{
    /// <summary>
    /// Provides local conversation search with keyword matching and ranking.
    /// Foundation for future semantic/contextual discovery.
    /// </summary>
    public class ConversationSearchService
    {
        private readonly ConversationHistoryService _historyService;
        private readonly Logger _logger;

        public ConversationSearchService(ConversationHistoryService historyService, Logger logger)
        {
            _historyService = historyService ?? throw new ArgumentNullException(nameof(historyService));
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
        }

        /// <summary>
        /// Search conversations by keyword/context matching.
        /// Returns ranked results with matching context.
        /// </summary>
        public async Task<List<SearchResult>> SearchAsync(string query)
        {
            if (string.IsNullOrWhiteSpace(query))
                return new List<SearchResult>();

            try
            {
                var summaries = await _historyService.LoadAllConversationsAsync();
                var results = new List<SearchResult>();

                // Normalize query for case-insensitive matching
                var normalizedQuery = query.Trim().ToLowerInvariant();
                var keywords = normalizedQuery.Split(' ', StringSplitOptions.RemoveEmptyEntries);

                foreach (var summary in summaries)
                {
                    // Load full conversation to search message content
                    var conversation = await _historyService.LoadConversationAsync(summary.Id);
                    if (conversation == null) continue;

                    var searchResult = ScoreConversation(conversation, keywords, normalizedQuery);
                    if (searchResult != null && searchResult.Score > 0)
                    {
                        results.Add(searchResult);
                    }
                }

                // Sort by score (highest first), then by recency
                var rankedResults = results
                    .OrderByDescending(r => r.Score)
                    .ThenByDescending(r => r.UpdatedAt)
                    .Take(50)
                    .ToList();

                _logger.Log($"Search for '{query}' returned {rankedResults.Count} results");
                return rankedResults;
            }
            catch (Exception ex)
            {
                _logger.LogError($"Search failed for query '{query}'", ex);
                throw;
            }
        }

        /// <summary>
        /// Score a conversation against search keywords.
        /// Returns null if no match found.
        /// </summary>
        private SearchResult? ScoreConversation(Conversation conversation, string[] keywords, string fullQuery)
        {
            double score = 0;
            string matchingSnippet = string.Empty;
            string matchReason = string.Empty;

            var titleLower = conversation.Title.ToLowerInvariant();

            // Exact title match (highest priority)
            if (titleLower.Contains(fullQuery))
            {
                score += 100;
                matchReason = "Title match";
                matchingSnippet = conversation.Title;
            }
            else
            {
                // Keyword matches in title
                int titleMatches = keywords.Count(kw => titleLower.Contains(kw));
                if (titleMatches > 0)
                {
                    score += titleMatches * 10;
                    matchReason = $"{titleMatches} keyword(s) in title";
                    matchingSnippet = conversation.Title;
                }
            }

            // Search message content
            var messageMatches = 0;
            ConversationMessage? bestMatchMessage = null;

            foreach (var message in conversation.Messages)
            {
                var contentLower = message.Content.ToLowerInvariant();

                // Exact query match in message
                if (contentLower.Contains(fullQuery))
                {
                    score += 20;
                    messageMatches++;
                    if (bestMatchMessage == null)
                        bestMatchMessage = message;
                }
                else
                {
                    // Keyword matches in message
                    int keywordMatches = keywords.Count(kw => contentLower.Contains(kw));
                    if (keywordMatches > 0)
                    {
                        score += keywordMatches * 2;
                        messageMatches++;
                        if (bestMatchMessage == null)
                            bestMatchMessage = message;
                    }
                }
            }

            // Add message match info
            if (messageMatches > 0)
            {
                if (string.IsNullOrEmpty(matchReason))
                    matchReason = $"Found in {messageMatches} message(s)";
                else
                    matchReason += $", {messageMatches} message(s)";

                // Use best matching message for snippet if no title match
                if (string.IsNullOrEmpty(matchingSnippet) && bestMatchMessage != null)
                {
                    matchingSnippet = ExtractSnippet(bestMatchMessage.Content, keywords);
                }
            }

            // Recency bonus (conversations updated in last 7 days)
            var daysSinceUpdate = (DateTime.Now - conversation.UpdatedAt).TotalDays;
            if (daysSinceUpdate < 7)
            {
                score += (7 - daysSinceUpdate) * 0.5;
            }

            // No match found
            if (score == 0)
                return null;

            return new SearchResult
            {
                ConversationId = conversation.Id,
                Title = conversation.Title,
                MatchingSnippet = matchingSnippet,
                MatchReason = matchReason,
                Score = score,
                UpdatedAt = conversation.UpdatedAt
            };
        }

        /// <summary>
        /// Extract a snippet of text around matching keywords
        /// </summary>
        private string ExtractSnippet(string content, string[] keywords)
        {
            const int snippetLength = 150;
            var contentLower = content.ToLowerInvariant();

            // Find first keyword match position
            int matchPos = -1;
            foreach (var keyword in keywords)
            {
                matchPos = contentLower.IndexOf(keyword);
                if (matchPos >= 0) break;
            }

            if (matchPos < 0)
                return content.Length > snippetLength ? content.Substring(0, snippetLength) + "..." : content;

            // Extract snippet around match
            int start = Math.Max(0, matchPos - 50);
            int length = Math.Min(snippetLength, content.Length - start);

            var snippet = content.Substring(start, length);

            // Add ellipsis if truncated
            if (start > 0) snippet = "..." + snippet;
            if (start + length < content.Length) snippet += "...";

            return snippet;
        }

        /// <summary>
        /// Find potentially relevant conversations based on keywords/topics.
        /// Foundation for automatic contextual discovery.
        /// </summary>
        public async Task<List<SearchResult>> FindRelevantConversationsAsync(string context, int maxResults = 5)
        {
            // Extract potential keywords from context
            var words = context.ToLowerInvariant()
                .Split(new[] { ' ', ',', '.', '?', '!' }, StringSplitOptions.RemoveEmptyEntries)
                .Where(w => w.Length > 3) // Filter short words
                .Distinct()
                .ToArray();

            if (words.Length == 0)
                return new List<SearchResult>();

            // Build query from extracted keywords
            var query = string.Join(" ", words.Take(5)); // Use top 5 keywords

            var results = await SearchAsync(query);
            return results.Take(maxResults).ToList();
        }
    }

    /// <summary>
    /// Search result with ranking information
    /// </summary>
    public class SearchResult
    {
        public Guid ConversationId { get; set; }
        public string Title { get; set; } = string.Empty;
        public string MatchingSnippet { get; set; } = string.Empty;
        public string MatchReason { get; set; } = string.Empty;
        public double Score { get; set; }
        public DateTime UpdatedAt { get; set; }
    }
}
