# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import json
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# =====================================================================================
# 1. CONFIGURATION & INITIALIZATION
# =====================================================================================

# ข้อมูลเช็กลิสต์ (ไม่มีการเปลี่ยนแปลงจากเดิม)
HARDCODED_CHECKLIST_DATA = {
    "Step 1": {
        "Check the form": [
            "Business Unit", "What is Booking Period (BOOPER ABSOLUTE)?", "Ticket Number ?",
            "Offer Name TK", "Offer Name Commercial", "Is there any BOOPER Relative request?",
            "Stay Period provided?", "Rate level code confirmed?", "TK (Check if existing please follow 'CLEAN UP')",
            "Eligible with point - Must clarify only earnpoint or use point", "Central use", "Flexibility",
            "Exclude TK?", "Meal Plan", "MINSTA MAXSTA", "CANPOL", "GUAPOL",
            "Other informative Sale condition . PKGS, AHRES1…", "Meal products = combinded or included or index meal products aswell?",
            "Substitution Tars Key Code?", "Referencial TK", "If any unclear qustion please reach out to requester",
            "Check if WDR or MS, if MS hotel included please awere Rate Family in Basisweb",
            "Check reference rate and MODIFY in the loading form", "Check What is PMS interface"
        ],
        "Check OTAs/ GDS part": [
            "Is this offer included OTAs?", "Rate level code ? OTAs",
            "Special to be awere -0% on Expedia ? (for promotagging purpose)",
            "Check the requester is require specific contacts people to CC when sendign DD to?",
            "ALL OTAs for All hotels or only some OTAs?", "All GDS?", "If yes on GDS is there specific RAC code required?"
        ],
        "This must be done first day": [
            "Open request to the ENA team before start loading", "Open request to the American team before start loading",
            "Open the ticket for create rate in Ddege", "Double check reference rate before start using automation",
            "Changed TK Validity = No limit to No limit both Direct and OTAs"
        ]
    },
    "Step 2": {
        "Clean up Using Extraction": ["CANPOL", "GUAPOL", "BOOPER", "MINSTA, MAXSTA, MINAB, MAXAB, MINTHR, MAXTHR", "HRL", "HTK", "INDEX", "Pricing (STATIC)"],
        "Clean up": ["Is TK already used in another offer?", "Has previous offer been ended or deactivated?", "Check and clean up any saleconfition in DBMDIS", "Review all extractions and delete if possible"]
    },
    "Step 3": {
        "Loading Day Direct Automation": ["Using Automation Offer", "Selected correct fuction, Create, Add hotel to offer, or Renewal", "Put the require TK,", "Make sure correct Qualification", "Card holder", "Booking wit point", "Extended name, Marketing Name", "Flexibility", "Substitution Tars Key Code?", "Put rate Level", "Pricing file CSV, Index or Static", "Sale condition Ensure MINSTA, MAXSTA, BOOPER, CANPOL, GUAPOL", "Check the Error if any must fix now"],
        "Loading After Automation": ["Reload everything according to the form such as HRL, Index, and other specific", "Modify HTK with adding Referencial TK", "Modify Rate Level combunded MBREAK, no generic if Meal is discounted", "If Meal plan discount must index Meal plan", "APOL load all hotels ?", "Add MINAB if require incaes using BOOPER absolute already", "Chenck :R_Matrix RL-TK setting per channels (If any specific channels needed such as GDS)"],
        "Loading day OTAS Pre-requistes": ["Make sure check all hotel has taxes set up and associtaed to room type otherwise can't pull DD", "OTAs H-RL ", "External Mapping for PMS ", "Indexation/Pricing loading are done"],
        "Loading day OTAS Automation": ["Choose the correct fuction Add hotel to offer , Create, or Renewal OTAS?", "Make sure to clean up RL index, rate, Sale condition, if reusing the existing", "Put Direct TK", "GDS, CTO and OTAs selection Click here for the list of eligible GDS, CTO and OTA", "Put indirect RL both OTAs and CTOs (FLxxx & FLMxxxx)", "I want to send Datadump manually to distributors", "Then put Email", "Select hotel and add the parameter, it will copy hotel list participating from Direct TKs", "Then check all detail before confirm"],
        "Loading After OTAs Automation": ["Make sure HTK Validity = Stay date period only (Please Hold and only change before live OTAS date)", "Make sure to put BOOPER Absolute now", "Advance OTAs push schedule as soon as possible", "Many OTAS partner will have FPLOS error if put BOOPER in TK level (DBMDis)", "Many OTAS partner will have MINSTA in TK level (DBMDis)"],
        "GDS": ["Apply RAC for each public rate for 4 GDS in DBMDIs"]
    },
    "Step 4": {"Distribution to OTAS": ["Generate Email for each partner", "Promo tagging require on OTAS?", "Check if any attched missing remuneration in GES", "Expedia make sure to fill up the blank, Expedia ID, Payment model, Stanalone or package", "EX Daily File Done?", "AG Daily File Done?", "BK API Done?"]},
    "Step 5": {
        "Final check": ["Please make sure to attatch correct Absolute BOOPER in all TKs direct and indirect", "Please review the final indexation, Booper, MINSTA CLOARR and HTK Validity", "Call test booking with in Data Admin team", "Test 4 GDS Bookign and keep screenshot"],
        "Final Check Direct Landing Page?": ["Landing page? If Yes, both Accor Plus and Main offer must be Qualify or not must ask requester to test"],
        "Upload": ["Upload the Excel online link for OTAS Tracking Status", "Upload Hotel lists", "Upload TARSKEYS lists"]
    },
    "Step 6": {"After Offer Expiration": ["Schedule the clean up on calendar ", "Make sure to clean up when offer expire date", "Pricing deleteion", "Put CLOARR then push ARI", "Change TK validity to 20491231 to 20491231"]}
}

