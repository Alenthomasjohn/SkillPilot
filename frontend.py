import streamlit as st
import requests
import hashlib
import json
import os

# Replace with your actual n8n webhook URL
N8N_WEBHOOK_URL = "https://alphy.app.n8n.cloud/webhook-test/job-course-recs"

# Users file path
USERS_FILE = "users.json"

def load_users_from_file():
    """Load users from JSON file, create empty file if doesn't exist"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # If file is corrupted, return empty dict
            return {}
    else:
        # Create empty file
        users = {}
        save_users_to_file(users)
        return users

def save_users_to_file(users_dict=None):
    """Save users dictionary to JSON file"""
    if users_dict is None:
        users_dict = st.session_state.users_db
    
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users_dict, f, indent=2)
        return True
    except IOError:
        return False

# Initialize users in session state if not exists
if 'users_db' not in st.session_state:
    st.session_state.users_db = load_users_from_file()

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(username, password):
    """Check if username and password are correct"""
    if username in st.session_state.users_db:
        user_data = st.session_state.users_db[username]
        if isinstance(user_data, dict):
            return user_data.get('password_hash') == hash_password(password)
        else:
            # Handle old format (just password hash)
            return user_data == hash_password(password)
    return False

def create_user(username, password, skills="", education="", interests=""):
    """Create a new user account with profile information"""
    if username in st.session_state.users_db:
        return False, "Username already exists"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    # Create user profile with all information
    user_profile = {
        "password_hash": hash_password(password),
        "skills": skills,
        "education": education,
        "interests": interests,
        "created_at": st.session_state.get('current_time', 'Unknown')
    }
    
    # Add user to session state
    st.session_state.users_db[username] = user_profile
    
    # Save to file
    if save_users_to_file():
        return True, "Account created successfully!"
    else:
        # Remove from session state if file save failed
        del st.session_state.users_db[username]
        return False, "Failed to save account. Please try again."

def get_user_profile(username):
    """Get user profile information"""
    if username in st.session_state.users_db:
        user_data = st.session_state.users_db[username]
        if isinstance(user_data, dict):
            return {
                "skills": user_data.get("skills", ""),
                "education": user_data.get("education", ""),
                "interests": user_data.get("interests", "")
            }
    return {"skills": "", "education": "", "interests": ""}

def auth_page():
    """Display login/signup page"""
    st.title("🔐 Authentication")
    
    # Tab selection
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login")
        st.write("Please log in to access the Job & Course Recommendation System")
        
        # Login form
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            login_button = st.form_submit_button("Login")
            
            if login_button:
                if check_password(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        # Demo credentials info
        if len(st.session_state.users_db) == 0:
            st.info("No existing users. Create your first account in the Sign Up tab!")
    
    with tab2:
        st.subheader("Create New Account")
        st.write("Sign up to get personalized job and course recommendations")
        
        # Signup form
        with st.form("signup_form"):
            new_username = st.text_input("Choose Username", key="signup_username")
            new_password = st.text_input("Choose Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
            
            st.write("**Optional: Add your profile information**")
            signup_skills = st.text_area("Skills (comma-separated)", placeholder="Python, Data Analysis, SQL", key="signup_skills")
            signup_education = st.text_input("Education", placeholder="B.Sc in Computer Science", key="signup_education")
            signup_interests = st.text_area("Interests (comma-separated)", placeholder="Machine Learning, AI, Cloud Computing", key="signup_interests")
            
            signup_button = st.form_submit_button("Create Account")
            
            if signup_button:
                if not new_username or not new_password:
                    st.error("Please fill in username and password")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    # Set current time for user creation
                    import datetime
                    st.session_state.current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    success, message = create_user(
                        new_username, 
                        new_password, 
                        signup_skills, 
                        signup_education, 
                        signup_interests
                    )
                    if success:
                        st.success(message)
                        st.info("You can now login with your new credentials!")
                    else:
                        st.error(message)

def logout():
    """Handle logout"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()

def main_app():
    """Main application after login"""
    # Logout button in sidebar
    with st.sidebar:
        st.write(f"👋 Welcome, {st.session_state.username}!")
        if st.button("Logout"):
            logout()
        
        # Show total registered users
        st.write(f"📊 Total users: {len(st.session_state.users_db)}")
    
    st.title("🎯 Job & Course Recommendation System")
    st.write("Fill in your profile to get personalized job and course suggestions.")

    # Get user's saved profile data
    user_profile = get_user_profile(st.session_state.username)

    # --- User Input Form ---
    with st.form("user_form"):
        name = st.text_input("Name", value=st.session_state.username)
        skills = st.text_area("Skills (comma-separated)", 
                             value=user_profile["skills"], 
                             placeholder="Python, Data Analysis, SQL")
        education = st.text_input("Education", 
                                 value=user_profile["education"], 
                                 placeholder="B.Sc in Computer Science")
        interests = st.text_area("Interests (comma-separated)", 
                                value=user_profile["interests"], 
                                placeholder="Machine Learning, AI, Cloud Computing")

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

# --- Main App Logic ---
st.set_page_config(page_title="Job & Course Recommender", layout="centered")

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None

# Show appropriate page based on authentication status
if not st.session_state.authenticated:
    auth_page()
else:
    main_app()
