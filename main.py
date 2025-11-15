"""
main.py
-------

FastAPI application for the Resume Parser & Job‑Matching Portal.  This
application allows recruiters to upload resumes and job descriptions.  It
parses the uploaded documents to extract structured information (candidate
details and skills) and computes simple match scores between candidates and
job openings based on overlapping skills.  A dashboard view lists all
resumes, jobs and match scores.

Note: This implementation uses basic heuristics and is intended as a
proof‑of‑concept.  For production use, integrate a proper NLP library
(e.g. spaCy) and connect a database for persistent storage.
"""

import os
import re
import io
from typing import List, Dict, Tuple

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pdfminer.high_level import extract_text as pdf_extract_text
from PyPDF2 import PdfReader


app = FastAPI(title="Resume Parser & Job‑Matching Portal")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Load list of skills from file
def load_skill_set() -> List[str]:
    skills_file = os.path.join(os.path.dirname(__file__), "skills.txt")
    skills: List[str] = []
    try:
        with open(skills_file, "r", encoding="utf-8") as f:
            for line in f:
                skill = line.strip()
                if skill:
                    skills.append(skill.lower())
    except Exception:
        pass
    return skills

SKILLS_SET = load_skill_set()

# In‑memory storage for parsed resumes and jobs
candidates: List[Dict] = []
jobs: List[Dict] = []


def extract_text_from_file(file: UploadFile) -> str:
    """Extract raw text from an uploaded resume or job description file.

    Supports plain text and PDF formats.  Returns an empty string on failure.
    """
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    try:
        content = file.file.read()
    except Exception:
        return ""
    # Reset file pointer
    file.file.seek(0)
    if ext == ".pdf":
        try:
            # Use PyPDF2 as fallback if pdfminer fails
            reader = PdfReader(io.BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return text
        except Exception:
            try:
                return pdf_extract_text(io.BytesIO(content))
            except Exception:
                return ""
    else:
        # Assume plain text
        try:
            return content.decode("utf-8", errors="ignore")
        except Exception:
            return ""


def parse_resume(text: str) -> Dict[str, any]:
    """Parse a resume to extract candidate details and skills.

    Returns a dictionary with keys: name, email, phone, skills, experience.
    The implementation uses simple regex heuristics.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    name = lines[0] if lines else ""
    # Email
    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    email = email_match.group(0) if email_match else ""
    # Phone number (various formats)
    phone_match = re.search(r"(\+?\d{1,3}[\s.-]?)?(\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})", text)
    phone = phone_match.group(0) if phone_match else ""
    # Skills: look for skills in our list
    skills_found = set()
    lower_text = text.lower()
    for skill in SKILLS_SET:
        if re.search(r"\b" + re.escape(skill) + r"\b", lower_text):
            skills_found.add(skill.title())
    # Experience: naive extraction of the section after 'experience' or 'work experience'
    experience = ""
    exp_match = re.search(r"(?i)(experience|work experience)(.*)" , text, re.DOTALL)
    if exp_match:
        experience = exp_match.group(2).strip()
        # limit to first 500 characters for display
        experience = experience[:500]
    return {
        "name": name,
        "email": email,
        "phone": phone,
        "skills": sorted(list(skills_found)),
        "experience": experience,
    }


def parse_job_description(text: str) -> Dict[str, any]:
    """Parse a job description to extract the title and required skills."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = lines[0] if lines else "Untitled Job"
    lower_text = text.lower()
    required_skills = set()
    for skill in SKILLS_SET:
        if re.search(r"\b" + re.escape(skill) + r"\b", lower_text):
            required_skills.add(skill.title())
    return {
        "title": title,
        "skills_required": sorted(list(required_skills)),
        "description": text,
    }


def match_candidates(job: Dict[str, any]) -> List[Tuple[int, float]]:
    """Compute a match score between each candidate and the given job.

    The score is the fraction of required skills that the candidate possesses.  Returns
    a list of tuples `(candidate_id, score)` sorted by descending score.
    """
    matches: List[Tuple[int, float]] = []
    req_skills = set(job.get("skills_required", []))
    if not req_skills:
        return []
    for idx, candidate in enumerate(candidates):
        cand_skills = set(candidate.get("skills", []))
        if not cand_skills:
            score = 0.0
        else:
            intersect = req_skills.intersection(cand_skills)
            score = len(intersect) / len(req_skills)
        matches.append((idx, score))
    # Sort by score descending
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render the main dashboard page with forms and tables."""
    # Compute match results for each job
    job_matches: List[List[Tuple[str, float]]] = []  # list of lists: candidate name, score
    for job in jobs:
        matches = match_candidates(job)
        match_list: List[Tuple[str, float]] = []
        for cand_idx, score in matches:
            candidate = candidates[cand_idx]
            match_list.append((candidate["name"], score))
        job_matches.append(match_list)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "candidates": candidates,
            "jobs": jobs,
            "job_matches": job_matches,
        },
    )


@app.post("/upload_resume")
async def upload_resume(request: Request, file: UploadFile = File(...)):
    """Handle resume upload: parse and store candidate details."""
    if not file:
        return RedirectResponse("/", status_code=303)
    raw_text = extract_text_from_file(file)
    if not raw_text:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "error": "Failed to extract text from the uploaded resume.",
                "candidates": candidates,
                "jobs": jobs,
                "job_matches": [],
            },
            status_code=500,
        )
    candidate_info = parse_resume(raw_text)
    candidate_info["filename"] = file.filename
    candidates.append(candidate_info)
    return RedirectResponse("/", status_code=303)


@app.post("/upload_job")
async def upload_job(request: Request, file: UploadFile = File(...)):
    """Handle job description upload: parse and store job details, compute matches."""
    if not file:
        return RedirectResponse("/", status_code=303)
    raw_text = extract_text_from_file(file)
    if not raw_text:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "error": "Failed to extract text from the uploaded job description.",
                "candidates": candidates,
                "jobs": jobs,
                "job_matches": [],
            },
            status_code=500,
        )
    job_info = parse_job_description(raw_text)
    job_info["filename"] = file.filename
    jobs.append(job_info)
    return RedirectResponse("/", status_code=303)