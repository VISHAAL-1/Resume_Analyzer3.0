import streamlit as st
import requests
import json
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import time
import streamlit as st
st.write("Hello, Streamlit is running!")

# --- Page Config & Custom CSS ---
st.set_page_config(layout="wide", page_title="Resume Checker", page_icon="📄")

# Define color palettes
user_colors = {
    "primary": "#FF4B4B",
    "secondary": "#FF8C00",
    "background": "#121212",
    "text": "#FFFFFF",
    "button_bg": "#333333",
    "hover": "#FF4B4B"
}
admin_colors = {
    "primary": "#36F500",
    "secondary": "#36F5C0",
    "background": "#0A1929",
    "text": "#FFFFFF",
    "button_bg": "#0A2840",
    "hover": "#36F500"
}

# Load custom CSS based on role
def apply_custom_css(role):
    colors = admin_colors if role == "admin" else user_colors
    
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {colors['background']};
            color: {colors['text']};
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: {colors['primary']};
        }}
        .stButton > button {{
            color: {colors['text']};
            background-color: {colors['button_bg']};
            border-radius: 5px;
            border: 1px solid {colors['primary']};
            padding: 10px 20px;
            font-weight: normal;
            transition: all 0.3s ease-in-out;
        }}
        .stButton > button:hover {{
            background-color: {colors['hover']};
            color: {colors['background']};
            border-color: {colors['secondary']};
            box-shadow: 0px 0px 10px {colors['hover']};
        }}
        /* Main container for initial screen to center content */
        .main-container {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            width: 100%;
            animation: fadeIn 1s ease-in-out;
        }}
        /* Fade in animation for transitions */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        /* New CSS to center align table content */
        .stTable table th, .stTable table td {{
            text-align: center;
        }}
        .stTable {{
            animation: fadeIn 1s ease-in-out;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# --- Constants & State Management ---
API_BASE = "http://localhost:8000"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.admin_page = "main"
    st.session_state.view_job_title = None
    st.session_state.view_evaluation_id = None
    st.session_state.user_page = "main"
    st.session_state.user_view_job_title = None
    st.session_state.app_state = "login_select"

def login_form():
    with st.form("login_form"):
        st.subheader("🔐 Log In")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In")
        if submitted:
            try:
                resp = requests.post(f"{API_BASE}/login/", data={"username": username, "password": password})
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = data.get("role")
                    with st.spinner("Logging in..."):
                        time.sleep(1)
                    st.success(f"Welcome back, {username}! 👋")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to backend API. Make sure it's running.")

def signup_form():
    with st.form("signup_form"):
        st.subheader("📝 Sign Up as a User")
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        email = st.text_input("Email")
        phone_number = st.text_input("Phone Number")
        city = st.text_input("City")
        state = st.text_input("State")
        signup_submitted = st.form_submit_button("Create Account")
        if signup_submitted:
            if not new_username or not new_password:
                st.error("Username and password are required.")
            else:
                try:
                    resp = requests.post(f"{API_BASE}/signup/", data={"username": new_username, "password": new_password, "email": email, "phone_number": phone_number, "city": city, "state": state})
                    if resp.status_code == 200:
                        st.success("Account created successfully! Please log in.")
                        st.session_state.app_state = "user_login"
                        st.rerun()
                    else:
                        st.error(resp.json().get("detail", "Failed to create account."))
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to backend API. Make sure it's running.")
                    
def main_login_select_page():
    st.title("📄 Resume Relevance Checker")
    st.write("---")
    st.header("Make your resume stand out.")
    st.write("Intelligently evaluate your resume against job descriptions using AI to get actionable feedback and improve your chances.")
    st.write("---")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("Sign in as User", use_container_width=True):
            st.session_state.app_state = "user_login"
            st.rerun()
    with col2:
        if st.button("Sign in as Recruiter", use_container_width=True):
            st.session_state.app_state = "admin_login"
            st.rerun()
    with col3:
        if st.button("New? Sign up as a User", use_container_width=True):
            st.session_state.app_state = "signup"
            st.rerun()

def main_login_form_page():
    if st.session_state.app_state == "user_login":
        st.header("User Login")
        login_form()
        if st.button("⬅️ Back"):
            st.session_state.app_state = "login_select"
            st.rerun()
    elif st.session_state.app_state == "admin_login":
        st.header("Recruiter Login")
        login_form()
        if st.button("⬅️ Back"):
            st.session_state.app_state = "login_select"
            st.rerun()
    elif st.session_state.app_state == "signup":
        signup_form()
        if st.button("⬅️ Back"):
            st.session_state.app_state = "login_select"
            st.rerun()

# --- Admin Portal ---
def show_admin_portal():
    apply_custom_css("admin")
    with st.sidebar:
        st.success(f"Logged in as {st.session_state.username} ({st.session_state.role})")
        st.button("📊 View All Submissions", on_click=lambda: st.session_state.update(admin_page="submissions", view_job_title=None, view_evaluation_id=None))
        st.button("➕ Create a New Job", on_click=lambda: st.session_state.update(admin_page="create_job"))
        st.button("Logout", on_click=lambda: st.session_state.update(logged_in=False, username="", role="", admin_page="main", app_state="login_select"))

    if st.session_state.admin_page == "main":
        st.markdown("<div class='main-container'>", unsafe_allow_html=True)
        st.title("Admin Dashboard")
        st.write("Welcome, Admin. Please select an action.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 View All Submissions", use_container_width=True):
                st.session_state.admin_page = "submissions"
                st.rerun()
        with col2:
            if st.button("➕ Create a New Job", use_container_width=True):
                st.session_state.admin_page = "create_job"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        if st.session_state.admin_page == "create_job":
            st.header("➕ Create New Job Description")
            with st.form("job_form"):
                title = st.text_input("Job Title")
                must_have = st.text_input("Must-have skills (comma separated)", help="e.g. python, sql, ml")
                good_to_have = st.text_input("Good-to-have skills (comma separated)")
                qualifications = st.text_area("Qualifications / Notes (optional)")
                branch_office = st.text_input("Branch Office")
                job_state = st.text_input("State")
                submitted = st.form_submit_button("Create Job")
                if submitted:
                    params = {"username": st.session_state.username}
                    resp = requests.post(f"{API_BASE}/jobs/", params=params, data={"title": title, "must_have": must_have, "good_to_have": good_to_have, "qualifications": qualifications, "branch_office": branch_office, "state": job_state})
                    if resp.status_code == 200:
                        st.success("Job created: " + str(resp.json()))
                    else:
                        st.error(f"Failed: {resp.status_code} - {resp.text}")

        elif st.session_state.admin_page == "submissions":
            st.header("📊 All Candidate Submissions by Job")
            try:
                params = {"username": st.session_state.username}
                resp = requests.get(f"{API_BASE}/evaluations/", params=params)
                
                if resp.status_code != 200:
                    st.error(f"Failed to fetch evaluations: {resp.status_code} - {resp.text}")
                    return
                
                evs = resp.json()
                if not evs:
                    st.info("No evaluations found.")
                    return
                
                df = pd.DataFrame(evs)
                job_titles = df['job_title'].unique()
                st.subheader("Select a Job to View Submissions")
                for job_title in job_titles:
                    st.button(f"View Submissions for {job_title}", key=f"view_job_{job_title}", on_click=lambda jt=job_title: st.session_state.update(admin_page="view_job_submissions", view_job_title=jt))
            except Exception as e:
                st.error(f"Failed to fetch evaluations: {e}")

        elif st.session_state.admin_page == "view_job_submissions":
            st.header(f"Submissions for Job: {st.session_state.view_job_title}")
            st.button("⬅️ Back to All Jobs", on_click=lambda: st.session_state.update(admin_page="submissions", view_job_title=None, view_evaluation_id=None))
            
            try:
                params = {"username": st.session_state.username}
                resp = requests.get(f"{API_BASE}/evaluations/", params=params)

                if resp.status_code != 200:
                    st.error(f"Failed to fetch evaluations: {resp.status_code} - {resp.text}")
                    return

                all_evals = resp.json()
                job_evals = [ev for ev in all_evals if ev.get('job_title') == st.session_state.view_job_title]
                
                if not job_evals:
                    st.info("No submissions found for this job.")
                    return
                
                # Filter by verdict and location
                verdicts = ['All', 'High', 'Medium', 'Low']
                verdict_filter = st.selectbox("Filter by Verdict", verdicts)

                locations = ["Doesn't Matter", "Same State", "Same City"]
                location_filter = st.selectbox("Filter by Place", locations)
                
                filtered_evals = job_evals
                if verdict_filter != 'All':
                    filtered_evals = [ev for ev in filtered_evals if ev['verdict'] == verdict_filter]

                job_details_resp = requests.get(f"{API_BASE}/jobs/").json()
                job_details = next((j for j in job_details_resp if j['title'] == st.session_state.view_job_title), None)

                if location_filter == "Same State" and job_details and job_details.get('state'):
                    filtered_evals = [ev for ev in filtered_evals if ev.get('candidate_state') and ev['candidate_state'].lower() == job_details.get('state', '').lower()]
                elif location_filter == "Same City" and job_details and job_details.get('branch_office'):
                    filtered_evals = [ev for ev in filtered_evals if ev.get('candidate_city') and ev['candidate_city'].lower() == job_details.get('branch_office', '').lower()]

                st.subheader("Submissions List")
                if not filtered_evals:
                    st.info("No submissions match the selected filter.")
                else:
                    for ev in filtered_evals:
                        with st.container(border=True):
                            col1, col2, col3, col4 = st.columns([0.4, 0.2, 0.2, 0.2])
                            col1.markdown(f"**Candidate:** {ev['candidate_name']}")
                            col2.markdown(f"**Score:** {ev['score']}%")
                            col3.markdown(f"**Verdict:** {ev['verdict']}")
                            with col4:
                                st.button("View Details", key=f"view_admin_detail_{ev['evaluation_id']}", on_click=lambda eval_id=ev['evaluation_id']: st.session_state.update(admin_page="view_admin_submission_details", view_evaluation_id=eval_id))
            except Exception as e:
                st.error(f"Failed to fetch candidate submissions: {e}")

        elif st.session_state.admin_page == "view_admin_submission_details":
            st.header("Submission Details")
            st.button("⬅️ Back to Job Submissions", on_click=lambda: st.session_state.update(admin_page="view_job_submissions", view_evaluation_id=None))
            
            try:
                params = {"username": st.session_state.username}
                resp = requests.get(f"{API_BASE}/evaluations/", params=params)

                if resp.status_code != 200:
                    st.error(f"Failed to fetch submissions: {resp.status_code} - {resp.text}")
                    return

                all_evals = resp.json()
                selected_eval = next((ev for ev in all_evals if ev.get('evaluation_id') == st.session_state.view_evaluation_id), None)
                
                if not selected_eval:
                    st.error("Submission not found.")
                    return
                
                job_evals = [ev for ev in all_evals if ev.get('job_title') == st.session_state.view_job_title]
                total_submissions = len(job_evals)
                current_index = job_evals.index(selected_eval) if selected_eval in job_evals else 0
                
                nav_cols = st.columns([1, 6, 1])
                with nav_cols[0]:
                    if st.button("Previous", disabled=(current_index == 0)):
                        st.session_state.view_evaluation_id = job_evals[current_index - 1]['evaluation_id']
                        st.rerun()
                with nav_cols[2]:
                    if st.button("Next", disabled=(current_index == total_submissions - 1)):
                        st.session_state.view_evaluation_id = job_evals[current_index + 1]['evaluation_id']
                        st.rerun()
                st.markdown(f"**Submission {current_index + 1} of {total_submissions} for {selected_eval['candidate_name']}**")

                st.subheader(f"Job: {selected_eval['job_title']}")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="Overall Score", value=f"{selected_eval.get('score', 0.0)}%")
                with col2:
                    verdict = selected_eval.get('verdict', 'N/A')
                    verdict_color = "red" if verdict == "Low" else "orange" if verdict == "Medium" else "green"
                    st.markdown(f"**Verdict:** <span style='color:{verdict_color}; font-size: 24px; font-weight: bold;'>{verdict}</span>", unsafe_allow_html=True)
                
                score_fig = go.Figure(go.Indicator(
                    mode="gauge",
                    gauge={'shape': "angular",
                           'bar': {'color': "lightgreen" if selected_eval.get('score', 0) > 75 else "orange" if selected_eval.get('score', 0) > 50 else "red"},
                           'axis': {'range': [0, 100], 'tickvals': [0, 50, 75, 100]},
                           'steps': [{'range': [0, 50], 'color': "lightpink"},
                                     {'range': [50, 75], 'color': "lightgray"},
                                     {'range': [75, 100], 'color': "lightgreen"}],
                           'threshold': {'line': {'color': 'black', 'width': 4}, 'thickness': 0.75, 'value': selected_eval.get('score', 0)}},
                    value=selected_eval.get('score', 0),
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Overall Score"}
                ))
                score_fig.update_layout(height=400)
                st.plotly_chart(score_fig, use_container_width=True)

                st.markdown("---")
                st.subheader("LLM Analysis")
                st.markdown(f"**LLM Summary:** {selected_eval.get('summary', 'N/A')}")
                st.markdown(f"**Suggestions for Improvement:**")
                st.write(selected_eval.get('feedback', 'N/A'))
                
                st.markdown("---")
                st.subheader("Score Breakdown")
                hard_score = selected_eval.get('hard_score', 0.0)
                semantic_score = selected_eval.get('semantic_score', 0.0)
                df_scores = pd.DataFrame({"Metric": ["Hard Match Score", "Semantic Match Score"], "Score": [hard_score, semantic_score]})
                st.bar_chart(df_scores, x="Metric", y="Score", use_container_width=True)
            except Exception as e:
                st.error(f"Failed to fetch submission details: {e}")

# --- User Portal ---
def show_user_portal():
    apply_custom_css("user")
    with st.sidebar:
        st.success(f"Logged in as {st.session_state.username} ({st.session_state.role})")
        st.button("📄 Upload Resume", on_click=lambda: st.session_state.update(user_page="upload"))
        st.button("📂 My Submissions", on_click=lambda: st.session_state.update(user_page="my_submissions", user_view_job_title=None, view_evaluation_id=None))
        st.button("👤 My Profile", on_click=lambda: st.session_state.update(user_page="my_profile"))
        st.button("Logout", on_click=lambda: st.session_state.update(logged_in=False, username="", role="", user_page="main", app_state="login_select"))
            
    if st.session_state.user_page == "main":
        st.markdown("<div class='main-container'>", unsafe_allow_html=True)
        st.title("User Dashboard")
        st.write("Welcome, User. Please select an action.")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📄 Upload Resume", use_container_width=True):
                st.session_state.user_page = "upload"
                st.rerun()
        with col2:
            if st.button("📂 My Submissions", use_container_width=True):
                st.session_state.user_page = "my_submissions"
                st.session_state.user_view_job_title = None
                st.rerun()
        with col3:
            if st.button("👤 My Profile", use_container_width=True):
                st.session_state.user_page = "my_profile"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
    elif st.session_state.user_page == "upload":
        st.header("📄 Upload Your Resume")
        try:
            jobs = requests.get(f"{API_BASE}/jobs/").json()
        except Exception:
            jobs = []
        if jobs:
            job_titles = {j['title']: j['id'] for j in jobs}
            selected_job_title = st.selectbox("Select a Job to Apply for", list(job_titles.keys()))
            job_id = job_titles[selected_job_title]
        else:
            st.info("No jobs found. Please contact an admin.")
            return

        with st.form("resume_form"):
            name = st.text_input("Your Name", value=st.session_state.username)
            email = st.text_input("Your Email")
            uploaded_file = st.file_uploader("Upload resume (pdf/docx)", type=["pdf", "docx"], help="Limit 2MB per file")
            submit_resume = st.form_submit_button("Upload & Evaluate")
            if submit_resume:
                if not uploaded_file:
                    st.error("Please upload a resume file")
                else:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                    data = {"job_id": str(job_id), "name": name or "", "email": email or ""}
                    try:
                        with st.spinner("Analyzing your resume..."):
                            resp = requests.post(f"{API_BASE}/upload_resume/", data=data, files=files, timeout=120)
                            if resp.status_code == 200:
                                st.success("Evaluation complete!")
                                st.session_state.user_page = "my_submissions"
                                st.rerun()
                            else:
                                st.error(f"Error: {resp.status_code} - {resp.text}")
                    except Exception as e:
                        st.error(f"Request failed: {e}")

    elif st.session_state.user_page == "my_submissions":
        st.header("📂 My Submissions")
        try:
            params = {"username": st.session_state.username} 
            resp = requests.get(f"{API_BASE}/my_evaluations/", params=params)
            if resp.status_code == 200:
                my_evals = resp.json()
            else:
                st.error(f"Failed to fetch submissions: {resp.status_code} - {resp.text}")
                return
            if not my_evals:
                st.info("You have no submissions yet. Upload a resume to get started!")
                return
            
            df = pd.DataFrame(my_evals)
            job_titles = df['job_title'].unique()
            st.subheader("Select a Job to View Submissions")
            for job_title in job_titles:
                st.button(f"View Submissions for {job_title}", key=f"user_view_job_{job_title}", on_click=lambda jt=job_title: st.session_state.update(user_page="view_user_job_submissions", user_view_job_title=jt))
        except Exception as e:
            st.error(f"Failed to fetch submissions: {e}")

    elif st.session_state.user_page == "view_user_job_submissions":
        st.header(f"Submissions for Job: {st.session_state.user_view_job_title}")
        st.button("⬅️ Back to My Submissions", on_click=lambda: st.session_state.update(user_page="my_submissions", user_view_job_title=None, view_evaluation_id=None))

        try:
            params = {"username": st.session_state.username}
            resp = requests.get(f"{API_BASE}/my_evaluations/", params=params)
            
            if resp.status_code != 200:
                st.error(f"Failed to fetch submissions: {resp.status_code} - {resp.text}")
                return

            my_evals = resp.json()
            job_evals = [ev for ev in my_evals if ev.get('job_title') == st.session_state.user_view_job_title]

            if not job_evals:
                st.info("No submissions found for this job.")
                return
            
            st.subheader("Submissions List")
            for ev in job_evals:
                with st.container(border=True):
                    st.markdown(f"**Score:** {ev['score']}% - **Verdict:** {ev['verdict']}")
                    st.button("View Details", key=f"view_user_details_{ev['evaluation_id']}", on_click=lambda eval_id=ev['evaluation_id']: st.session_state.update(user_page="view_single_submission", view_evaluation_id=eval_id))
        except Exception as e:
            st.error(f"Failed to fetch submission details: {e}")

    elif st.session_state.user_page == "view_single_submission":
        st.header("Submission Details")
        st.button("⬅️ Back to My Submissions", on_click=lambda: st.session_state.update(user_page="view_user_job_submissions", user_view_job_title=st.session_state.user_view_job_title, view_evaluation_id=None))
        try:
            params = {"username": st.session_state.username}
            resp = requests.get(f"{API_BASE}/my_evaluations/", params=params)
            if resp.status_code == 200:
                my_evals = resp.json()
                selected_eval = next((ev for ev in my_evals if ev.get('evaluation_id') == st.session_state.view_evaluation_id), None)
            else:
                st.error(f"Failed to fetch submissions: {resp.status_code} - {resp.text}")
                return
            if not selected_eval:
                st.error("Submission not found.")
                return
            st.subheader(f"Job: {selected_eval['job_title']}")
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="Overall Score", value=f"{selected_eval['score']}%")
            with col2:
                verdict_color = "red" if selected_eval['verdict'] == "Low" else "orange" if selected_eval['verdict'] == "Medium" else "green"
                st.markdown(f"**Verdict:** <span style='color:{verdict_color}; font-size: 24px; font-weight: bold;'>{selected_eval['verdict']}</span>", unsafe_allow_html=True)
            score_fig = go.Figure(go.Indicator(
                mode="gauge",
                gauge={'shape': "angular",
                       'bar': {'color': "lightgreen" if selected_eval['score'] > 75 else "orange" if selected_eval['score'] > 50 else "red"},
                       'axis': {'range': [0, 100], 'tickvals': [0, 50, 75, 100]},
                       'steps': [{'range': [0, 50], 'color': "lightpink"},
                                 {'range': [50, 75], 'color': "lightgray"},
                                 {'range': [75, 100], 'color': "lightgreen"}],
                       'threshold': {'line': {'color': 'black', 'width': 4}, 'thickness': 0.75, 'value': selected_eval['score']}},
                value=selected_eval['score'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Your Score"}
            ))
            score_fig.update_layout(height=400)
            st.plotly_chart(score_fig, use_container_width=True)
            st.markdown("---")
            st.subheader("LLM Analysis")
            st.markdown(f"**LLM Summary:** {selected_eval['summary']}")
            st.markdown(f"**Suggestions for Improvement:**")
            st.write(selected_eval['feedback'])
            st.markdown("---")
            st.subheader("Score Breakdown")
            hard_score = selected_eval.get('hard_score', 0.0)
            semantic_score = selected_eval.get('semantic_score', 0.0)
            df_scores = pd.DataFrame({"Metric": ["Hard Match Score", "Semantic Match Score"], "Score": [hard_score, semantic_score]})
            st.bar_chart(df_scores, x="Metric", y="Score", use_container_width=True)
        except Exception as e:
            st.error(f"Failed to fetch submission details: {e}")

    elif st.session_state.user_page == "my_profile":
        st.header("👤 My Profile")
        try:
            params = {"username": st.session_state.username}
            resp = requests.get(f"{API_BASE}/profile/", params=params)
            if resp.status_code == 200:
                profile_data = resp.json()
                st.subheader("Personal Information")
                st.write(f"**Username:** {profile_data.get('username', 'N/A')}")
                st.write(f"**Email:** {profile_data.get('email', 'N/A')}")
                st.write(f"**Phone Number:** {profile_data.get('phone_number', 'N/A')}")
                st.write(f"**City:** {profile_data.get('city', 'N/A')}")
                st.write(f"**State:** {profile_data.get('state', 'N/A')}")
                
                st.subheader("My Submissions")
                submissions_resp = requests.get(f"{API_BASE}/my_evaluations/", params=params)
                if submissions_resp.status_code == 200:
                    my_evals = submissions_resp.json()
                    if my_evals:
                        df_submissions = pd.DataFrame(my_evals)
                        # Corrected: Safely handle missing 'created_at' column
                        columns_to_display = ['job_title', 'score', 'verdict']
                        if 'created_at' in df_submissions.columns:
                            columns_to_display.append('created_at')

                        df_display = df_submissions[columns_to_display].rename(columns={'job_title': 'Job', 'score': 'Score', 'verdict': 'Verdict', 'created_at': 'Date Submitted'})
                        st.table(df_display)
                    else:
                        st.info("You have not submitted any resumes yet.")
                else:
                    st.error("Failed to fetch your submissions.")
            else:
                st.error("Failed to fetch profile data.")
        except Exception as e:
            st.error(f"An error occurred: {e}")

# --- Main Logic ---
if not st.session_state.logged_in:
    if st.session_state.app_state == "login_select":
        st.markdown("<div class='main-container'>", unsafe_allow_html=True)
        main_login_select_page()
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='main-container'>", unsafe_allow_html=True)
        main_login_form_page()
        st.markdown("</div>", unsafe_allow_html=True)
else:
    st.sidebar.success(f"Logged in as {st.session_state.username} ({st.session_state.role})")
    
    if st.session_state.role == "admin":
        show_admin_portal()
    elif st.session_state.role == "user":
        show_user_portal()
    else:

        st.warning("Invalid role. Please contact support.")
