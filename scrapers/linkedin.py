from jobspy import scrape_jobs
from config import SEARCH_CONFIG

def run_scrape():
    cfg = SEARCH_CONFIG
    keywords = cfg["keywords"]
    locations = cfg["locations"]
    max_jobs = cfg["max_jobs"]
    job_type = cfg["job_type"]

    jobs_df = scrape_jobs(
        site_name="linkedin",
        search_term=keywords,
        location=locations,
        results_wanted=max_jobs,
        hours_old=24,
        job_type=job_type,
        linkedin_fetch_description=True
    )

    return jobs_df