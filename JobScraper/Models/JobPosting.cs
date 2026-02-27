using System.Text.Json.Serialization;

namespace JobScraper.Models;

public class JobPosting
{
    public int Id {get;set;}
    public string SourceId {get;set;} = string.Empty;
    public string? Title {get;set;} = string.Empty;
    public string? Company {get;set;} = string.Empty;
    public string? Location {get;set;} = string.Empty;
    public string? Salary {get;set;} = string.Empty;
    public string? Description {get;set;} = string.Empty;
    public DateTime? DatePosted {get;set;}
    public string Url {get;set;} = string.Empty;
    public DateTime ScrapedAt {get;set;} = DateTime.UtcNow;
}