namespace JupiHome.Models
{
    public enum MusicCommandType
    {
        Unknown,
        PlayRandom,
        PlayQuery,
        Pause,
        Resume,
        Stop,
        Skip
    }

    public class MusicIntent
    {
        public MusicCommandType CommandType { get; set; } = MusicCommandType.Unknown;
        public string Query { get; set; } = string.Empty;
        public bool IsMusicCommand => CommandType != MusicCommandType.Unknown;
    }
}
