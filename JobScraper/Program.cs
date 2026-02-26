using JobScraper.Data;
using JobScraper.Repositories;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Npgsql;

var host = Host.CreateDefaultBuilder(args).ConfigureServices((context, services) =>
{
    // create data source for connecting with postgres server
    var dataSource = new NpgsqlDataSourceBuilder(context.Configuration.GetConnectionString("Postgres")
        ?? "Host=localhost;Port=5433;Database=JobPostings;Username=postgres;Password=Th3Pr0gr@mm3r!")
        .Build();
    
    services.AddSingleton(dataSource);

    // apply data source to dbcontext options
    services.AddDbContext<AppDbContext>(options => 
        options.UseNpgsql(dataSource));
    
    // this section will need duplicating for every scraper I make. 
    // add the http client to each scraper service (Indeed, ...)
    services.AddHttpClient<IndeedScraperService>(client =>
    {
        client.DefaultRequestHeaders.Add("User-Agent","Mozilla/5.0 (compatible; JobScrapper/1.0)");
        client.Timeout = TimeSpan.FromSeconds(30);
    });

    services.AddScoped<JobRepository>();
})
// add logging in the console 
.ConfigureLogging(logging =>
{
    logging.ClearProviders();
    logging.AddConsole();
})
.Build();

using (var scope = host.Services.CreateScope())
{
    var scraper   = scope.ServiceProvider.GetRequiredService<ScraperService>();
    var repo      = scope.ServiceProvider.GetRequiredService<JobRepository>();
    var logger    = scope.ServiceProvider.GetRequiredService<ILogger<Program>>();

    // the url contains filters for ontario, remote, junior software developer, full time and/or coop/intern
    const string indeedUrl = "https://ca.indeed.com/jobs?q=junior+software+developer&l=Ontario&sc=0kf%3Aattr%28CF3CP%7CVDTG7%252COR%29%3B&from=searchOnDesktopSerp&vjk=f56171ec461148e8";

    logger.LogInformation("Fetching {Url}", indeedUrl);
    var jobs = await scraper.FetchAsync(indeedUrl);
    logger.LogInformation("Found {Count} job postings", jobs.Count);

    logger.LogInformation("Inserting into database...");
    var inserted = await repo.GetJobPostingsAsync(jobs);
    logger.LogInformation("Done");
}

return 0;