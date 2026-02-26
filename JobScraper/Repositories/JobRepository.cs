using JobScraper.Data;
using JobScraper.Models;
using Microsoft.EntityFrameworkCore;

namespace JobScraper.Repositories;

public class JobRepository
{
    readonly AppDbContext _context;
    public JobRepository(AppDbContext dbContext)
    {
        _context = dbContext;
    }

    public async Task<JobPosting> AddJobPostingAsync(JobPosting posting)
    {
        _context.JobPostings.Add(posting);
        await _context.SaveChangesAsync();
        return posting;
    }
    public async Task<List<JobPosting>> AddJobPostingAsync(List<JobPosting> postings)
    {
        _context.JobPostings.AddRange(postings);
        await _context.SaveChangesAsync();
        return postings;
    }

    public async Task<List<JobPosting>> GetJobPostingsAsync()
    {
        var postings = await _context.JobPostings.ToListAsync();
        if (postings == null) 
            return new List<JobPosting>();
        return postings;
    }

    public async Task<JobPosting?> GetJobPostingByIdAsync(int id)
    {
        var posting = await _context.JobPostings.FindAsync(id);
        if (posting == null)
            return null;
        return posting;
    }

    public async Task<JobPosting?> UpdateJobPostingAsync(JobPosting newPosting)
    {
        var oldPosting = await _context.JobPostings.FindAsync(newPosting.Id);
        if (oldPosting == null)
            return null;

        oldPosting.Title = newPosting.Title;
        oldPosting.Company = newPosting.Company;
        oldPosting.Location = newPosting.Location;
        oldPosting.Salary = newPosting.Salary;
        oldPosting.Description = newPosting.Description;
        oldPosting.DatePosted = newPosting.DatePosted;
        oldPosting.Url = newPosting.Url;

        _context.JobPostings.Update(oldPosting);
        await _context.SaveChangesAsync();

        return newPosting;
    }

    public async Task<bool> DeleteJobPostingAsync(int id)
    {
        var posting = await _context.JobPostings.FindAsync(id);
        if (posting == null)
            return false;
        _context.JobPostings.Remove(posting);
        await _context.SaveChangesAsync();
        return true;
    }
}