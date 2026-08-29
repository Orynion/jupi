using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace JupiHome.Services
{
    public class SaturniaClient : IDisposable
    {
        private readonly HttpClient _httpClient;
        private readonly Logger _logger;
        private readonly string _baseUrl;
        private bool _disposed;

        public SaturniaClient(string baseUrl, Logger logger)
        {
            _baseUrl = baseUrl?.TrimEnd('/') ?? throw new ArgumentNullException(nameof(baseUrl));
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));

            _httpClient = new HttpClient
            {
                BaseAddress = new Uri(_baseUrl),
                Timeout = TimeSpan.FromSeconds(30)
            };

            _httpClient.DefaultRequestHeaders.Add("Accept", "application/json");
        }

        public async Task<string?> SendMessageAsync(string message, CancellationToken cancellationToken = default)
        {
            if (string.IsNullOrWhiteSpace(message))
            {
                throw new ArgumentException("Message cannot be empty", nameof(message));
            }

            try
            {
                _logger.Log($"Sending message to Saturnia: {message}");

                var requestBody = new { message };
                var jsonContent = JsonSerializer.Serialize(requestBody);
                var content = new StringContent(jsonContent, Encoding.UTF8, "application/json");

                var response = await _httpClient.PostAsync("/api/chat", content, cancellationToken);

                if (!response.IsSuccessStatusCode)
                {
                    _logger.LogError($"Saturnia API returned error: {response.StatusCode}");
                    return null;
                }

                var responseBody = await response.Content.ReadAsStringAsync(cancellationToken);
                _logger.Log($"Raw response: {responseBody}");

                var responseData = JsonSerializer.Deserialize<SaturniaResponse>(responseBody, new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                });

                if (responseData?.Response == null)
                {
                    _logger.LogError("Response JSON missing 'response' field");
                    return null;
                }

                _logger.Log($"Saturnia response: {responseData.Response}");
                return responseData.Response;
            }
            catch (HttpRequestException ex)
            {
                _logger.LogError("HTTP request failed (connection refused or network error)", ex);
                return null;
            }
            catch (TaskCanceledException ex) when (!cancellationToken.IsCancellationRequested)
            {
                _logger.LogError("Request timed out", ex);
                return null;
            }
            catch (JsonException ex)
            {
                _logger.LogError("Failed to parse JSON response", ex);
                return null;
            }
            catch (Exception ex)
            {
                _logger.LogError("Unexpected error during Saturnia request", ex);
                return null;
            }
        }

        public async Task<bool> CheckConnectionAsync(CancellationToken cancellationToken = default)
        {
            try
            {
                var response = await _httpClient.GetAsync("/", cancellationToken);
                return response.IsSuccessStatusCode;
            }
            catch
            {
                return false;
            }
        }

        public void Dispose()
        {
            if (_disposed) return;

            _httpClient?.Dispose();
            _disposed = true;
        }

        private class SaturniaResponse
        {
            public string? Response { get; set; }
        }
    }
}
