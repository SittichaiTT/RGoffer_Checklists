import streamlit as st
import pandas as pd
import json
import datetime
import firebase_admin
from firebase_admin import credentials, auth, firestore
import uuid # For generating unique user IDs for anonymous login

# --- Configuration ---
# Theme Colors (Adjusted for minimalist, high-contrast look)
THEME_COLORS = {
    "primary_bg": "#F8F8F8",  # Very light grey background
    "secondary_bg": "#FFFFFF",  # Pure white for content blocks
    "text_dark": "#212121",   # Very dark grey/almost black for main text
    "text_light": "#757575",  # Medium grey for secondary text
    "button_primary": "#4285F4",  # Google Blue
    "button_primary_hover": "#3367D6", # Darker Google Blue on hover
    "button_secondary": "#BDBDBD", # Light neutral grey
    "button_secondary_hover": "#9E9E9E", # Darker neutral grey on hover
    "button_disabled": "#E0E0E0", # Light grey for disabled buttons
    "progress_yellow": "#FBBC04", # Google Yellow
    "progress_blue": "#4285F4",   # Consistent with primary button
    "progress_green": "#34A853",  # Google Green
    "border_color": "#E0E0E0", # Light grey border
    "placeholder_text": "#9E9E9E", # Medium grey for placeholders
    "dropdown_fg": "#212121", # Dark text for dropdowns
    "dropdown_hover": "#F5F5F5", # Very light hover for dropdowns
    "sub_group_underline": "#4285F4" # Consistent with primary color
}

# Business Unit selection options constant
BUSINESS_UNIT_OPTIONS = ["", "MEAPAC", "La Maison", "ENA", "RIXOS", "Fairmont & Raffles", "China"]

# Hardcoded Checklist Data (Python dictionary)
HARDCODED_CHECKLIST_DATA = {
    "Step 1": {
        "Check the form": [
            "Business Unit",
            "What is Booking Period (BOOPER ABSOLUTE)?",
            "Ticket Number ?",
            "Offer Name TK",
            "Offer Name Commercial",
            "Is there any BOOPER Relative request?",
            "Stay Period provided?",
            "Rate level code confirmed?",
            "TK (Check if existing please follow 'CLEAN UP')",
            "Eligible with point - Must clarify only earnpoint or use point",
            "Central use",
            "Flexibility",
            "Exclude TK?",
            "Meal Plan",
            "MINSTA MAXSTA",
            "CANPOL",
            "GUAPOL",
            "Other informative Sale condition . PKGS, AHRES1…",
            "Meal products = combinded or included or index meal products aswell?",
            "Substitution Tars Key Code?",
            "Referencial TK",
            "If any unclear qustion please reach out to requester",
            "Check if WDR or MS, if MS hotel included please awere Rate Family in Basisweb",
            "Check reference rate and MODIFY in the loading form",
            "Check What is PMS interface"
        ],
        "Check OTAs/ GDS part": [
            "Is this offer included OTAs?",
            "Rate level code ? OTAs",
            "Special to be awere -0% on Expedia ? (for promotagging purpose)",
            "Check the requester is require specific contacts people to CC when sendign DD to?",
            "ALL OTAs for All hotels or only some OTAs?",
            "All GDS?",
            "If yes on GDS is there specific RAC code required?"
        ],
        "This must be done first day": [
            "Open request to the ENA team before start loading",
            "Open request to the American team before start loading",
            "Open the ticket for create rate in Ddege",
            "Double check reference rate before start using automation",
            "Changed TK Validity = No limit to No limit both Direct and OTAs"
        ]
    },
    "Step 2": {
        "Clean up Using Extraction": [
            "CANPOL",
            "GUAPOL",
            "BOOPER",
            "MINSTA, MAXSTA, MINAB, MAXAB, MINTHR, MAXTHR",
            "HRL",
            "HTK",
            "INDEX",
            "Pricing (STATIC)"
        ],
        "Clean up": [
            "Is TK already used in another offer?",
            "Has previous offer been ended or deactivated?",
            "Check and clean up any saleconfition in DBMDIS",
            "Review all extractions and delete if possible"
        ]
    },
    "Step 3": {
        "Loading Day Direct Automation": [
            "Using Automation Offer",
            "Selected correct fuction, Create, Add hotel to offer, or Renewal",
            "Put the require TK,",
            "Make sure correct Qualification",
            "Card holder",
            "Booking wit point",
            "Extended name, Marketing Name",
            "Flexibility",
            "Substitution Tars Key Code?",
            "Put rate Level",
            "Pricing file CSV, Index or Static",
            "Sale condition Ensure MINSTA, MAXSTA, BOOPER, CANPOL, GUAPOL",
            "Check the Error if any must fix now"
        ],
        "Loading After Automation": [
            "Reload everything according to the form such as HRL, Index, and other specific",
            "Modify HTK with adding Referencial TK",
            "Modify Rate Level combunded MBREAK, no generic if Meal is discounted",
            "If Meal plan discount must index Meal plan",
            "APOL load all hotels ?",
            "Add MINAB if require incaes using BOOPER absolute already",
            "Chenck :R_Matrix RL-TK setting per channels (If any specific channels needed such as GDS)"
        ],
        "Loading day OTAS Pre-requistes": [
            "Make sure check all hotel has taxes set up and associtaed to room type otherwise can't pull DD",
            "OTAs H-RL ",
            "External Mapping for PMS ",
            "Indexation/Pricing loading are done"
        ],
        "Loading day OTAS Automation": [
            "Choose the correct fuction Add hotel to offer , Create, or Renewal OTAS?",
            "Make sure to clean up RL index, rate, Sale condition, if reusing the existing",
            "Put Direct TK",
            "GDS, CTO and OTAs selection Click here for the list of eligible GDS, CTO and OTA",
            "Put indirect RL both OTAs and CTOs (FLxxx & FLMxxxx)",
            "I want to send Datadump manually to distributors",
            "Then put Email",
            "Select hotel and add the parameter, it will copy hotel list participating from Direct TKs",
            "Then check all detail before confirm"
        ],
        "Loading After OTAs Automation": [
            "Make sure HTK Validity = Stay date period only (Please Hold and only change before live OTAS date)",
            "Make sure to put BOOPER Absolute now",
            "Advance OTAs push schedule as soon as possible",
            "Many OTAS partner will have FPLOS error if put BOOPER in TK level (DBMDis)",
            "Many OTAS partner will have MINSTA in TK level (DBMDis)"
        ],
        "GDS": [
            "Apply RAC for each public rate for 4 GDS in DBMDIs"
        ]
    },
    "Step 4": {
        "Distribution to OTAS": [
            "Generate Email for each partner",
            "Promo tagging require on OTAS?",
            "Check if any attched missing remuneration in GES",
            "Expedia make sure to fill up the blank, Expedia ID, Payment model, Stanalone or package",
            "EX Daily File Done?",
            "AG Daily File Done?",
            "BK API Done?"
        ]
    },
    "Step 5": {
        "Final check": [
            "Please make sure to attatch correct Absolute BOOPER in all TKs direct and indirect",
            "Please review the final indexation, Booper, MINSTA CLOARR and HTK Validity",
            "Call test booking with in Data Admin team",
            "Test 4 GDS Bookign and keep screenshot"
        ],
        "Final Check Direct Landing Page?": [
            "Landing page? If Yes, both Accor Plus and Main offer must be Qualify or not must ask requester to test"
        ],
        "Upload": [
            "Upload the Excel online link for OTAS Tracking Status",
            "Upload Hotel lists",
            "Upload TARSKEYS lists"
        ]
    },
    "Step 6": {
        "After Offer Expiration": [
            "Schedule the clean up on calendar ",
            "Make sure to clean up when offer expire date",
            "Pricing deleteion",
            "Put CLOARR then push ARI",
            "Change TK validity to 20491231 to 20491231"
        ]
    }
}

