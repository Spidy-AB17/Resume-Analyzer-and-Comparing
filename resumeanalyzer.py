# resume_analyzer.py
import os
import sys
import argparse
import re
import json
import pandas as pd
import matplotlib.pyplot as plt

try:
    import pdfplumber
except Exception as e:
    print("Missing pdfplumber. Install with: pip install pdfplumber")
    raise e


# ---------- Helpers ----------
def extract_text_from_pdf(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def load_skills(skills_file=None):
    # If a skills file provided, load it (one skill per line)
    if skills_file and os.path.exists(skills_file):
        with open(skills_file, "r", encoding="utf-8") as f:
            items = [line.strip().lower() for line in f if line.strip()]
        return items
    # Default skill list (expand as you like)
    return [
        "python", "java", "c++", "c", "sql", "html", "css", "javascript",
        "react", "node", "django", "flask", "machine learning",
        "deep learning", "nlp", "data science", "git", "linux", "excel",
        "pandas", "numpy", "tensorflow", "pytorch", "rest api",
        "mongodb", "mysql", "docker", "kubernetes", "aws", "azure"
    ]


def find_skills(text, skills_list):
    text = text.lower()
    found = []
    for skill in skills_list:
        # Use boundaries that handle non-word chars like C++
        pattern = r'(?<!\w)' + re.escape(skill) + r'(?!\w)'
        if re.search(pattern, text):
            found.append(skill)
    return sorted(found)


def detect_sections(text):
    text = text.lower()
    sections = {
        "contact": bool(re.search(r'(contact|phone|email|linkedin|github)', text)),
        "summary/objective": bool(re.search(r'(career objective|summary|objective|profile)', text)),
        "education": bool(re.search(r'\beducation\b', text)),
        "experience": bool(re.search(r'\b(experience|work experience|professional experience)\b', text)),
        "projects": bool(re.search(r'\b(projects?|personal projects)\b', text)),
        "skills": bool(re.search(r'\b(skills|technical skills|core competencies)\b', text))
    }
    present = [k for k, v in sections.items() if v]
    return present, sections


def extract_job_skills(job_file, skills_list):
    if not job_file:
        return []
    if not os.path.exists(job_file):
        print(f"Warning: job file not found: {job_file}")
        return []
    with open(job_file, "r", encoding="utf-8") as f:
        jd = f.read().lower()
    job_skills = [s for s in skills_list if re.search(r'(?<!\w)'+re.escape(s)+r'(?!\w)', jd)]
    return job_skills


def score_resume(found_skills, job_skills, sections_map, all_skills):
    # Skills ratio:
    if job_skills:
        # If JD provided, match to the JD's required skills
        matched_against_job = len([s for s in found_skills if s in job_skills])
        skills_ratio = matched_against_job / len(job_skills) if job_skills else 0.0
    else:
        # Otherwise measure coverage against the general skills list
        skills_ratio = len(found_skills) / len(all_skills) if all_skills else 0.0

    # Sections ratio:
    total_sections = len(sections_map)
    present_sections = sum(1 for v in sections_map.values() if v)
    sections_ratio = present_sections / total_sections if total_sections else 0.0

    # Weighted score:
    skills_weight = 0.7
    sections_weight = 0.3
    final_score = (skills_ratio * skills_weight + sections_ratio * sections_weight) * 100
    return {
        "skills_ratio": round(skills_ratio, 3),
        "sections_ratio": round(sections_ratio, 3),
        "final_score": int(round(final_score))
    }


def save_results(results, out_prefix="resume_analysis"):
    # JSON
    json_path = f"{out_prefix}.json"
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(results, jf, indent=2, ensure_ascii=False)

    # CSV for skill presence
    skill_rows = []
    for s, present in results["skill_presence"].items():
        skill_rows.append({"skill": s, "present": present})
    df = pd.DataFrame(skill_rows)
    csv_path = f"{out_prefix}_skills.csv"
    df.to_csv(csv_path, index=False)

    return json_path, csv_path


def plot_matched_missing(found, required, out_name="matched_vs_missing.png"):
    # If required list provided, compare against that; else use union of found+some default
    if required:
        matched = len([s for s in found if s in required])
        missing = len(required) - matched
        labels = ["matched", "missing"]
        values = [matched, max(0, missing)]
    else:
        # Compare found vs not found from found + some representative total
        values = [len(found), 0]  # simple chart if no job_skills
        labels = ["found", "others"]

    plt.figure(figsize=(6, 4))
    plt.bar(labels, values)
    plt.title("Skill match overview")
    plt.tight_layout()
    plt.savefig(out_name)
    plt.close()
    return out_name


# ---------- Main ----------
def main():
    parser = argparse.ArgumentParser(description="Resume Analyzer (PDF)")
    parser.add_argument("--file", "-f", help="Path to resume PDF", required=False)
    parser.add_argument("--job", "-j", help="Optional: path to job description txt", required=False)
    parser.add_argument("--skills", "-s", help="Optional: path to custom skills list (one per line)", required=False)
    parser.add_argument("--out", help="Output prefix (default: resume_analysis)", default="resume_analysis")
    args = parser.parse_args()

    # file input
    file_path = args.file
    if not file_path:
        file_path = input("Enter path to resume PDF: ").strip()

    try:
        resume_text = extract_text_from_pdf(file_path)
    except FileNotFoundError as e:
        print(str(e))
        sys.exit(1)

    all_skills = load_skills(args.skills)
    found_sk = find_skills(resume_text, all_skills)
    present_sections, sections_map = detect_sections(resume_text)
    job_sk = extract_job_skills(args.job, all_skills) if args.job else []

    # skill presence map for CSV/JSON
    skill_presence = {s: (s in found_sk) for s in all_skills}

    # missing skill suggestions vs job
    missing_vs_job = [s for s in job_sk if s not in found_sk] if job_sk else []

    # score
    scores = score_resume(found_sk, job_sk, sections_map, all_skills)

    results = {
        "file_searched": file_path,
        "found_skills": found_sk,
        "skill_count": len(found_sk),
        "total_skills_in_list": len(all_skills),
        "job_skills_detected": job_sk,
        "missing_skills_against_job": missing_vs_job,
        "sections_present": present_sections,
        "sections_map": sections_map,
        "skill_presence": skill_presence,
        "scores": scores,
        "resume_preview": resume_text[:2000]  # store first 2k chars
    }

    json_path, csv_path = save_results(results, out_prefix=args.out)
    chart_path = plot_matched_missing(found_sk, job_sk, out_name=f"{args.out}_matched_vs_missing.png")

    # Print summary to console
    print("\n----- Analysis Summary -----")
    print(f"File: {file_path}")
    print(f"Found skills ({len(found_sk)}): {found_sk}")
    if job_sk:
        print(f"Job skills required ({len(job_sk)}): {job_sk}")
        print(f"Missing vs job ({len(missing_vs_job)}): {missing_vs_job}")
    print(f"Sections present: {present_sections}")
    print(f"Score: {scores['final_score']} / 100")
    print(f"Saved JSON: {json_path}")
    print(f"Saved CSV (skills): {csv_path}")
    print(f"Saved chart: {chart_path}")

    print("\nSuggestions:")
    if missing_vs_job:
        print(" - Add these job-specific skills to increase matching:", missing_vs_job)
    else:
        print(" - No job file or no missing job skills detected. Consider adding more domain skills if relevant.")
    # Section suggestions:
    needed_sections = [k for k, v in sections_map.items() if not v]
    if needed_sections:
        print(" - Consider adding these sections:", needed_sections)
    else:
        print(" - Resume already has the basic sections detected.")

    print("\nDone.")

if __name__ == "__main__":
    main()