@st.cache_resource
def initialize_firebase():
    """Initializes Firebase using credentials from st.secrets."""
    try:
        if "firebase_credentials" not in st.secrets:
            st.error("Firebase credentials not found in st.secrets. Please configure them.")
            return None
        
        creds_json = json.loads(st.secrets["firebase_credentials"])
        cred = credentials.Certificate(creds_json)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Failed to initialize Firebase: {e}")
        return None

db = initialize_firebase()
APP_ID = st.secrets.get("app_id", "regional-offer-checklist-web")
PROJECTS_COLLECTION = db.collection(f"artifacts/{APP_ID}/projects") if db else None

# =====================================================================================
# 2. DATA HANDLING FUNCTIONS
# =====================================================================================

@st.cache_data(ttl=60) # Cache data for 60 seconds
def load_projects():
    if not PROJECTS_COLLECTION:
        return []
    try:
        docs = PROJECTS_COLLECTION.stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        st.error(f"Error loading projects: {e}")
        return []

def save_project(project_data):
    if not PROJECTS_COLLECTION:
        st.error("Database connection not available.")
        return
    try:
        project_name = project_data["name"]
        project_data["last_updated"] = datetime.now(datetime.timezone.utc).isoformat()
        PROJECTS_COLLECTION.document(project_name).set(project_data)
        st.cache_data.clear() # Invalidate cache after saving
    except Exception as e:
        st.error(f"Error saving project '{project_name}': {e}")

def delete_project(project_name):
    if not PROJECTS_COLLECTION:
        st.error("Database connection not available.")
        return
    try:
        PROJECTS_COLLECTION.document(project_name).delete()
        st.toast(f"Deleted project '{project_name}'", icon="🗑️")
        st.cache_data.clear() # Invalidate cache after deleting
    except Exception as e:
        st.error(f"Error deleting project '{project_name}': {e}")

# =====================================================================================
# 3. HELPER & UI FUNCTIONS
# =====================================================================================

def get_initial_checklist_data():
    """Creates a blank data structure for a new checklist."""
    initial_data = {}
    for step, groups in HARDCODED_CHECKLIST_DATA.items():
        initial_data[step] = {}
        for group, items in groups.items():
            initial_data[step][group] = {}
            for item in items:
                initial_data[step][group][item] = {"selection": "", "note": "", "from_date": None, "to_date": None}
    return initial_data

def calculate_progress(checklist_data):
    """Calculates the completion percentage of a checklist."""
    total, completed = 0, 0
    skip_step2 = checklist_data.get("Step 1", {}).get("Check the form", {}).get("TK (Check if existing please follow 'CLEAN UP')", {}).get("selection") == "No"
    
    for step_name, groups in HARDCODED_CHECKLIST_DATA.items():
        if step_name == "Step 2" and skip_step2:
            continue
        for group_name, items in groups.items():
            for item_name in items:
                total += 1
                item_data = checklist_data.get(step_name, {}).get(group_name, {}).get(item_name, {})
                if ("Period" in item_name and item_data.get("from_date") and item_data.get("to_date")) or \
                   ("Period" not in item_name and item_data.get("selection")):
                    completed += 1
    return (completed / total) * 100 if total > 0 else 0

# =====================================================================================
# 4. PAGE RENDERING
# =====================================================================================