MONTH_NAMES = ["All Months", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

# --- Firebase Initialization ---
# This function initializes Firebase Admin SDK. It should only be called once.
@st.cache_resource
def initialize_firebase():
    try:
        # Load Firebase credentials from Streamlit secrets
        firebase_credentials_info = json.loads(st.secrets["firebase_credentials"])
        cred = credentials.Certificate(firebase_credentials_info)
        firebase_admin.initialize_app(cred)
        st.success("Firebase initialized successfully!")
        return firestore.client()
    except Exception as e:
        st.error(f"Error initializing Firebase: {e}")
        st.info("Please ensure your Firebase service account credentials are correctly configured in `.streamlit/secrets.toml`.")
        return None

db = initialize_firebase()

# --- Authentication Functions ---
def login_user(email, password):
    try:
        user = auth.get_user_by_email(email)
        # In a real app, you would verify password here.
        # Firebase Admin SDK does not directly verify passwords for security reasons.
        # For a Streamlit app, you might use a client-side Firebase SDK or
        # a custom backend to handle password authentication securely.
        # For this example, we'll assume if user_by_email is found, it's a valid login.
        # THIS IS NOT SECURE FOR PRODUCTION. For production, use Firebase client SDK or custom auth.
        st.session_state.user_id = user.uid
        st.session_state.user_email = user.email
        st.session_state.logged_in = True
        log_activity(user.uid, user.email, "Logged in")
        st.success(f"Logged in as {user.email}")
        st.rerun()
    except Exception as e:
        st.error(f"Login failed: {e}. Please check your email and password.")

def logout_user():
    if st.session_state.get('logged_in'):
        log_activity(st.session_state.user_id, st.session_state.user_email, "Logged out")
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_email = None
    st.info("Logged out successfully.")
    st.rerun()

# --- Firestore Data Operations ---
def get_user_projects_collection_ref(user_id):
    """Returns the Firestore collection reference for a user's projects."""
    if db is None:
        return None
    app_id = st.secrets.get("app_id", "default-app-id") # Get app_id from secrets or use default
    return db.collection(f"artifacts/{app_id}/users/{user_id}/projects")

def get_activity_logs_collection_ref():
    """Returns the Firestore collection reference for activity logs."""
    if db is None:
        return None
    app_id = st.secrets.get("app_id", "default-app-id") # Get app_id from secrets or use default
    return db.collection(f"artifacts/{app_id}/public/activity_logs")

def load_projects_from_firestore(user_id):
    """Loads projects from Firestore for the given user."""
    projects_ref = get_user_projects_collection_ref(user_id)
    if projects_ref is None:
        return pd.DataFrame(columns=["user_id", "project_name", "progress", "summary", "checklist_data"])
    
    try:
        docs = projects_ref.stream()
        projects_list = []
        for doc in docs:
            project_data = doc.to_dict()
            project_data['id'] = doc.id # Store Firestore document ID
            projects_list.append(project_data)
        df = pd.DataFrame(projects_list)
        st.success(f"Successfully loaded {len(df)} projects from Firestore.")
        return df
    except Exception as e:
        st.error(f"Error loading projects from Firestore: {e}")
        return pd.DataFrame(columns=["user_id", "project_name", "progress", "summary", "checklist_data"])

def save_project_to_firestore(user_id, project_name, progress, summary, checklist_data):
    """Saves or updates a project in Firestore."""
    projects_ref = get_user_projects_collection_ref(user_id)
    if projects_ref is None:
        st.error("Firestore not initialized. Cannot save project.")
        return

    try:
        # Check if project exists for this user
        existing_doc = projects_ref.where("project_name", "==", project_name).limit(1).get()
        
        project_data = {
            "user_id": user_id,
            "project_name": project_name,
            "progress": progress,
            "summary": summary,
            "checklist_data": json.dumps(checklist_data), # Store checklist_data as JSON string
            "last_updated": datetime.datetime.now()
        }

        if existing_doc:
            doc_id = existing_doc[0].id
            projects_ref.document(doc_id).update(project_data)
            st.success(f"Project '{project_name}' updated successfully!")
            log_activity(user_id, st.session_state.user_email, f"Updated project '{project_name}'")
        else:
            projects_ref.add(project_data)
            st.success(f"Project '{project_name}' created successfully!")
            log_activity(user_id, st.session_state.user_email, f"Created new project '{project_name}'")
    except Exception as e:
        st.error(f"Error saving project to Firestore: {e}")

def delete_project_from_firestore(user_id, project_name):
    """Deletes a project from Firestore."""
    projects_ref = get_user_projects_collection_ref(user_id)
    if projects_ref is None:
        st.error("Firestore not initialized. Cannot delete project.")
        return

    try:
        existing_doc = projects_ref.where("project_name", "==", project_name).limit(1).get()
        if existing_doc:
            doc_id = existing_doc[0].id
            projects_ref.document(doc_id).delete()
            st.success(f"Project '{project_name}' deleted successfully!")
            log_activity(user_id, st.session_state.user_email, f"Deleted project '{project_name}'")
        else:
            st.warning(f"Project '{project_name}' not found for deletion.")
    except Exception as e:
        st.error(f"Error deleting project from Firestore: {e}")

def log_activity(user_id, user_email, description):
    """Logs an activity to Firestore."""
    logs_ref = get_activity_logs_collection_ref()
    if logs_ref is None:
        st.error("Firestore not initialized. Cannot log activity.")
        return
    try:
        logs_ref.add({
            "timestamp": datetime.datetime.now(),
            "user_id": user_id,
            "user_email": user_email,
            "description": description
        })
    except Exception as e:
        st.error(f"Error logging activity to Firestore: {e}")

def load_activity_logs():
    """Loads all activity logs from Firestore."""
    logs_ref = get_activity_logs_collection_ref()
    if logs_ref is None:
        return pd.DataFrame(columns=["timestamp", "user_id", "user_email", "description"])
    try:
        docs = logs_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(100).stream()
        logs_list = []
        for doc in docs:
            log_data = doc.to_dict()
            logs_list.append(log_data)
        return pd.DataFrame(logs_list)
    except Exception as e:
        st.error(f"Error loading activity logs from Firestore: {e}")
        return pd.DataFrame(columns=["timestamp", "user_id", "user_email", "description"])

# --- Helper Functions (unchanged logic) ---
def get_initial_checklist_values():
    """Initializes an empty checklist structure based on HARDCODED_CHECKLIST_DATA."""
    initial_values = {}
    for step_name, sub_groups in HARDCODED_CHECKLIST_DATA.items():
        initial_values[step_name] = {}
        for sub_group_name, items in sub_groups.items():
            for item_name in items:
                if "Booking Period" in item_name or "Stay Period" in item_name:
                    initial_values[step_name][item_name] = {"from_date": "", "to_date": "", "note": ""}
                elif item_name == "Business Unit":
                    initial_values[step_name][item_name] = {"selection": "", "note": ""}
                else:
                    initial_values[step_name][item_name] = {"selection": "", "note": ""}
    return initial_values

def calculate_progress(values):
    """Calculates the completion progress of the checklist."""
    total_tasks_countable = 0
    completed_items = 0

    tk_selection = values.get('Step 1', {}).get("TK (Check if existing please follow 'CLEAN UP')", {}).get("selection")
    is_step2_active_for_progress = tk_selection != "No"

    for step_name, sub_groups in HARDCODED_CHECKLIST_DATA.items():
        if step_name == "Step 2" and not is_step2_active_for_progress:
            continue

        for sub_group_name, items in sub_groups.items():
            for item_name in items:
                total_tasks_countable += 1
                item_value = values.get(step_name, {}).get(item_name)

                if "Booking Period" in item_name or "Stay Period" in item_name:
                    if item_value and item_value.get("from_date") and item_value.get("to_date"):
                        completed_items += 1
                elif item_value and item_value.get("selection"):
                    completed_items += 1
    
    return (completed_items / total_tasks_countable) * 100 if total_tasks_countable > 0 else 0

def generate_step1_summary(step1_data):
    """Generates a concise summary string from key items in Step 1."""
    summary_parts = []

    bu = step1_data.get("Business Unit", {}).get("selection")
    if bu:
        summary_parts.append(f"Business Unit: {bu}")

    bp_from = step1_data.get("What is Booking Period (BOOPER ABSOLUTE)?", {}).get("from_date")
    bp_to = step1_data.get("What is Booking Period (BOOPER ABSOLUTE)?", {}).get("to_date")
    if bp_from and bp_to:
        summary_parts.append(f"Booking Period: {bp_from} to {bp_to}")

    sp_from = step1_data.get("Stay Period provided?", {}).get("from_date")
    sp_to = step1_data.get("Stay Period provided?", {}).get("to_date")
    if sp_from and sp_to:
        summary_parts.append(f"Stay Period: {sp_from} to {sp_to}")

    ticket_num_note = step1_data.get("Ticket Number ?", {}).get("note")
    if ticket_num_note:
        summary_parts.append(f"Ticket Number: {ticket_num_note}")

    for item_name, item_state in step1_data.items():
        if item_name not in ["Business Unit", "What is Booking Period (BOOPER ABSOLUTE)?", "Ticket Number ?", "Stay Period provided?"]:
            if item_state and item_state.get("note"):
                summary_parts.append(f"{item_name}: {item_state['note']}")

    return " | ".join(summary_parts) if summary_parts else "No key details from Step 1."

def get_available_years(projects_df):
    """Gets unique years from project data for filtering."""
    years = set()
    if not projects_df.empty:
        for _, project in projects_df.iterrows():
            project_data = json.loads(project['checklist_data'])
            bp_from_date_str = project_data.get('Step 1', {}).get("What is Booking Period (BOOPER ABSOLUTE)?", {}).get("from_date")
            sp_from_date_str = project_data.get('Step 1', {}).get("Stay Period provided?", {}).get("from_date")
            
            if bp_from_date_str:
                try:
                    years.add(datetime.datetime.strptime(bp_from_date_str, "%Y-%m-%d").year)
                except ValueError:
                    pass
            if sp_from_date_str:
                try:
                    years.add(datetime.datetime.strptime(sp_from_date_str, "%Y-%m-%d").year)
                except ValueError:
                    pass
    return ["All Years"] + sorted([str(y) for y in list(years)], reverse=True)

# --- UI Components ---
def display_llm_output_modal(title, content):
    """Simulates a modal for LLM output using Streamlit's expander."""
    with st.expander(f"**{title}**", expanded=True):
        st.text_area("Generated Content", content, height=300, disabled=True)
        st.download_button(
            label="Download as Text",
            data=content,
            file_name=f"{title.replace(' ', '_').lower()}.txt",
            mime="text/plain"
        )
        st.info("You can copy the content by selecting it in the text area and pressing Ctrl+C (Cmd+C on Mac).")

def render_login_page():
    st.set_page_config(layout="centered", page_title="Login - Regional Offer Checklist App")
    st.markdown(f"""
    <style>
        .stApp {{
            background-color: {THEME_COLORS['primary_bg']};
            color: {THEME_COLORS['text_dark']};
            font-family: 'Inter', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}
        .login-container {{
            background-color: {THEME_COLORS['secondary_bg']};
            padding: 2.5rem;
            border-radius: 0.75rem;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
            width: 100%;
            max-width: 400px;
            text-align: center;
        }}
        .stButton > button {{
            background-color: {THEME_COLORS['button_primary']};
            color: white;
            border-radius: 0.5rem;
            padding: 0.75rem 1.5rem;
            font-weight: bold;
            transition: background-color 0.2s, transform 0.2s;
            border: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            width: 100%;
            margin-top: 1rem;
        }}
        .stButton > button:hover {{
            background-color: {THEME_COLORS['button_primary_hover']};
            transform: translateY(-2px);
        }}
        .stTextInput > div > div > input {{
            border-radius: 0.5rem;
            border-color: {THEME_COLORS['border_color']};
            background-color: {THEME_COLORS['primary_bg']};
            color: {THEME_COLORS['text_dark']};
            padding: 0.75rem 1rem;
            font-size: 1em;
        }}
        .stTextInput label {{
            color: {THEME_COLORS['text_dark']};
            font-weight: 600;
            margin-bottom: 0.5rem;
            display: block;
        }}
        h1 {{
            color: {THEME_COLORS['text_dark']};
            font-size: 2em;
            margin-bottom: 1.5rem;
        }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.markdown("<h1>เข้าสู่ระบบ</h1>", unsafe_allow_html=True)

    with st.form("login_form"):
        email = st.text_input("อีเมล", key="login_email")
        password = st.text_input("รหัสผ่าน", type="password", key="login_password")
        submitted = st.form_submit_button("เข้าสู่ระบบ")

        if submitted:
            if email and password:
                login_user(email, password)
            else:
                st.error("โปรดป้อนอีเมลและรหัสผ่าน")
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_dashboard(gc_client, user_id, user_email):
    """Renders the project dashboard view."""
    st.markdown(f"<h1 style='color:{THEME_COLORS['text_dark']}; font-size: 2.5em; font-weight: bold; margin-bottom: 2rem;'>ภาพรวมโครงการข้อเสนอภูมิภาค</h1>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("🚀 เริ่มโครงการใหม่", use_container_width=True):
            st.session_state.show_project_prompt = True
    with col2:
        st.info(f"เข้าสู่ระบบในฐานะ: {user_email} (User ID: {user_id})", icon="�")
        if st.button("ออกจากระบบ", key="logout_btn"):
            logout_user()

    if st.session_state.get('show_project_prompt'):
        with st.form("new_project_form"):
            st.markdown(f"<h2 style='color:{THEME_COLORS['text_dark']}; font-size: 1.5em; font-weight: bold; margin-bottom: 1rem;'>ป้อนชื่อโครงการ</h2>", unsafe_allow_html=True)
            new_project_name = st.text_input("ชื่อโครงการ", key="new_project_name_input")
            
            submitted = st.form_submit_button("ยืนยัน")
            if submitted:
                if new_project_name.strip():
                    st.session_state.current_project_name = new_project_name.strip()
                    st.session_state.checklist_values = get_initial_checklist_values()
                    st.session_state.current_step_index = 0
                    st.session_state.view = 'wizard'
                    st.rerun()
                else:
                    st.error("ชื่อโครงการไม่สามารถเว้นว่างได้.")
            if st.form_submit_button("ยกเลิก", type="secondary"):
                st.session_state.show_project_prompt = False
                st.rerun()


    st.markdown(f"<div style='background-color:{THEME_COLORS['secondary_bg']}; padding: 1.5rem; border-radius: 0.75rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);'>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["ความคืบหน้าโครงการทั้งหมด", "บันทึก"])

    with tab1:
        st.markdown(f"<h2 style='color:{THEME_COLORS['text_dark']}; font-size: 1.5em; font-weight: bold; margin-bottom: 1rem;'>ความคืบหน้าโครงการทั้งหมด</h2>", unsafe_allow_html=True)
        
        col_search, col_year, col_month = st.columns([2, 1, 1])
        with col_search:
            search_term = st.text_input("ค้นหาชื่อโปรเจกต์...", value=st.session_state.get('search_term', ''), key="search_input")
            st.session_state.search_term = search_term # Update session state

        projects_df = load_projects_from_firestore(user_id)
        
        # Filter projects based on search term, year, and month
        filtered_projects_df = projects_df[projects_df['user_id'] == user_id] # Filter by current user first

        if search_term:
            filtered_projects_df = filtered_projects_df[filtered_projects_df['project_name'].str.contains(search_term, case=False, na=False)]

        available_years = get_available_years(filtered_projects_df) # Get years from filtered projects
        with col_year:
            filter_year = st.selectbox("ทุกปี", available_years, key="filter_year")
            st.session_state.filter_year = filter_year
        
        with col_month:
            filter_month = st.selectbox("ทุกเดือน", MONTH_NAMES, key="filter_month")
            st.session_state.filter_month = filter_month

        if filter_year != "All Years":
            filtered_projects_df = filtered_projects_df[
                filtered_projects_df['checklist_data'].apply(lambda x: datetime.datetime.strptime(json.loads(x).get('Step 1', {}).get("What is Booking Period (BOOPER ABSOLUTE)?", {}).get("from_date", "1900-01-01"), "%Y-%m-%d").year == int(filter_year) if json.loads(x).get('Step 1', {}).get("What is Booking Period (BOOPER ABSOLUTE)?", {}).get("from_date") else (datetime.datetime.strptime(json.loads(x).get('Step 1', {}).get("Stay Period provided?", {}).get("from_date", "1900-01-01"), "%Y-%m-%d").year == int(filter_year) if json.loads(x).get('Step 1', {}).get("Stay Period provided?", {}).get("from_date") else False))
            ]
        if filter_month != "All Months":
            month_index = MONTH_NAMES.index(filter_month)
            filtered_projects_df = filtered_projects_df[
                filtered_projects_df['checklist_data'].apply(lambda x: datetime.datetime.strptime(json.loads(x).get('Step 1', {}).get("What is Booking Period (BOOPER ABSOLUTE)?", {}).get("from_date", "1900-01-01"), "%Y-%m-%d").month == month_index if json.loads(x).get('Step 1', {}).get("What is Booking Period (BOOPER ABSOLUTE)?", {}).get("from_date") else (datetime.datetime.strptime(json.loads(x).get('Step 1', {}).get("Stay Period provided?", {}).get("from_date", "1900-01-01"), "%Y-%m-%d").month == month_index if json.loads(x).get('Step 1', {}).get("Stay Period provided?", {}).get("from_date") else False))
            ]

        if filtered_projects_df.empty:
            st.markdown(f"<p style='text-align:center; color:{THEME_COLORS['text_light']}; font-size: 1.125em;'>ไม่พบโครงการใดๆ ที่ตรงกับตัวกรอง. เริ่มโครงการใหม่ได้เลย!</p>", unsafe_allow_html=True)
        else:
            cols = st.columns(3) # Display in 3 columns
            for i, (_, project) in enumerate(filtered_projects_df.iterrows()):
                with cols[i % 3]:
                    st.markdown(f"<div style='background-color:white; padding: 1.5rem; border-radius: 0.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: flex; flex-direction: column; align-items: center; justify-content: space-between; height: 100%; border: 1px solid {THEME_COLORS['border_color']};'>", unsafe_allow_html=True)
                    st.markdown(f"<div style='display: flex; justify-content: space-between; width: 100%; align-items: flex-start; margin-bottom: 0.75rem;'>", unsafe_allow_html=True)
                    st.markdown(f"<h3 style='color:{THEME_COLORS['text_dark']}; font-size: 1.25em; font-weight: 600;'>{project['project_name']}</h3>", unsafe_allow_html=True)
                    if st.button("🗑️", key=f"delete_{project['project_name']}"):
                        if st.session_state.get('confirm_delete_project') == project['project_name']:
                            delete_project_from_firestore(user_id, project['project_name'])
                            st.session_state.confirm_delete_project = None # Reset confirmation
                            st.rerun()
                        else:
                            st.session_state.confirm_delete_project = project['project_name']
                            st.warning(f"คุณแน่ใจหรือไม่ว่าต้องการลบ '{project['project_name']}'? คลิก '🗑️' อีกครั้งเพื่อยืนยัน.")
                    st.markdown("</div>", unsafe_allow_html=True)

                    # Circular Progress Indicator (simplified HTML/SVG)
                    progress_color = (
                        THEME_COLORS['progress_yellow'] if project['progress'] < 35 else
                        THEME_COLORS['progress_blue'] if project['progress'] < 80 else
                        THEME_COLORS['progress_green']
                    )
                    st.markdown(f"""
                    <div style="position: relative; width: 6rem; height: 6rem; margin-bottom: 1rem;">
                        <svg viewBox="0 0 100 100" style="transform: rotate(-90deg); width: 100%; height: 100%;">
                            <circle cx="50" cy="50" r="45" fill="none" stroke="{THEME_COLORS['border_color']}" stroke-width="7" opacity="0.75"/>
                            <circle cx="50" cy="50" r="45" fill="none" stroke="{progress_color}" stroke-width="7"
                                stroke-dasharray="{ (project['progress'] / 100) * 2 * 3.14159 * 45 } { 2 * 3.14159 * 45 }"
                                stroke-linecap="round"
                            />
                        </svg>
                        <span style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 1.125em; font-weight: bold; color:{THEME_COLORS['text_dark']};">
                            {round(project['progress'])}%
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"<p style='text-align:center; color:{THEME_COLORS['text_light']}; font-size: 0.875em; min-height: 2.5rem;'>{project['summary']}</p>", unsafe_allow_html=True)
                    if st.button("ดำเนินการต่อ", key=f"continue_{project['project_name']}", use_container_width=True):
                        st.session_state.current_project_name = project['project_name']
                        st.session_state.checklist_values = json.loads(project['checklist_data']) # Load JSON string
                        st.session_state.current_step_index = 0
                        st.session_state.view = 'wizard'
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
    with tab2:
        st.markdown(f"<h3 style='color:{THEME_COLORS['text_dark']}; font-size: 1.25em; font-weight: bold; margin-bottom: 1rem;'>กิจกรรมล่าสุด</h3>", unsafe_allow_html=True)
        logs_df = load_activity_logs()
        if logs_df.empty:
            st.info("ยังไม่มีกิจกรรม.")
        else:
            # Format timestamp for better readability
            logs_df['timestamp'] = logs_df['timestamp'].apply(lambda x: x.strftime("%Y-%m-%d %H:%M:%S"))
            st.dataframe(logs_df[['timestamp', 'user_email', 'description']], use_container_width=True, hide_index=True)
    
    st.markdown("</div>", unsafe_allow_html=True) # Close secondary_bg div


def render_wizard(gc_client, user_id):
    """Renders the multi-step checklist wizard view."""
    current_project_name = st.session_state.current_project_name
    current_step_index = st.session_state.current_step_index
    checklist_values = st.session_state.checklist_values

    steps = list(HARDCODED_CHECKLIST_DATA.keys())
    current_step_name = steps[current_step_index]
    sub_groups = HARDCODED_CHECKLIST_DATA[current_step_name]

    # Progress bar and project info
    current_project_progress = calculate_progress(checklist_values)
    st.markdown(f"<div style='background-color:white; padding: 1.5rem; border-radius: 0.75rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); border: 1px solid {THEME_COLORS['border_color']}; margin-bottom: 1.5rem;'>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='color:{THEME_COLORS['text_dark']}; font-size: 1.875em; font-weight: bold; margin-bottom: 0.5rem;'>โครงการ: {current_project_name}</h1>", unsafe_allow_html=True)
    st.markdown(f"<div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;'>", unsafe_allow_html=True)
    st.markdown(f"<span style='color:{THEME_COLORS['text_light']}; font-size: 1.125em; font-weight: 500;'>ความคืบหน้า: {round(current_project_progress)}%</span>", unsafe_allow_html=True)
    st.markdown(f"<div style='width: 66%; height: 0.5rem; border-radius: 9999px; background-color: {THEME_COLORS['secondary_bg']};'>", unsafe_allow_html=True)
    st.markdown(f"<div style='width: {current_project_progress}%; height: 100%; border-radius: 9999px; background-color: {THEME_COLORS['progress_green'] if current_project_progress >= 80 else (THEME_COLORS['progress_blue'] if current_project_progress >= 35 else THEME_COLORS['progress_yellow'])}; transition: all 0.5s ease-in-out;'></div>", unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

    # LLM Buttons
    llm_cols = st.columns([1, 1])
    with llm_cols[0]:
        if st.button("✨ สรุปบันทึก", key="summarize_notes_btn", use_container_width=True):
            with st.spinner("กำลังสรุปบันทึก..."):
                all_notes = []
                for step_data in checklist_values.values():
                    for item_state in step_data.values():
                        if item_state.get("note"):
                            all_notes.append(item_state["note"])
                
                if not all_notes:
                    st.warning("ไม่มีบันทึกให้สรุป.")
                else:
                    prompt = f"Summarize the following project notes concisely, focusing on key actions, statuses, and issues. Combine related points and avoid redundancy:\n\n{'; '.join(all_notes)}"
                    # Gemini API call is commented out for now to focus on core features
                    # gemini_model = get_gemini_model()
                    # summary = call_gemini_api(gemini_model, prompt)
                    summary = "LLM feature temporarily disabled for core app stability. Summary of notes would go here." # Placeholder
                    st.session_state.llm_summary_content = summary
                    st.session_state.show_llm_summary_modal = True
    with llm_cols[1]:
        if current_step_index == 3: # Step 4 is index 3
            with st.form("email_draft_form"):
                recipient = st.text_input("ป้อนผู้รับ (เช่น 'Expedia Partner'):", key="email_recipient_input_form")
                purpose = st.text_input("ป้อนวัตถุประสงค์ของอีเมล (เช่น 'การเปิดตัวข้อเสนอภูมิภาคใหม่'):", key="email_purpose_input_form")
                generate_button_clicked = st.form_submit_button("สร้างฉบับร่างอีเมล")
                
                if generate_button_clicked:
                    if recipient and purpose:
                        with st.spinner("กำลังร่างอีเมล..."):
                            email_details = [f"Project: {current_project_name}"]
                            step4_data = checklist_values.get('Step 4', {}).get("Distribution to OTAS", {})
                            for item_name, item_state in step4_data.items():
                                if item_state.get("selection") == 'Yes' or item_state.get("note"):
                                    detail = f"{item_name}: {item_state.get('selection', '')}"
                                    if item_state.get("note"):
                                        detail += f" ({item_state['note']})"
                                    email_details.append(detail.strip())

                            prompt_text = (
                                "Draft a professional email to '{recipient}' about '{purpose}'.\n"
                                "Include the following details from the regional offer distribution checklist:\n"
                                "{email_details_str}\n\n"
                                "Keep it concise and actionable."
                            ).format(
                                recipient=recipient,
                                purpose=purpose,
                                email_details_str='\n'.join(email_details)
                            )
                            
                            # Gemini API call is commented out for now to focus on core features
                            # gemini_model = get_gemini_model()
                            # drafted_email = call_gemini_api(gemini_model, prompt_text)
                            drafted_email = "LLM feature temporarily disabled for core app stability. Drafted email would go here." # Placeholder
                            st.session_state.llm_email_content = drafted_email
                            st.session_state.show_llm_email_modal = True
                    else:
                        st.warning("โปรดป้อนทั้งผู้รับและวัตถุประสงค์เพื่อร่างอีเมล.")
    st.markdown("</div>", unsafe_allow_html=True) # Close header div

    # Step Indicators
    step_cols = st.columns(len(steps))
    for i, step in enumerate(steps):
        is_step2_disabled = (i == 1 and checklist_values.get('Step 1', {}).get("TK (Check if existing please follow 'CLEAN UP')", {}).get("selection") == "No")
        
        with step_cols[i]:
            st.markdown(f"""
                <style>
                    .stButton[data-testid="stButton-{f"step_btn_{i}"}"] > button {{
                        background-color: {THEME_COLORS['button_primary'] if i == current_step_index else (THEME_COLORS['button_disabled'] if is_step2_disabled else THEME_COLORS['button_secondary'])};
                        color: white;
                        font-weight: bold;
                        padding: 0.3rem 0.8rem; /* Smaller padding */
                        font-size: 0.85em; /* Smaller font size */
                        border-radius: 0.5rem;
                        border: none;
                        cursor: {'not-allowed' if is_step2_disabled else 'pointer'};
                        transition: background-color 0.2s, transform 0.2s;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        width: 100%; /* Ensure it fills column */
                    }}
                    .stButton[data-testid="stButton-{f"step_btn_{i}"}"] > button:hover {{
                        background-color: {THEME_COLORS['button_primary_hover'] if i == current_step_index else (THEME_COLORS['button_disabled'] if is_step2_disabled else THEME_COLORS['button_secondary_hover'])};
                        transform: translateY(-1px); /* Smaller hover effect */
                    }}
                </style>
                """, unsafe_allow_html=True)
            if st.button(step, key=f"step_btn_{i}", disabled=is_step2_disabled, help="ขั้นตอนที่ 2 จะถูกข้ามหาก 'TK (Check if existing please follow 'CLEAN UP')' ถูกตั้งค่าเป็น 'No'"):
                if is_step2_disabled and i == 1:
                    st.warning("ขั้นตอนที่ 2 ถูกข้ามเนื่องจาก 'TK (Check if existing please follow 'CLEAN UP')' ถูกตั้งค่าเป็น 'No'.")
                else:
                    st.session_state.current_step_index = i
                    st.rerun()
    
    st.markdown(f"<div style='background-color:{THEME_COLORS['secondary_bg']}; padding: 1.5rem; border-radius: 0.75rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); margin-top: 1.5rem;'>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:{THEME_COLORS['text_dark']}; font-size: 1.5em; font-weight: bold; margin-bottom: 1.5rem;'>{current_step_name} รายการตรวจสอบ</h2>", unsafe_allow_html=True)

    for sub_group_name, items in sub_groups.items():
        st.markdown(f"<div style='border-bottom: 2px solid {THEME_COLORS['sub_group_underline']}; padding-bottom: 0.5rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;'>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='color:{THEME_COLORS['text_dark']}; font-size: 1.25em; font-weight: bold;'>{sub_group_name}</h3>", unsafe_allow_html=True)
        
        # Select All buttons for subgroup
        col_select_all_yes, col_select_all_no = st.columns(2)
        with col_select_all_yes:
            if st.button("เลือกทั้งหมด ใช่", key=f"select_all_yes_{current_step_name}_{sub_group_name}", use_container_width=True):
                for item_name in items:
                    if "selection" in checklist_values[current_step_name][item_name]:
                        checklist_values[current_step_name][item_name]["selection"] = "Yes"
                st.session_state.checklist_values = checklist_values
                st.rerun()
        with col_select_all_no:
            if st.button("เลือกทั้งหมด ไม่ใช่", key=f"select_all_no_{current_step_name}_{sub_group_name}", use_container_width=True):
                for item_name in items:
                    if "selection" in checklist_values[current_step_name][item_name]:
                        checklist_values[current_step_name][item_name]["selection"] = "No"
                st.session_state.checklist_values = checklist_values
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True) # Close select all div

        for item_name in items:
            item_state = checklist_values.get(current_step_name, {}).get(item_name, {"selection": "", "from_date": "", "to_date": "", "note": ""})
            
            # Adjusted column widths for a more compact and readable row layout
            item_cols = st.columns([0.1, 0.4, 0.5]) # Smaller first column for radio/checkbox, larger for text and note

            with item_cols[0]:
                if "Booking Period" in item_name or "Stay Period" in item_name:
                    # Date inputs are naturally larger, will keep them as is for usability
                    # Labels are moved to the main text column for better alignment
                    pass 
                elif item_name == "Business Unit":
                    # Selection box will be in the main text column
                    pass
                else:
                    selection_options = ["", "Yes", "No"]
                    selected_option = st.selectbox("", selection_options, # Label is empty, item_name will be in next column
                                 index=selection_options.index(item_state["selection"]) if item_state["selection"] in selection_options else 0,
                                 key=f"select_{current_step_name}_{item_name}",
                                 label_visibility="collapsed") # Hide default label for compactness
                    checklist_values[current_step_name][item_name]["selection"] = selected_option
            
            with item_cols[1]:
                st.markdown(f"<p style='color:{THEME_COLORS['text_dark']}; font-size: 0.95em; font-weight: 500; margin-bottom: 0;'>{item_name}</p>", unsafe_allow_html=True)
                if "Booking Period" in item_name or "Stay Period" in item_name:
                    # Display date inputs here
                    selected_from_date = st.date_input("จาก", 
                                  value=datetime.datetime.strptime(item_state["from_date"], "%Y-%m-%d").date() if item_state["from_date"] else None,
                                  key=f"from_date_{current_step_name}_{item_name}",
                                  label_visibility="collapsed")
                    if selected_from_date:
                        checklist_values[current_step_name][item_name]["from_date"] = str(selected_from_date)
                    else:
                        checklist_values[current_step_name][item_name]["from_date"] = ""

                    selected_to_date = st.date_input("ถึง", 
                                  value=datetime.datetime.strptime(item_state["to_date"], "%Y-%m-%d").date() if item_state["to_date"] else None,
                                  key=f"to_date_{current_step_name}_{item_name}",
                                  label_visibility="collapsed")
                    if selected_to_date:
                        checklist_values[current_step_name][item_name]["to_date"] = str(selected_to_date)
                    else:
                        checklist_values[current_step_name][item_name]["to_date"] = ""
                elif item_name == "Business Unit":
                    selection_options = ["", "MEAPAC", "La Maion", "ENA", "RIXOS", "Fairmont & Raffles", "China"]
                    selected_bu = st.selectbox("Business Unit", selection_options, 
                                 index=selection_options.index(item_state["selection"]) if item_state["selection"] in selection_options else 0,
                                 key=f"select_{current_step_name}_{item_name}",
                                 label_visibility="collapsed")
                    checklist_values[current_step_name][item_name]["selection"] = selected_bu
            
            with item_cols[2]:
                note_value = st.text_input("บันทึก", value=item_state["note"], key=f"note_{current_step_index}_{item_name}", label_visibility="collapsed")
                checklist_values[current_step_name][item_name]["note"] = note_value
            
            st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True) # Smaller separator

    # Update session state after all inputs are processed for the current step
    st.session_state.checklist_values = checklist_values

    st.markdown("</div>", unsafe_allow_html=True) # Close secondary_bg div

    # Navigation buttons
    nav_cols = st.columns([1, 1, 1, 1])
    with nav_cols[0]:
        if st.button("🏠 กลับสู่แดชบอร์ด", key="back_to_dashboard_btn", use_container_width=True):
            st.session_state.view = 'dashboard'
            st.rerun()
    with nav_cols[1]:
        if st.button("< ก่อนหน้า", key="prev_step_btn", disabled=(current_step_index == 0), use_container_width=True):
            tk_selection = checklist_values.get('Step 1', {}).get("TK (Check if existing please follow 'CLEAN UP')", {}).get("selection")
            if current_step_index == 2 and tk_selection == "No":
                st.session_state.current_step_index = 0
            else:
                st.session_state.current_step_index -= 1
            st.rerun()
    with nav_cols[2]:
        if st.button("ถัดไป >", key="next_step_btn", disabled=(current_step_index == len(steps) - 1), use_container_width=True):
            tk_selection = checklist_values.get('Step 1', {}).get("TK (Check if existing please follow 'CLEAN UP')", {}).get("selection")
            if current_step_index == 0 and tk_selection == "No":
                st.session_state.current_step_index = 2
            else:
                st.session_state.current_step_index += 1
            st.rerun()
    with nav_cols[3]:
        if st.button("💾 บันทึกข้อมูล", key="save_data_btn", use_container_width=True):
            summary_text = generate_step1_summary(checklist_values.get('Step 1', {}))
            save_project_to_firestore(user_id, current_project_name, current_project_progress, summary_text, checklist_values)
            st.rerun() # Rerun to refresh dashboard data if user goes back

    # Display LLM output modals if triggered
    if st.session_state.get('show_llm_summary_modal'):
        display_llm_output_modal("Project Notes Summary", st.session_state.llm_summary_content)
        st.session_state.show_llm_summary_modal = False # Reset after display

    if st.session_state.get('show_llm_email_modal'):
        display_llm_output_modal("Drafted Email", st.session_state.llm_email_content)
        st.session_state.show_llm_email_modal = False # Reset after display

