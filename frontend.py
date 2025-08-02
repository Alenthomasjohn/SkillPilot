import streamlit as st
import requests

# Replace with your actual n8n webhook URL
N8N_WEBHOOK_URL = "https://your-n8n-instance/webhook/job-course-recs"

st.set_page_config(page_title="Job & Course Recommender", layout="centered")

st.title("🎯 Job & Course Recommendation System")
st.write("Fill in your profile to get personalized job and course suggestions.")

# --- User Input Form ---
with st.form("user_form"):
    name = st.text_input("Name")
    skills = st.text_area("Skills (comma-separated)", placeholder="Python, Data Analysis, SQL")
    education = st.text_input("Education", placeholder="B.Sc in Computer Science")
    interests = st.text_area("Interests (comma-separated)", placeholder="Machine Learning, AI, Cloud Computing")

    submitted = st.form_submit_button("Get Recommendations")

# --- On Submit ---
if submitted:
    if not name or not skills or not education or not interests:
        st.warning("Please fill in all fields.")
    else:
        # Show loading spinner
        with st.spinner("Fetching your recommendations..."):
            payload = {
                "name": name,
                "skills": [s.strip() for s in skills.split(",")],
                "education": education,
                "interests": [i.strip() for i in interests.split(",")]
            }

            try:
                response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()

                    st.success("Here are your recommendations:")

                    # --- Summary ---
                    if "summary" in data:
                        st.markdown(f"**Summary:** {data['summary']}")

                    # --- Jobs Table ---
                    if "jobs" in data and data["jobs"]:
                        st.subheader("💼 Job Recommendations")
                        for job in data["jobs"]:
                            st.markdown(f"**{job['title']}** at *{job['company']}* ({job['location']})")
                            st.markdown(f"[Apply Here]({job['link']})")
                            st.markdown("---")

                    # --- Courses Table ---
                    if "courses" in data and data["courses"]:
                        st.subheader("📚 Course Recommendations")
                        for course in data["courses"]:
                            st.markdown(f"**{course['title']}** — {course['platform']}")
                            st.markdown(f"[View Course]({course['link']})")
                            st.markdown("---")

                else:
                    st.error(f"Error: Received status code {response.status_code}")

            except requests.exceptions.RequestException as e:
                st.error(f"Request failed: {e}")