def render_dashboard():
    """Displays the main dashboard with all project cards."""
    st.title("📊 Regional Offer Projects Dashboard")
    st.markdown("---")

    # --- New Project Section ---
    with st.expander("🚀 Create a New Project", expanded=False):
        with st.form("new_project_form", clear_on_submit=True):
            project_name = st.text_input("Project Name")
            creator_name = st.text_input("Your Name (Creator)")
            submitted = st.form_submit_button("Create Project")

            if submitted:
                if project_name and creator_name:
                    all_projects = load_projects()
                    if any(p['name'] == project_name for p in all_projects):
                        st.error(f"Project name '{project_name}' already exists.")
                    else:
                        st.session_state.current_project = {
                            "name": project_name,
                            "creator": creator_name,
                            "checklist_data": get_initial_checklist_data()
                        }
                        save_project(st.session_state.current_project)
                        st.session_state.view = 'wizard'
                        st.rerun()
                else:
                    st.warning("Please fill in both Project Name and Creator Name.")

    st.markdown("### All Projects")
    projects = load_projects()
    if not projects:
        st.info("No projects found. Create one above to get started!")
        return

    # --- Project Cards Grid ---
    cols = st.columns(3)
    for i, project in enumerate(sorted(projects, key=lambda p: p.get('last_updated', ''), reverse=True)):
        with cols[i % 3]:
            with st.container(border=True):
                progress = calculate_progress(project['checklist_data'])
                st.markdown(f"**{project['name']}**")
                st.caption(f"Created by: {project.get('creator', 'N/A')}")
                st.progress(int(progress), text=f"{int(progress)}% Complete")
                
                c1, c2 = st.columns(2)
                if c1.button("Continue ➔", key=f"continue_{project['name']}", use_container_width=True):
                    st.session_state.current_project = project
                    st.session_state.view = 'wizard'
                    st.rerun()
                if c2.button("Delete 🗑️", key=f"delete_{project['name']}", use_container_width=True, type="secondary"):
                    delete_project(project['name'])
                    st.rerun()

def render_wizard():
    """Displays the checklist interface for the currently selected project."""
    project = st.session_state.current_project
    project_name = project['name']
    
    st.title(f"📝 Checklist: {project_name}")
    st.caption(f"Created by: {project.get('creator', 'N/A')}")
    st.markdown("---")
    
    # --- Navigation and Saving ---
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("🏠 Back to Dashboard"):
        del st.session_state.current_project
        st.session_state.view = 'dashboard'
        st.rerun()
    
    progress = calculate_progress(project['checklist_data'])
    c2.progress(int(progress), text=f"Overall Progress: {int(progress)}%")

    # --- Tabs for each Step ---
    step_tabs = st.tabs([f"**{s}**" for s in HARDCODED_CHECKLIST_DATA.keys()])
    
    for i, step_name in enumerate(HARDCODED_CHECKLIST_DATA.keys()):
        with step_tabs[i]:
            groups = HARDCODED_CHECKLIST_DATA[step_name]
            for group_name, items in groups.items():
                with st.expander(f"**{group_name}**", expanded=True):
                    for item_name in items:
                        item_data = project['checklist_data'][step_name][group_name][item_name]
                        
                        # Layout for each item
                        cols = st.columns([2, 1, 2])
                        cols[0].markdown(item_name)
                        
                        if "Period" in item_name:
                            # Date inputs
                            from_date_val = datetime.fromisoformat(item_data['from_date']).date() if item_data.get('from_date') else None
                            to_date_val = datetime.fromisoformat(item_data['to_date']).date() if item_data.get('to_date') else None
                            
                            new_from = cols[1].date_input("From", value=from_date_val, key=f"from_{project_name}_{item_name}", label_visibility="collapsed")
                            new_to = cols[1].date_input("To", value=to_date_val, key=f"to_{project_name}_{item_name}", label_visibility="collapsed")
                            
                            # Update data if changed
                            if str(new_from) != str(from_date_val): item_data['from_date'] = new_from.isoformat() if new_from else None
                            if str(new_to) != str(to_date_val): item_data['to_date'] = new_to.isoformat() if new_to else None
                        else:
                            # Selection inputs
                            options = ["", "Yes", "No"]
                            if item_name == "Business Unit":
                                options = ["", "MEAPAC", "La Maison", "ENA", "RIXOS", "Fairmont & Raffles", "China"]
                            
                            current_index = options.index(item_data['selection']) if item_data.get('selection') in options else 0
                            item_data['selection'] = cols[1].selectbox("Selection", options, index=current_index, key=f"sel_{project_name}_{item_name}", label_visibility="collapsed")
                        
                        # Note input
                        item_data['note'] = cols[2].text_input("Note", value=item_data.get('note', ''), key=f"note_{project_name}_{item_name}", label_visibility="collapsed")
    
    # Auto-save changes
    save_project(st.session_state.current_project)


# =====================================================================================
# 5. MAIN APP LOGIC
# =====================================================================================
def main():
    st.set_page_config(layout="wide", page_title="Regional Offer Checklist")

    # Initialize session state
    if "view" not in st.session_state:
        st.session_state.view = "dashboard"

    # Check for database connection
    if not db:
        st.warning("Connecting to the database... If this message persists, please check your Firebase configuration in st.secrets.")
        return

    # View router
    if st.session_state.view == "dashboard":
        render_dashboard()
    elif st.session_state.view == "wizard" and "current_project" in st.session_state:
        render_wizard()
    else:
        st.session_state.view = "dashboard"
        st.rerun()

if __name__ == "__main__":
    main()
