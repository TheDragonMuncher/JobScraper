using System.Reflection.Metadata;
using HtmlAgilityPack;
using JobScraper.Models;
using Microsoft.Extensions.Logging;

namespace JobScraper.Services;

class ScraperService
{
    readonly HttpClient _http;
    readonly ILogger<ScraperService> _logger;
    readonly string _targetUrl;

    // specific paths for indeed scraping
    const string JobCardXPath = "";

    public ScraperService(HttpClient http, ILogger<ScraperService> logger, string url)
    {
        _http = http;
        _logger = logger;
        _targetUrl = url;
    }

    public async Task<List<JobPosting>> ScrapSite(CancellationToken ct = default)
    {
        var html = await _http.GetStringAsync(_targetUrl, ct);
        var doc = new HtmlDocument();
        doc.LoadHtml(html);

        var cards = doc.DocumentNode.SelectNodes(JobCardXPath);

        if (cards == null || cards.Count == 0)
        {
            _logger.LogWarning("No job postings found. Check the XPath of for the job cards");
            return new List<JobPosting>();
        }

        var postings = new List<JobPosting>();

        foreach (var card in cards)
        {
            try {
                // use xPath to pull info from cards into new job postings
            } catch
            {
                _logger.LogWarning("Failed to parse job card. Skipping");
            }
        }

        return postings;
    }
}