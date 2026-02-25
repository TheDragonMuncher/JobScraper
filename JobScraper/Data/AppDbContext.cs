using JobScraper.Models;
using Microsoft.EntityFrameworkCore;

namespace JobScraper.Data;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base (options){}

    public DbSet<JobPosting> JobPostings {get;set;}

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.Entity<JobPosting>(entity =>
        {
            entity.HasKey(j => j.Id);
            entity.Property(j => j.SourceId).IsRequired();
            entity.Property(j => j.Title).IsRequired();
        });
    }
}