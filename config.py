# config.py
SEARCH_CONFIG = {
    "keywords": [
        "data analyst",
        "senior data analyst",
        "business intelligence analyst"
    ],
    "locations": ["Toronto", "Remote", "Ontario"],
    "max_jobs_per_source": 50,
    "days_back": 1,           # only fetch last 24hrs on daily run
}

FILTERS = {
    "exclude_companies": [],   # add companies to ignore
    "require_salary": False,
    "remote_only": False,
}

SCHEDULE = {
    "run_time": "08:00",       # run every day at 8am
    "timezone": "America/Toronto"
}
# ```

# ---

## Requirements
# ```
# httpx
# beautifulsoup4
# sqlalchemy
# apscheduler
# tenacity
# python-dotenv
# loguru
# anthropic
# lxml