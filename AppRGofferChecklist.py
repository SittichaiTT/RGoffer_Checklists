import streamlit as st
import gspread
import pandas as pd
import json
import datetime
from google.oauth2 import service_account

# --- Configuration ---
# Theme Colors (Python dictionary for consistency) - Adjusted for better contrast
THEME_COLORS = {
    "primary_bg": "#F0F2F6",  # สีเทาอ่อนสำหรับพื้นหลังหลัก
    "secondary_bg": "#FFFFFF",  # สีขาวสำหรับส่วนต่างๆ
    "text_dark": "#2C3E50",   # สีดำเข้มขึ้นเพื่อให้อ่านง่าย
    "text_light": "#7F8C8D",  # สีเทากลางสำหรับข้อความรอง
    "button_primary": "#3498DB",  # สีน้ำเงินสดใส
    "button_primary_hover": "#2980B9", # สีน้ำเงินเข้มขึ้นเมื่อวางเมาส์
    "button_secondary": "#BDC3C7", # สีเทาอ่อนสำหรับปุ่มรอง
    "button_secondary_hover": "#95A5A6", # สีเทาเข้มขึ้นเมื่อวางเมาส์
    "button_disabled": "#E0E0E0", # สีเทาอ่อนสำหรับปุ่มที่ปิดใช้งาน
    "progress_yellow": "#F39C12", # สีเหลืองสดใสขึ้น
    "progress_blue": "#3498DB",   # สอดคล้องกับสีปุ่มหลัก
    "progress_green": "#2ECC71",  # สีเขียวสดใสขึ้น
    "border_color": "#D5DBDB", # สีขอบที่เข้มขึ้นเล็กน้อย
    "placeholder_text": "#B2BABB", # สีเทาอ่อนสำหรับข้อความ Placeholder
    "dropdown_fg": "#2C3E50", # สีข้อความเข้มสำหรับ Dropdown
    "dropdown_hover": "#ECF0F1", # สีอ่อนเมื่อวางเมาส์บน Dropdown
    "sub_group_underline": "#3498DB" # สอดคล้องกับสีหลัก
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

# --- Helper Functions ---
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

    # Determine if Step 2 should be active for progress calculation
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

# --- Google Sheets Integration ---
@st.cache_resource(ttl=3600)
def get_gspread_client():
    """Initializes and caches the gspread client using service account credentials."""
    try:
        # Load credentials from Streamlit secrets
        # Ensure 'gcp_service_account' key exists in .streamlit/secrets.toml
        # with 'type', 'project_id', 'private_key_id', 'private_key', 'client_email', etc.
        credentials_info = json.loads(st.secrets["gcp_service_account"])
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        gc = gspread.authorize(credentials)
        st.success("Google Sheets client initialized successfully!") # Added for debugging
        return gc
    except Exception as e:
        st.error(f"Error initializing Google Sheets client: {e}")
        st.info("โปรดตรวจสอบให้แน่ใจว่าข้อมูลรับรองบัญชีบริการ Google Cloud ของคุณได้รับการกำหนดค่าอย่างถูกต้องใน `.streamlit/secrets.toml` และเปิดใช้งาน Google Sheets/Drive API แล้ว")
        return None

@st.cache_data(ttl=60) # Cache data for 60 seconds to avoid excessive API calls
def load_projects_from_sheet(gc, sheet_name="Regional Offer Projects"):
    """Loads all projects from a specified Google Sheet."""
    if gc is None: # Added check for client
        st.warning("Google Sheets client not initialized. Cannot load projects.")
        return pd.DataFrame(columns=["user_id", "project_name", "progress", "summary", "checklist_data"])
    try:
        spreadsheet = gc.open(sheet_name)
        worksheet = spreadsheet.worksheet("Projects") # Assuming a worksheet named "Projects"
        data = worksheet.get_all_records() # Get all data as a list of dictionaries
        df = pd.DataFrame(data)
        st.success(f"Successfully loaded {len(df)} projects from Google Sheet.") # Added for debugging
        return df
    except gspread.exceptions.SpreadsheetNotFound:
        st.warning(f"Google Sheet '{sheet_name}' ไม่พบ. โปรดสร้างและแชร์กับบัญชีบริการ.")
        return pd.DataFrame(columns=["user_id", "project_name", "progress", "summary", "checklist_data"])
    except gspread.exceptions.WorksheetNotFound:
        st.warning(f"Worksheet 'Projects' ไม่พบใน '{sheet_name}'. โปรดสร้าง.")
        return pd.DataFrame(columns=["user_id", "project_name", "progress", "summary", "checklist_data"])
    except Exception as e:
        st.error(f"Error loading projects from Google Sheet: {e}")
        return pd.DataFrame(columns=["user_id", "project_name", "progress", "summary", "checklist_data"])

def save_project_to_sheet(gc, user_id, project_name, progress, summary, checklist_data, sheet_name="Regional Offer Projects"):
    """Saves or updates a project in the Google Sheet."""
    if gc is None: # Added check for client
        st.error("Google Sheets client not initialized. Cannot save project.")
        return
    try:
        spreadsheet = gc.open(sheet_name)
        worksheet = spreadsheet.worksheet("Projects")

        # Load existing data to find the row
        df = load_projects_from_sheet(gc, sheet_name)
        
        # Find if project exists for this user
        existing_row_index = -1
        if not df.empty:
            matching_rows = df[(df['user_id'] == user_id) & (df['project_name'] == project_name)]
            if not matching_rows.empty:
                # gspread is 1-indexed, pandas is 0-indexed. Plus header row.
                existing_row_index = matching_rows.index[0] + 2 

        if existing_row_index != -1:
            # Update existing row
            worksheet.update_cell(existing_row_index, df.columns.get_loc('progress') + 1, progress)
            worksheet.update_cell(existing_row_index, df.columns.get_loc('summary') + 1, summary)
            worksheet.update_cell(existing_row_index, df.columns.get_loc('checklist_data') + 1, json.dumps(checklist_data))
            st.success(f"Project '{project_name}' updated successfully!")
        else:
            # Add new row
            new_row = [user_id, project_name, progress, summary, json.dumps(checklist_data)]
            worksheet.append_row(new_row)
            st.success(f"Project '{project_name}' created successfully!")
        
        # Invalidate cache so next load_projects_from_sheet gets fresh data
        load_projects_from_sheet.clear()

    except Exception as e:
        st.error(f"Error saving project to Google Sheet: {e}")

def delete_project_from_sheet(gc, user_id, project_name, sheet_name="Regional Offer Projects"):
    """Deletes a project from the Google Sheet."""
    if gc is None: # Added check for client
        st.error("Google Sheets client not initialized. Cannot delete project.")
        return
    try:
        spreadsheet = gc.open(sheet_name)
        worksheet = spreadsheet.worksheet("Projects")

        # Load existing data to find the row
        df = load_projects_from_sheet(gc, sheet_name)
        
        # Find rows matching user_id and project_name
        matching_rows = df[(df['user_id'] == user_id) & (df['project_name'] == project_name)]

        if not matching_rows.empty:
            # gspread is 1-indexed, pandas is 0-indexed. Plus header row.
            row_to_delete = matching_rows.index[0] + 2 
            worksheet.delete_rows(row_to_delete)
            st.success(f"Project '{project_name}' deleted successfully!")
        else:
            st.warning(f"Project '{project_name}' ไม่พบสำหรับการลบ.")
        
        # Invalidate cache
        load_projects_from_sheet.clear()

    except Exception as e:
        st.error(f"Error deleting project from Google Sheet: {e}")

# --- UI Components ---

def render_dashboard(gc_client, user_id, user_email):
    """Renders the project dashboard view."""
    st.markdown(f"<h1 style='color:{THEME_COLORS['text_dark']}; font-size: 2.5em; font-weight: bold; margin-bottom: 2rem;'>ภาพรวมโครงการข้อเสนอภูมิภาค</h1>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("🚀 เริ่มโครงการใหม่", use_container_width=True):
            st.session_state.show_project_prompt = True
    with col2:
        st.info(f"เข้าสู่ระบบในฐานะ: {user_email} (User ID: {user_id})", icon="👤")

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
                    st.session_state.show_project_prompt = False
                    st.rerun() # Rerun to switch view
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

        projects_df = load_projects_from_sheet(gc_client, "Regional Offer Projects")
        
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
                            delete_project_from_sheet(gc_client, user_id, project['project_name'])
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
        st.markdown(f"<h3 style='color:{THEME_COLORS['text_dark']}; font-size: 1.25em; font-weight: bold; margin-bottom: 1rem;'>กิจกรรมล่าสุด (บันทึกตัวอย่าง)</h3>", unsafe_allow_html=True)
        dummy_logs = [
            "2024-07-18 10:00 AM: โครงการ 'Summer Campaign 2025' เริ่มต้นโดย User ABC.",
            "2024-07-18 10:15 AM: User ABC อัปเดต 'Business Unit' เป็น 'MEAPAC' ใน 'Summer Campaign 2025'.",
            "2024-07-18 11:00 AM: User XYZ ดำเนินการต่อ 'Winter Promo 2024'.",
            "2024-07-17 03:30 PM: โครงการ 'Holiday Deals' ถูกลบโดย User PQR.",
            "2024-07-16 09:00 AM: สร้างโครงการใหม่ 'Q4 Launch' โดย User LMN."
        ]
        for log in dummy_logs:
            st.markdown(f"<p style='color:{THEME_COLORS['text_light']}; font-size: 0.875em;'>{log}</p>", unsafe_allow_html=True)
    
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

    # Step Indicators
    step_cols = st.columns(len(steps))
    for i, step in enumerate(steps):
        is_step2_disabled = (i == 1 and checklist_values.get('Step 1', {}).get("TK (Check if existing please follow 'CLEAN UP')", {}).get("selection") == "No")
        button_style = f"background-color: {THEME_COLORS['button_primary'] if i == current_step_index else (THEME_COLORS['button_disabled'] if is_step2_disabled else THEME_COLORS['button_secondary'])}; color: white; font-weight: bold; padding: 0.5rem 1rem; border-radius: 0.5rem; border: none; cursor: {'not-allowed' if is_step2_disabled else 'pointer'}; transition: background-color 0.2s;"
        
        with step_cols[i]:
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
            
            item_cols = st.columns([0.2, 0.5, 0.3]) # Adjust column widths for better layout

            with item_cols[0]:
                if "Booking Period" in item_name or "Stay Period" in item_name:
                    # Streamlit date_input returns datetime.date object. Convert to string for storage.
                    selected_from_date = st.date_input(f"จาก: {item_name}", 
                                  value=datetime.datetime.strptime(item_state["from_date"], "%Y-%m-%d").date() if item_state["from_date"] else None,
                                  key=f"from_date_{current_step_name}_{item_name}")
                    if selected_from_date:
                        checklist_values[current_step_name][item_name]["from_date"] = str(selected_from_date)
                    else:
                        checklist_values[current_step_name][item_name]["from_date"] = ""

                    selected_to_date = st.date_input(f"ถึง: {item_name}", 
                                  value=datetime.datetime.strptime(item_state["to_date"], "%Y-%m-%d").date() if item_state["to_date"] else None,
                                  key=f"to_date_{current_step_name}_{item_name}")
                    if selected_to_date:
                        checklist_values[current_step_name][item_name]["to_date"] = str(selected_to_date)
                    else:
                        checklist_values[current_step_name][item_name]["to_date"] = ""

                elif item_name == "Business Unit":
                    selection_options = ["", "MEAPAC", "La Maion", "ENA", "RIXOS", "Fairmont & Raffles", "China"]
                    selected_bu = st.selectbox(item_name, selection_options, 
                                 index=selection_options.index(item_state["selection"]) if item_state["selection"] in selection_options else 0,
                                 key=f"select_{current_step_name}_{item_name}")
                    checklist_values[current_step_name][item_name]["selection"] = selected_bu
                else:
                    selection_options = ["", "Yes", "No"]
                    selected_option = st.selectbox(item_name, selection_options, 
                                 index=selection_options.index(item_state["selection"]) if item_state["selection"] in selection_options else 0,
                                 key=f"select_{current_step_name}_{item_name}")
                    checklist_values[current_step_name][item_name]["selection"] = selected_option
            
            with item_cols[1]:
                st.markdown(f"<p style='color:{THEME_COLORS['text_dark']}; font-size: 1em; font-weight: 500;'>{item_name}</p>", unsafe_allow_html=True)

            with item_cols[2]:
                note_value = st.text_input("บันทึก", value=item_state["note"], key=f"note_{current_step_index}_{item_name}")
                checklist_values[current_step_name][item_name]["note"] = note_value
            
            st.markdown("---") # Separator for items

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
            save_project_to_sheet(gc_client, user_id, current_project_name, current_project_progress, summary_text, checklist_values)
            st.rerun() # Rerun to refresh dashboard data if user goes back

# --- Main App Logic ---
def main():
    st.set_page_config(layout="wide", page_title="Regional Offer Checklist App")

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
            padding: 0.75rem 1.5rem;
            font-weight: bold;
            transition: background-color 0.2s, transform 0.2s;
            border: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
        .stSelectbox > div > div {{
            border-radius: 0.5rem;
            border-color: {THEME_COLORS['border_color']};
            background-color: {THEME_COLORS['primary_bg']};
            color: {THEME_COLORS['text_dark']};
        }}
        .stTextInput > div > div > input {{
            border-radius: 0.5rem;
            border-color: {THEME_COLORS['border_color']};
            background-color: {THEME_COLORS['primary_bg']};
            color: {THEME_COLORS['text_dark']};
        }}
        .stTextArea > div > div > textarea {{
            border-radius: 0.5rem;
            border-color: {THEME_COLORS['border_color']};
            background-color: {THEME_COLORS['primary_bg']};
            color: {THEME_COLORS['text_dark']};
        }}
        .stDateInput > label + div > div {{
            border-radius: 0.5rem;
            border-color: {THEME_COLORS['border_color']};
            background-color: {THEME_COLORS['primary_bg']};
            color: {THEME_COLORS['text_dark']};
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
    </style>
    """, unsafe_allow_html=True)

    # Initialize session state variables if they don't exist
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
    if 'search_term' not in st.session_state:
        st.session_state.search_term = ''
    if 'filter_year' not in st.session_state:
        st.session_state.filter_year = 'All Years'
    if 'filter_month' not in st.session_state:
        st.session_state.filter_month = 'All Months'
    if 'confirm_delete_project' not in st.session_state:
        st.session_state.confirm_delete_project = None


    # --- Authentication (Simplified for local testing) ---
    # For a real app, you'd integrate with st-oauth or similar.
    # Here, we'll simulate a logged-in user with a dummy ID and email.
    # In a real deployed app, you'd replace this with actual Google OAuth.
    user_id = "dummy_user_id_123" # Replace with actual authenticated user ID
    user_email = "dummy.user@example.com" # Replace with actual authenticated user email

    # Initialize Google Sheets client
    gc_client = get_gspread_client()
    # If gc_client is None, it means there was an error initializing.
    # The error message is already displayed by get_gspread_client.
    # We can add a check here to prevent further execution if the client is not ready.
    if gc_client is None:
        st.stop() # Stop the app if Google Sheets client cannot be initialized

    # Render appropriate view
    if st.session_state.view == 'dashboard':
        render_dashboard(gc_client, user_id, user_email)
    elif st.session_state.view == 'wizard':
        render_wizard(gc_client, user_id)

if __name__ == "__main__":
    main()
