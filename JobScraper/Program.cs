using JobScraper.Data;
using JobScraper.Services;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

var config = new ConfigurationBuilder()
    .AddJsonFile("appsettings.json", optional: false)
    .AddEnvironmentVariables()
    .Build();

using var logFactory = LoggerFactory.Create(b => b.AddConsole());

var connectionString = config.GetConnectionString("Postgres")
    ?? throw new InvalidOperationException("Missing Postgres connection string");

var http = new HttpClient();
http.DefaultRequestHeaders.UserAgent.ParseAdd("JobScraper/1.0");

var scraper    = new ScraperService(http, logFactory.CreateLogger<ScraperService>());
var repository = new JobRepository(connectionString, logFactory.CreateLogger<JobRepository>());
var logger     = logFactory.CreateLogger("Program");

try
{
    await repository.EnsureSchemaAsync();
    var postings = await scraper.ScrapeAsync();
    logger.LogInformation("Parsed {Count} postings", postings.Count);
    var saved = await repository.UpsertAsync(postings);
    logger.LogInformation("Upserted {Count} rows into job_postings", saved);
}
catch (Exception ex)
{
    logger.LogCritical(ex, "Scraper failed");
    return 1;
}

return 0;