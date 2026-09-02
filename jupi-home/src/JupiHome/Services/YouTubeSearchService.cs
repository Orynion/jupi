using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using System.Web;
using JupiHome.Configuration;
using JupiHome.Models;

namespace JupiHome.Services
{
    public class YouTubeSearchService
    {
        private readonly HttpClient _httpClient;
        private readonly AppSettings _settings;
        private readonly Logger _logger;

        private static readonly string[] RandomTerms = new[]
        {
            "top music hits", "lofi hip hop beats", "chill acoustic music",
            "popular pop songs", "top rock classics", "jazz instrumental music"
        };

        public YouTubeSearchService(AppSettings settings, Logger logger, HttpClient? httpClient = null)
        {
            _settings = settings ?? throw new ArgumentNullException(nameof(settings));
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
            _httpClient = httpClient ?? new HttpClient();
        }

        public async Task<(List<MusicTrack> Tracks, string? ErrorMessage)> SearchTracksAsync(string query, bool isRandom = false)
        {
            if (string.IsNullOrWhiteSpace(_settings.YouTubeApiKey))
            {
                _logger.LogError("YouTube API key missing in AppSettings.");
                return (new List<MusicTrack>(), "YouTube API Key is missing. Please set YouTubeApiKey in appsettings.json.");
            }

            string term = query;
            if (isRandom || string.IsNullOrWhiteSpace(term))
            {
                term = RandomTerms[new Random().Next(RandomTerms.Length)];
            }

            try
            {
                string encodedQuery = HttpUtility.UrlEncode(term);
                string url = $"https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&videoEmbeddable=true&maxResults=10&q={encodedQuery}&key={_settings.YouTubeApiKey}";

                _logger.Log($"Searching YouTube for: '{term}'");
                var response = await _httpClient.GetAsync(url);

                if (!response.IsSuccessStatusCode)
                {
                    _logger.LogError($"YouTube API returned HTTP {response.StatusCode}");
                    if (response.StatusCode == System.Net.HttpStatusCode.Forbidden || response.StatusCode == System.Net.HttpStatusCode.Unauthorized)
                        return (new List<MusicTrack>(), "YouTube API key error or quota exceeded.");
                    return (new List<MusicTrack>(), $"YouTube API returned error: {response.StatusCode}");
                }

                string json = await response.Content.ReadAsStringAsync();
                using var doc = JsonDocument.Parse(json);
                var tracks = new List<MusicTrack>();

                if (doc.RootElement.TryGetProperty("items", out var items) && items.ValueKind == JsonValueKind.Array)
                {
                    foreach (var item in items.EnumerateArray())
                    {
                        if (item.TryGetProperty("id", out var idObj) && idObj.TryGetProperty("videoId", out var vId))
                        {
                            string videoId = vId.GetString() ?? string.Empty;
                            if (string.IsNullOrEmpty(videoId)) continue;

                            string title = string.Empty;
                            string channel = string.Empty;
                            string thumb = string.Empty;

                            if (item.TryGetProperty("snippet", out var snippet))
                            {
                                if (snippet.TryGetProperty("title", out var tProp)) title = HttpUtility.HtmlDecode(tProp.GetString() ?? "");
                                if (snippet.TryGetProperty("channelTitle", out var cProp)) channel = HttpUtility.HtmlDecode(cProp.GetString() ?? "");
                                if (snippet.TryGetProperty("thumbnails", out var thumbs) && thumbs.TryGetProperty("medium", out var mThumb) && mThumb.TryGetProperty("url", out var uProp))
                                    thumb = uProp.GetString() ?? "";
                            }

                            tracks.Add(new MusicTrack { VideoId = videoId, Title = title, ChannelTitle = channel, ThumbnailUrl = thumb });
                        }
                    }
                }

                if (tracks.Count == 0)
                {
                    _logger.Log($"No music results found for '{term}'.");
                    return (tracks, $"No music results found for '{term}'.");
                }

                _logger.Log($"Found {tracks.Count} tracks for '{term}'.");
                return (tracks, null);
            }
            catch (HttpRequestException ex)
            {
                _logger.LogError($"Network failure during YouTube search for '{term}'", ex);
                return (new List<MusicTrack>(), "Network error: Unable to connect to YouTube.");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Unexpected error during YouTube search for '{term}'", ex);
                return (new List<MusicTrack>(), $"Failed to search music: {ex.Message}");
            }
        }
    }
}
