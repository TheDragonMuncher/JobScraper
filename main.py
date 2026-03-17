from scrapers import linkedin
from database import db
from database import models

def main():
    job_postings = linkedin.run_scrape()

    database = db.Database()
    if database._migrated == False:
        database._run_migrations()
    
    inserted_count = db.QueryBuilder("job_postings").insert_many(database, job_postings)

    database.close()