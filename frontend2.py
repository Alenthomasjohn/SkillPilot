import streamlit as st
import requests
import hashlib
import json
import os
import gspread
from google.oauth2.service_account import Credentials

def get_gsheet_client(json_key_path):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_file(json_key_path, scopes=scopes)
    return gspread.authorize(credentials)

# Constants
GSHEET_JSON_KEY = "sheets-key.json"
USER_SHEET_NAME = "Sheet1"
COURSE_SHEET_NAME = "course_recommendations"
SPREADSHEET_ID = "1bHT8Z_BQqfPOKG6IlGYUeZR6QtN-TQkp5ZVERx4sBBU"
N8N_WEBHOOK_URL = "https://alphy.app.n8n.cloud/webhook-test/job-course-recs"
USERS_FILE = "users.json"

# -------------------- Local Storage ---------------------
def load_users_from_file():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    else:
        users = {}
        save_users_to_file(users)
        return users

def save_users_to_file(users_dict=None):
    if users_dict is None:
        users_dict = st.session_state.users_db
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users_dict, f, indent=2)
        return True
    except IOError:
        return False

# -------------------- Google Sheets ---------------------
def update_user_to_gsheet(username, gmail, skills, education, interests):
    try:
        print("Connecting to Google Sheet...")
        client = get_gsheet_client(GSHEET_JSON_KEY)
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(USER_SHEET_NAME)

        records = sheet.get_all_records()
        usernames = [row['username'] for row in records]
        user_data = [username, gmail, skills, education, interests]

        if username in usernames:
            idx = usernames.index(username) + 2
            sheet.update(f"A{idx}:E{idx}", [user_data])
            print(f"Updated row {idx}")
        else:
            sheet.append_row(user_data)
            print("Appended new user row.")

        return True
    except Exception as e:
        st.error("❌ Google Sheets update failed.")
        st.exception(e)  # 🔥 This will show full traceback
        print(f"[ERROR] update_user_to_gsheet: {e}")
        return False

def save_courses_to_gsheet(username, courses):
    try:
        client = get_gsheet_client(GSHEET_JSON_KEY)
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(COURSE_SHEET_NAME)

        for course in courses:
            row = [username, course["title"], course["platform"], course["link"]]
            sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Failed to save course recommendations: {e}")
        return False

# -------------------- User Auth ---------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(username, password):
    if username in st.session_state.users_db:
        user_data = st.session_state.users_db[username]
        return user_data.get('password_hash') == hash_password(password)
    return False

def create_user(username, password, gmail="", skills="", education="", interests=""):
    if username in st.session_state.users_db:
        return False, "Username already exists"
    if len(username) < 3 or len(password) < 6:
        return False, "Username or password too short"
    user_profile = {
        "password_hash": hash_password(password),
        "gmail": gmail,
        "skills": skills,
        "education": education,
        "interests": interests
    }
    st.session_state.users_db[username] = user_profile
    if save_users_to_file():
        return True, "Account created successfully!"
    else:
        del st.session_state.users_db[username]
        return False, "Failed to save account"

def get_user_profile(username):
    return st.session_state.users_db.get(username, {
        "gmail": "", "skills": "", "education": "", "interests": ""
    })

def auth_page():
    st.title("🔐 Authentication")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login")
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            login_btn = st.form_submit_button("Login")
            if login_btn:
                if check_password(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    with tab2:
        st.subheader("Sign Up")
        with st.form("signup_form"):
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            gmail = st.text_input("Gmail", placeholder="you@example.com")
            skills = st.text_area("Skills (comma-separated)")
            education = st.text_input("Education")
            interests = st.text_area("Interests (comma-separated)")
            create_btn = st.form_submit_button("Create Account")

            if create_btn:
                if new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    success, msg = create_user(
                        new_username, new_password, gmail, skills, education, interests
                    )
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)

def logout():
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()

def main_app():
    with st.sidebar:
        st.write(f"👋 Welcome, {st.session_state.username}!")
        if st.button("Logout"):
            logout()
        st.write(f"📊 Total users: {len(st.session_state.users_db)}")

    st.title("🎯 Job & Course Recommendation System")
    st.write("Get personalized job and course suggestions.")

    user_profile = get_user_profile(st.session_state.username)

    with st.form("user_form"):
        name = st.text_input("Name", value=st.session_state.username, disabled=True)
        gmail = st.text_input("Gmail", value=user_profile.get("gmail", ""), placeholder="you@example.com")
        skills = st.text_area("Skills (comma-separated)", value=user_profile.get("skills", ""))
        education = st.text_input("Education", value=user_profile.get("education", ""))
        interests = st.text_area("Interests (comma-separated)", value=user_profile.get("interests", ""))

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Get Recommendations")
        with col2:
            save_btn = st.form_submit_button("Save Profile")

    if save_btn:
        if not gmail or not skills or not education or not interests:
            st.warning("All fields (except name) must be filled to save.")
        else:
            st.session_state.users_db[st.session_state.username].update({
                "gmail": gmail,
                "skills": skills,
                "education": education,
                "interests": interests
            })

            if save_users_to_file():
                updated = update_user_to_gsheet(
                    username=name,
                    gmail=gmail,
                    skills=skills,
                    education=education,
                    interests=interests
                )
                if updated:
                    st.success("✅ Profile saved and synced to Google Sheets!")
                else:
                    st.warning("⚠️ Profile saved locally, but failed to sync with Google Sheets.")
            else:
                st.error("❌ Failed to save profile locally.")

    if submitted:
        if not name or not gmail or not skills or not education or not interests:
            st.warning("Please fill in all fields.")
        else:
            with st.spinner("Fetching your recommendations..."):
                payload = {
                    "name": name,
                    "gmail": gmail,
                    "skills": [s.strip() for s in skills.split(",")],
                    "education": education,
                    "interests": [i.strip() for i in interests.split(",")]
                }

                try:
                    response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=60)

                    if response.status_code == 200:
                        data = response.json()
                        st.success("Here are your recommendations:")

                        if "summary" in data:
                            st.markdown(f"**Summary:** {data['summary']}")

                        if "jobs" in data and data["jobs"]:
                            st.subheader("💼 Job Recommendations")
                            for job in data["jobs"]:
                                st.markdown(f"**{job.get('title', 'N/A')}** at *{job.get('company', 'Unknown')}* ({job.get('location', 'Unknown')})")

                                link = job.get('link') or (
    job.get('apply_options', [{}])[0].get('link')
)
                                if link:
                                    st.markdown(f"[Apply Here]({link})")
                                else:
                                    st.markdown("_No application link available._")

                                st.markdown("---")

                        if "courses" in data and data["courses"]:
                            st.subheader("📚 Course Recommendations")
                            for course in data["courses"]:
                                st.markdown(f"**{course.get('title', 'Untitled Course')}** — {course.get('platform', 'Unknown Platform')}")

                                st.markdown(f"[View Course]({course['link']})")
                                st.markdown("---")

                            # 👇 Save courses to Google Sheet
                            save_courses_to_gsheet(name, data["courses"])

                    else:
                        st.error(f"Error: Received status code {response.status_code}")

                except requests.exceptions.RequestException as e:
                    st.error(f"Request failed: {e}")

# --- Initialization ---
st.set_page_config(page_title="Job & Course Recommender", layout="centered")
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'users_db' not in st.session_state:
    st.session_state.users_db = load_users_from_file()

if not st.session_state.authenticated:
    auth_page()
else:
    main_app()
