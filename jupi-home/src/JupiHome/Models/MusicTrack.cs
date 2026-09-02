namespace JupiHome.Models
{
    public class MusicTrack
    {
        public string VideoId { get; set; } = string.Empty;
        public string Title { get; set; } = string.Empty;
        public string ChannelTitle { get; set; } = string.Empty;
        public string ThumbnailUrl { get; set; } = string.Empty;

        public string EmbedUrl =>
            $"https://www.youtube.com/embed/{VideoId}?autoplay=1&playsinline=1&rel=0&enablejsapi=1&origin=https%3A%2F%2Fwww.youtube.com";
    }
}
