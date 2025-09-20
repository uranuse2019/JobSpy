import streamlit as st
import pandas as pd
from jobspy import scrape_jobs
from jobspy.model import Country

st.set_page_config(page_title="JobSpy Web App", layout="wide")

st.title("🔎 JobSpy Web Scraper")
st.write("Enter your job search criteria below and see the results from multiple job boards.")

# --- User Inputs in Sidebar ---
st.sidebar.header("Search Parameters")

# Job Titles
job_titles_str = st.sidebar.text_area(
    "Job Titles (one per line)", 
    "PMO Lead\nPMO Analyst\nPMO"
)
job_titles_to_search = [title.strip() for title in job_titles_str.split('\n') if title.strip()]

# --- Location and Country Selection ---

# Create a list of countries from the JobSpy model
country_names = sorted([
    country.value[0].split(',')[0].title() 
    for country in Country 
    if country not in (Country.US_CANADA, Country.WORLDWIDE)
])

selected_country = st.sidebar.selectbox(
    "Country",
    options=country_names,
    index=country_names.index("Uk") # Default to UK
)

location_placeholder = "City, State" if selected_country == "Usa" else "City"
location = st.sidebar.text_input("Location (optional)", "", placeholder=f"e.g., London or {location_placeholder}")

st.sidebar.subheader("Job Sites")

# ZipRecruiter is only available in US/Canada
is_ziprecruiter_available = selected_country in ["Usa", "Canada"]

site_options = {
    "Indeed": "indeed",
    "LinkedIn": "linkedin",
    "ZipRecruiter": "zip_recruiter",
    "Google": "google",
    "Glassdoor": "glassdoor",
    "Bayt": "bayt",
    "Naukri": "naukri",
    "BDJobs": "bdjobs"
}

sites = []
for label, site_name in site_options.items():
    if site_name == "zip_recruiter":
        # Disable ZipRecruiter if the country is not US or Canada
        if st.sidebar.checkbox(label, value=(label in ["Indeed", "LinkedIn", "Google"]), disabled=not is_ziprecruiter_available, help="Only available for USA and Canada"):
            sites.append(site_name)
    elif st.sidebar.checkbox(label, value=(label in ["Indeed", "LinkedIn", "Google"])):
        sites.append(site_name)

# Other Parameters
results_wanted = st.sidebar.slider("Results Wanted (per site)", 1, 100, 20)
hours_old = st.sidebar.slider("Hours Old (max)", 1, 720, 72)

# --- Main App Logic ---

if st.button("🚀 Search for Jobs"):
    if not job_titles_to_search:
        st.warning("Please enter at least one job title.")
    elif not sites:
        st.warning("Please select at least one job site.")
    else:
        st.session_state.jobs_df = pd.DataFrame() # Clear previous results
        all_jobs = []

        total_searches = len(job_titles_to_search)
        progress_bar = st.progress(0, text=f"Starting search for {total_searches} job title(s)...")

        for i, search_term in enumerate(job_titles_to_search):
            progress_text = f"Searching for '{search_term}' ({i + 1}/{total_searches})"
            progress_bar.progress(i / total_searches, text=progress_text)

            # Dynamically create google_search_term
            google_search = f'"{search_term}" jobs in {location}'

            jobs_df = scrape_jobs(
                site_name=sites,
                search_term=search_term,
                google_search_term=google_search,
                location=location,
                results_wanted=results_wanted,
                hours_old=hours_old,
                country_indeed=selected_country,
            )
            if not jobs_df.empty:
                jobs_df['search_term'] = search_term
                all_jobs.append(jobs_df)

        if all_jobs:
            progress_bar.progress(1.0, text="All searches complete! Compiling results...")
            combined_jobs_df = pd.concat(all_jobs, ignore_index=True)
            st.session_state.jobs_df = combined_jobs_df
        else:
            st.warning("No jobs found for the given criteria.")

# --- Display Results ---
if 'jobs_df' in st.session_state and not st.session_state.jobs_df.empty:
    total_jobs = len(st.session_state.jobs_df)
    st.success(f"Found a total of {total_jobs} jobs!")

    # Provide a download button for the full results first
    st.download_button(
        label="📥 Download All Results as CSV",
        data=st.session_state.jobs_df.to_csv(index=False).encode('utf-8'),
        file_name='jobs.csv',
        mime='text/csv',
    )

    all_jobs_df = st.session_state.jobs_df
    search_terms = all_jobs_df['search_term'].unique()

    for term in search_terms:
        term_df = all_jobs_df[all_jobs_df['search_term'] == term].copy()
        term_df.reset_index(drop=True, inplace=True) # Important for selection indexing

        with st.expander(f"📂 Results for '{term}' ({len(term_df)} jobs found)", expanded=True):
            col1, col2 = st.columns([1, 2])

            with col1:
                # Initialize session state for selected job for this term if not present
                if f'selected_job_index_{term}' not in st.session_state:
                    st.session_state[f'selected_job_index_{term}'] = None

                st.subheader("Job List")
                # Create a container with a fixed height and border for the job list
                with st.container(height=550, border=True):
                    for index, row in term_df.iterrows():
                        # Use a button for each job. The label includes title, company, and location.
                        button_label = f"**{row['title']}**\n\n*at {row['company']} in {row['location']}*"
                        if st.button(button_label, key=f"btn_{term}_{index}", use_container_width=True):
                            st.session_state[f'selected_job_index_{term}'] = index

            with col2:
                st.subheader("Job Details")
                selected_index = st.session_state.get(f'selected_job_index_{term}')

                if selected_index is not None:
                    selected_job = term_df.iloc[selected_index]

                    st.markdown(f"#### {selected_job['title']}")
                    st.markdown(f"**🏢 Company:** {selected_job['company']}")
                    st.markdown(f"**📍 Location:** {selected_job['location']}")
                    st.markdown(f"**🔗 Source:** {selected_job['site']}")
                    
                    # Use a more prominent button for applying
                    st.link_button("🚀 Apply Here on a New Tab", selected_job['job_url'], use_container_width=True, type="primary")

                    st.markdown("---")
                    st.markdown("##### Job Description")
                    st.markdown(f"<div style='height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; border-radius: 5px;'>{selected_job['description']}</div>", unsafe_allow_html=True)
                else:
                    st.info("Select a job from the list on the left to see its details.")