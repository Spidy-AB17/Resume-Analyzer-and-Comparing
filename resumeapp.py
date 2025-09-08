# resume_app.py
import streamlit as st
import matplotlib.pyplot as plt
from resumeanalyzer import (
    extract_text_from_pdf,
    load_skills,
    find_skills,
    detect_sections,
    score_resume,
)

st.set_page_config(page_title="Resume Analyzer", layout="wide")

st.title("📄 Resume Analyzer")

uploaded_file = st.file_uploader("Upload your Resume (PDF)", type=["pdf"])

if uploaded_file is not None:
    # Save uploaded file temporarily
    with open("uploaded_resume.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    # --- Extract resume text ---
    resume_text = extract_text_from_pdf("uploaded_resume.pdf")

    # --- Skills analysis ---
    all_skills = load_skills()
    found_skills = find_skills(resume_text, all_skills)

    # --- Sections analysis ---
    present_sections, sections_map = detect_sections(resume_text)

    # --- Scoring ---
    scores = score_resume(found_skills, [], sections_map, all_skills)

    # --- UI Layout ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("✅ Skills Found")
        st.write(found_skills)

        st.subheader("📌 Sections Present")
        st.write(present_sections)

    with col2:
        st.subheader("📊 Resume Score")
        st.metric(label="Final Score", value=f"{scores['final_score']} / 100")
        st.write(f"Skills Coverage: {scores['skills_ratio']*100:.1f}%")
        st.write(f"Sections Coverage: {scores['sections_ratio']*100:.1f}%")

        # --- Chart: Matched vs Missing Skills ---
        matched = len(found_skills)
        missing = len(all_skills) - matched
        fig, ax = plt.subplots()
        ax.bar(["Matched", "Missing"], [matched, missing], color=["green", "red"])
        ax.set_ylabel("Count")
        ax.set_title("Skill Match Overview")
        st.pyplot(fig)

    # --- Suggestions ---
    st.subheader("💡 Suggestions to Improve Resume")
    missing_sections = [k for k, v in sections_map.items() if not v]
    if missing_sections:
        st.warning(f"Consider adding these sections: {missing_sections}")
    else:
        st.success("Your resume already has all the key sections! ✅")

    if missing > 0:
        st.info(f"You may want to add more skills. Missing {missing} from the default list.")
    else:
        st.success("All key skills detected in your resume! 🚀")