# --- Main App Logic ---
def main():
    # Initialize session state variables if they don't exist
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'view' not in st.session_state:
        st.session_state.view = 'dashboard'
    if 'current_project_name' not in st.session_state:
        st.session_state.current_project_name = None
    if 'checklist_values' not in st.session_state:
        st.session_state.checklist_values = get_initial_checklist_values()
    if 'current_step_index' not in st.session_state:
        st.session_state.current_step_index = 0
    if 'show_project_prompt' not in st.session_state:
        st.session_state.show_project_prompt = False
    if 'llm_summary_content' not in st.session_state:
        st.session_state.llm_summary_content = ""
    if 'show_llm_summary_modal' not in st.session_state:
        st.session_state.show_llm_summary_modal = False
    if 'llm_email_content' not in st.session_state:
        st.session_state.llm_email_content = ""
    if 'show_llm_email_modal' not in st.session_state:
        st.session_state.show_llm_email_modal = False
    if 'search_term' not in st.session_state:
        st.session_state.search_term = ''
    if 'filter_year' not in st.session_state:
        st.session_state.filter_year = 'All Years'
    if 'filter_month' not in st.session_state:
        st.session_state.filter_month = 'All Months'
    if 'confirm_delete_project' not in st.session_state:
        st.session_state.confirm_delete_project = None

    # Apply custom CSS for styling
    st.markdown(f"""
    <style>
        .stApp {{
            background-color: {THEME_COLORS['primary_bg']};
            color: {THEME_COLORS['text_dark']};
            font-family: 'Inter', sans-serif;
        }}
        .stButton > button {{
            background-color: {THEME_COLORS['button_primary']};
            color: white;
            border-radius: 0.5rem;
            padding: 0.75rem 1.5rem; /* Default button padding */
            font-weight: bold;
            transition: background-color 0.2s, transform 0.2s;
            border: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            font-size: 1em; /* Default button font size */
        }}
        .stButton > button:hover {{
            background-color: {THEME_COLORS['button_primary_hover']};
            transform: translateY(-2px);
        }}
        .stButton > button:disabled {{
            background-color: {THEME_COLORS['button_disabled']};
            cursor: not-allowed;
            transform: none;
        }}
        /* Specific styling for step navigation buttons - applied via markdown in render_wizard */
        
        .stSelectbox > div > div {{
            border-radius: 0.5rem;
            border-color: {THEME_COLORS['border_color']};
            background-color: {THEME_COLORS['primary_bg']};
            color: {THEME_COLORS['text_dark']};
            font-size: 0.9em; /* Smaller font for selectbox */
        }}
        .stSelectbox > div > div > div[data-baseweb="select"] {{
            padding: 0.25rem 0.5rem; /* Smaller padding for selectbox */
        }}
        .stTextInput > div > div > input {{
            border-radius: 0.5rem;
            border-color: {THEME_COLORS['border_color']};
            background-color: {THEME_COLORS['primary_bg']};
            color: {THEME_COLORS['text_dark']};
            padding: 0.25rem 0.5rem; /* Smaller padding for text input */
            font-size: 0.9em; /* Smaller font for text input */
        }}
        .stTextArea > div > div > textarea {{
            border-radius: 0.5rem;
            border-color: {THEME_COLORS['border_color']};
            background-color: {THEME_COLORS['primary_bg']};
            color: {THEME_COLORS['text_dark']};
            padding: 0.25rem 0.5rem; /* Smaller padding for text area */
            font-size: 0.9em; /* Smaller font for text area */
        }}
        .stDateInput > label + div > div {{
            border-radius: 0.5rem;
            border-color: {THEME_COLORS['border_color']};
            background-color: {THEME_COLORS['primary_bg']};
            color: {THEME_COLORS['text_dark']};
            padding: 0.25rem 0.5rem; /* Smaller padding for date input */
            font-size: 0.9em; /* Smaller font for date input */
        }}
        .stDateInput > label + div > div > input {{
            color: {THEME_COLORS['text_dark']};
        }}
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {{
            font-size:1.125rem;
        }}
        .stTabs [data-baseweb="tab-list"] button {{
            background-color: {THEME_COLORS['secondary_bg']};
            border-top-left-radius: 0.5rem;
            border-top-right-radius: 0.5rem;
            border: 1px solid {THEME_COLORS['border_color']};
            border-bottom: none;
            margin-right: 0.25rem;
            padding: 0.75rem 1.5rem;
        }}
        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
            background-color: white;
            border-bottom: 1px solid white; /* Hide bottom border for active tab */
        }}
        .stTabs [data-baseweb="tab-panel"] {{
            background-color: white;
            border-radius: 0.75rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            border: 1px solid {THEME_COLORS['border_color']};
            padding: 1rem;
        }}
        /* Custom styling for checklist items to make them more compact */
        div[data-testid="stVerticalBlock"] > div > div > div > div.st-emotion-cache-1r6ch9j {{ /* Target the inner div containing the item columns */
            margin-bottom: 0.25rem; /* Reduce space between items */
        }}
        .st-emotion-cache-1r6ch9j > div:first-child {{ /* Target the first column (selection) */
            padding-right: 0.5rem; /* Reduce padding */
        }}
        .st-emotion-cache-1r6ch9j > div:nth-child(2) {{ /* Target the second column (item name) */
            padding-left: 0.5rem; /* Reduce padding */
            padding-right: 0.5rem;
        }}
        .st-emotion-cache-1r6ch9j > div:last-child {{ /* Target the third column (note) */
            padding-left: 0.5rem; /* Reduce padding */
        }}
    </style>
    """, unsafe_allow_html=True)

    # Main app logic based on authentication status
    if not st.session_state.logged_in:
        render_login_page()
    else:
        st.set_page_config(layout="wide", page_title="Regional Offer Checklist App")
        # Initialize Google Sheets client (still needed for the `gc_client` parameter, but data ops are Firestore)
        # We pass None for gc_client as it's no longer used for data ops, but functions expect it.
        # This is a temporary workaround until refactoring is complete.
        gc_client = None 

        # Render appropriate view
        if st.session_state.view == 'dashboard':
            render_dashboard(gc_client, st.session_state.user_id, st.session_state.user_email)
        elif st.session_state.view == 'wizard':
            render_wizard(gc_client, st.session_state.user_id)

if __name__ == "__main__":
    main()
