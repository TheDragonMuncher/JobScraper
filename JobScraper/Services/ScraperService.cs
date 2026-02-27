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
    const string JobCardXPath = "//div[contains(@class, 'cardOutline')]";
    const string PostingLinkXPath = ".//h2[contains(@class, 'jobTitle')]/a";
    // const string SourceIdXPath = ".//";
    const string TitleXPath = ".//h1[contains(@class, 'jobsearch-JobInfoHeader-title')]/span";
    const string CompanyXPath = ".//div[@data-company-name='true']/span/a";
    const string LocationXPath = ".//div[@data-testid='inlineHeader-companyLocation']/div";
    const string SalaryXPath = ".//div[@id='salaryInfoAndJobType']/span";
    const string DescriptionXPath = ".//div[@id='jobDescriptionText']";

    public ScraperService(HttpClient http, ILogger<ScraperService> logger, string url)
    {
        _http = http;
        _logger = logger;
        _targetUrl = url;
    }

    public async Task<List<JobPosting>> ScrapeSite(CancellationToken ct = default)
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
            try 
            {
                var postingLink = await _http.GetStringAsync(
                    card.SelectSingleNode(PostingLinkXPath)?.GetAttributeValue("href","")
                );

                var postingHtml = await _http.GetStringAsync(postingLink);
                var postingDoc = new HtmlDocument();
                postingDoc.LoadHtml(postingHtml);
                
                try
                {
                    postings.Add(new JobPosting
                    {
                        SourceId = Guid.NewGuid().ToString(),
                        Title = postingDoc.DocumentNode.SelectSingleNode(TitleXPath)?.InnerHtml.Trim() ?? "Unknown",
                        Company = postingDoc.DocumentNode.SelectSingleNode(CompanyXPath)?.InnerHtml.Trim(),
                        Location = postingDoc.DocumentNode.SelectSingleNode(LocationXPath)?.InnerHtml.Trim(),
                        Salary = postingDoc.DocumentNode.SelectSingleNode(SalaryXPath)?.InnerHtml.Trim(),
                        Description = postingDoc.DocumentNode.SelectSingleNode(DescriptionXPath)?.ToString(),
                        Url = postingLink,
                        ScrapedAt = DateTime.UtcNow
                    });
                } catch
                {
                    _logger.LogWarning("Failed to parse job full posting. Check X Paths");
                }
            } catch
            {
                _logger.LogWarning("Failed to parse job card. Skipping");
            }
        }

        return postings;
    }
}