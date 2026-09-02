using System;
using System.IO;

namespace JupiHome.Models
{
    /// <summary>
    /// Represents a user-attached file waiting to be included with a message.
    /// The UI is explicit about file state: attachments are referenced by
    /// name for Saturnia (the backend cannot read file contents today), so
    /// nothing here pretends files were processed.
    /// </summary>
    public class FileAttachment
    {
        public string FileName { get; set; } = string.Empty;
        public string FilePath { get; set; } = string.Empty;
        public string FileType { get; set; } = "file";
        public long SizeBytes { get; set; }
        public bool IsImage { get; set; }

        public string Icon => IsImage ? "🖼" : "📄";

        public string SizeText
        {
            get
            {
                if (SizeBytes >= 1024L * 1024L)
                    return $"{SizeBytes / (1024.0 * 1024.0):0.#} MB";
                if (SizeBytes >= 1024L)
                    return $"{SizeBytes / 1024.0:0.#} KB";
                return $"{SizeBytes} B";
            }
        }

        public static FileAttachment FromPath(string path)
        {
            if (string.IsNullOrWhiteSpace(path))
                throw new ArgumentException("Path cannot be empty", nameof(path));

            var info = new FileInfo(path);
            var ext = (Path.GetExtension(path) ?? string.Empty).ToLowerInvariant();
            var isImage = ext is ".png" or ".jpg" or ".jpeg" or ".gif" or ".bmp" or ".webp" or ".svg";

            return new FileAttachment
            {
                FileName = info.Name,
                FilePath = path,
                FileType = string.IsNullOrWhiteSpace(ext) ? "file" : ext.TrimStart('.'),
                SizeBytes = info.Exists ? info.Length : 0,
                IsImage = isImage
            };
        }
    }
}