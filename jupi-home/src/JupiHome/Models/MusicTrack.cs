namespace JupiHome.Models
{
    public class MusicTrack
    {
        public string VideoId { get; set; } = string.Empty;
        public string Title { get; set; } = string.Empty;
        public string ChannelTitle { get; set; } = string.Empty;
        public string ThumbnailUrl { get; set; } = string.Empty;

        public string EmbedUrl => $"https://www.youtube.com/embed/{VideoId}?enablejsapi=1&autoplay=1";
    }
}
