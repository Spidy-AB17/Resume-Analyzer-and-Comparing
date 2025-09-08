# resume_dashboard.py
import streamlit as st
import pdfplumber
import re
import pandas as pd
import matplotlib.pyplot as plt

def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def find_skills(text, skills_list):
    text = text.lower()
    found = []
    for skill in skills_list:
        pattern = r'(?<!\w)' + re.escape(skill) + r'(?!\w)'
        if re.search(pattern, text):
            found.append(skill)
    return found

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
    return [k for k, v in sections.items() if v]


skills_list = [
    "python", "java", "c++", "c", "sql", "html", "css", "javascript",
    "react", "node", "django", "flask", "machine learning",
    "deep learning", "nlp", "data science", "git", "linux", "excel",
    "pandas", "numpy", "tensorflow", "pytorch", "rest api",
    "mongodb", "mysql", "docker", "kubernetes", "aws", "azure"
]


st.title("📊 Resume Analyzer Dashboard")

uploaded_files = st.file_uploader("Upload multiple resumes (PDF)", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    results = []

    for file in uploaded_files:
        resume_text = extract_text_from_pdf(file)
        found_skills = find_skills(resume_text, skills_list)
        sections = detect_sections(resume_text)

        results.append({
            "filename": file.name,
            "skills_found": len(found_skills),
            "sections_found": len(sections),
            "skills": found_skills,
            "sections": sections
        })

    df = pd.DataFrame(results)

    st.subheader("📌 Resume Comparison Table")
    st.dataframe(df[["filename", "skills_found", "sections_found"]])

    # 📊 Skills comparison chart
    st.subheader("📈 Skills Found per Resume")
    fig, ax = plt.subplots()
    df.plot(kind="bar", x="filename", y="skills_found", ax=ax, legend=False)
    plt.ylabel("Number of Skills")
    st.pyplot(fig)

    # 📊 Sections comparison chart
    st.subheader("📈 Sections Present per Resume")
    fig2, ax2 = plt.subplots()
    df.plot(kind="bar", x="filename", y="sections_found", ax=ax2, color="orange", legend=False)
    plt.ylabel("Number of Sections")
    st.pyplot(fig2)

    st.subheader("✅ Detailed Skills Extracted")
    for r in results:
        st.markdown(f"**{r['filename']}**")
        st.write("Skills:", r["skills"])
        st.write("Sections:", r["sections"])
