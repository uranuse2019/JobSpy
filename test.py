import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from jobspy import scrape_jobs

def search_for_title(search_term: str) -> pd.DataFrame:
    """Calls scrape_jobs for a given search term and returns the results."""
    print(f"Searching for: {search_term}...")
    # Dynamically create google_search_term based on the main search term
    google_search = f'"{search_term}" jobs near London, UK since yesterday'

    jobs_df = scrape_jobs(
        site_name=["indeed", "linkedin", "google"],  # zip_recruiter is US/CA only
        search_term=search_term,
        google_search_term=google_search,
        location="London, UK",
        results_wanted=20,
        hours_old=72,
        country_indeed='UK',
        # linkedin_fetch_description=True # gets more info such as description, direct job url (slower)
        # proxies=["208.195.175.46:65095", "208.195.175.45:65095", "localhost"],
    )

    # Add a column to track which search term this job came from
    if not jobs_df.empty:
        jobs_df['search_term'] = search_term

    print(f"Found {len(jobs_df)} jobs for: {search_term}")
    return jobs_df

if __name__ == "__main__":
    # Add all the job titles you want to search for in this list
    job_titles_to_search = ["PMO Lead", "PMO Analyst", "PMO"]

    all_jobs = []

    with ThreadPoolExecutor() as executor:
        # Submit all search tasks to the executor
        future_to_title = {executor.submit(search_for_title, title): title for title in job_titles_to_search}

        for future in as_completed(future_to_title):
            all_jobs.append(future.result())

    # Combine all the results into a single DataFrame
    combined_jobs_df = pd.concat(all_jobs, ignore_index=True)

    print(f"\nFound a total of {len(combined_jobs_df)} jobs across all searches.")
    print(combined_jobs_df.head())
    combined_jobs_df.to_excel("jobs.xlsx", index=False)
    print("\nSaved all jobs to jobs.xlsx")