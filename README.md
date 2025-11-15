# Resume Parser & Job‑Matching Portal

This repository contains a simple web application that demonstrates how to parse resumes and job descriptions, extract structured information such as skills and experience, and compute match scores between candidates and job openings.  The goal is to streamline recruiter workflows by organising unstructured text into searchable profiles and ranking candidates based on their alignment with job requirements.

## Features

1. **Resume upload and parsing**: Users can upload resume files (plain text or PDF).  A basic parser extracts the candidate’s name, email, phone number, skills and a description of their experience.  You can customise the parsing logic or integrate a more sophisticated NLP model such as spaCy.
2. **Job description upload**: Recruiters can upload job descriptions.  The parser extracts the job title and the list of required skills.
3. **Candidate–job matching**: When a new job is uploaded, the application computes a simple match score for each candidate based on the overlap between the candidate’s skills and the job’s required skills.  A ranked list of candidates is displayed for each job.
4. **Dashboard**: The home page shows tables of uploaded resumes, uploaded job descriptions and a matrix of match scores.  This allows recruiters to quickly see which candidates may be a good fit for each role.

## Setup

1. **Clone this repository** and change into its directory.
2. **Create a virtual environment** (optional but recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

   > **Optional:** If you wish to use spaCy for more advanced parsing, install it and download a language model:
   >
   > ```bash
   > pip install spacy
   > python -m spacy download en_core_web_sm
   > ```

4. **Run the server:**

   ```bash
   uvicorn main:app --reload
   ```

   Navigate to `http://127.0.0.1:8000/` in your browser.  You can upload resumes and job descriptions from the main page.

## Customisation

* **Parsing logic**: The functions `parse_resume()` and `parse_job_description()` in `main.py` contain simple heuristics based on regular expressions and a list of common skills.  For better results, integrate spaCy or another NLP library and update these functions accordingly.
* **Skills vocabulary**: The file `skills.txt` includes a short list of technology skills.  Edit this file to reflect the domains relevant to your recruitment needs.
* **Matching algorithm**: The match score is currently computed as the proportion of required skills that are found in the candidate’s skills list.  You can modify `match_candidates()` to incorporate experience, education or other factors.
* **Storage**: In this proof‑of‑concept the uploaded files and parsed data are stored in memory.  For production use, connect a database (e.g. SQLite, PostgreSQL) to persist resumes, jobs and match scores.

## License

This project is provided for educational purposes and does not come with any warranty.  Feel free to modify and extend it to suit your own applications.
