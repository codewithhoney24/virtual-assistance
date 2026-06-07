import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime, timedelta

# PAGE CONFIGURATION
st.set_page_config(page_title="NexusHealth AI Assistant", page_icon="⚕️", layout="wide", initial_sidebar_state="expanded")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.logger import log_info
from users.patient import Patient
from users.doctor import Doctor
from services.prescription import Prescription
from services.notifications import send_real_email, send_real_whatsapp
from chatbot.chatbot_engine import ChatBot
from services.database_manager import init_db, add_appointment, get_all_appointments, update_appointment_status, delete_appointment, check_availability
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Database on startup
init_db()

# --- INIT STATE ---
if 'bot' not in st.session_state:
    st.session_state.bot = ChatBot()

if 'triage_result' not in st.session_state:
    st.session_state.triage_result = None

if 'conflict_data' not in st.session_state:
    st.session_state.conflict_data = None

if 'active_consultation_id' not in st.session_state:
    st.session_state.active_consultation_id = None

if 'authenticated_role' not in st.session_state:
    st.session_state.authenticated_role = None

# Mock Doctor Database for smart routing
doctors_db = [
    {"name": "Dr. Sarah Smith", "specialty": "General Physician"},
    {"name": "Dr. John Doe", "specialty": "General Physician"},
    {"name": "Dr. Alan Turing", "specialty": "Neurologist"},
    {"name": "Dr. Grace Hopper", "specialty": "Neurologist"},
    {"name": "Dr. Lovelace", "specialty": "Cardiologist"}
]

# --- CUSTOM MODERN CSS ---
st.markdown("""
<style>
    .stApp { background-color: #f4f7fb; font-family: 'Inter', -apple-system, sans-serif; }
    .role-header { font-weight: 800; font-size: 2.5rem; margin-top: 0.5rem; margin-bottom: 0.2rem; }
    .sub-text { color: #64748b; font-size: 1.1rem; margin-bottom: 1.5rem; }
    .trust-banner { background-color: #dcfce7; border: 1px solid #bbf7d0; color: #166534; padding: 10px 15px; border-radius: 8px; font-size: 0.9rem; display: flex; align-items: center; margin-bottom: 20px; font-weight: 500; }
    .badge { padding: 5px 12px; border-radius: 20px; font-weight: 700; font-size: 0.85rem; display: inline-block; }
    .badge-emergency { background-color: #fee2e2; color: #991b1b; border: 1px solid #f87171; }
    .badge-urgent { background-color: #ffedd5; color: #9a3412; border: 1px solid #fdba74; }
    .badge-routine { background-color: #e0f2fe; color: #075985; border: 1px solid #7dd3fc; }
    .badge-low { background-color: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }
    .history-card { background: white; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 10px; }
    
    /* Global Permanent Scrollbar */
    *::-webkit-scrollbar { width: 10px !important; height: 10px !important; display: block !important; }
    *::-webkit-scrollbar-track { background: #f1f5f9 !important; border-radius: 10px !important; }
    *::-webkit-scrollbar-thumb { background-color: #cbd5e1 !important; border-radius: 10px !important; border: 2px solid #f1f5f9 !important; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR LOGIN & NAV ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2966/2966327.png", width=60)
    st.markdown("### Platform Access")
    
    # Role Selection
    role_view = st.radio("Select Role:", ["👤 Patient Portal", "👨‍⚕️ Doctor Dashboard", "🛡️ System Admin", "🎧 24/7 Support Desk"])
    st.divider()

    # Simple Role-Based Authentication
    if role_view in ["👨‍⚕️ Doctor Dashboard", "🛡️ System Admin"]:
        if st.session_state.authenticated_role != role_view:
            st.markdown(f"#### 🔐 {role_view} Login")
            password = st.text_input("Enter Password", type="password")
            if st.button("Login"):
                # Simplified production password check
                if (role_view == "👨‍⚕️ Doctor Dashboard" and password == "doctor123") or \
                   (role_view == "🛡️ System Admin" and password == "admin123"):
                    st.session_state.authenticated_role = role_view
                    st.success("Authenticated!")
                    st.rerun()
                else:
                    st.error("Invalid Credentials")
            st.stop() # Block content until authenticated
        else:
            if st.button("Logout"):
                st.session_state.authenticated_role = None
                st.rerun()

    st.caption("Production SQLite DB Active ✅")

# --- MAIN APP HEADER ---
st.markdown("""
<div style="text-align: center; padding: 10px 0 30px 0;">
    <h1 style="font-weight: 900; color: #1e3a8a; margin-bottom: 0; display: flex; align-items: center; justify-content: center; gap: 12px;">
        <img src="https://cdn-icons-png.flaticon.com/512/2966/2966327.png" width="45"> NexusHealth AI
    </h1>
    <p style="color: #64748b; font-size: 1.1rem; margin-top: 0;">Your Intelligent Virtual Health Assistant & Telemedicine Platform</p>
</div>
""", unsafe_allow_html=True)
st.divider()

# ==========================================
#         PATIENT PORTAL VIEW
# ==========================================
if role_view == "👤 Patient Portal":
    st.markdown("<div class='trust-banner'>🔒 Connection Encrypted | HIPAA & GDPR Compliance Simulation Active</div>", unsafe_allow_html=True)
    st.markdown("<h1 class='role-header'>Welcome, Patient</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1.5, 1], gap="large")
    
    with col1:
        st.markdown("### Step 1: Preliminary Clinical Assessment")
        with st.container(border=True):
            triage_symptoms = st.text_area("Describe your symptoms in detail:", height=120, placeholder="E.g., Severe headache...")
            
            if st.button("Initiate Clinical Assessment", type="primary", use_container_width=True):
                if triage_symptoms:
                    with st.spinner("Analyzing symptoms..."):
                        st.session_state.triage_result = st.session_state.bot.triage_symptoms(triage_symptoms)
                else:
                    st.warning("Please enter your symptoms first.")

            if st.session_state.triage_result:
                res = st.session_state.triage_result
                urgency = res.get('urgency', 'Unknown')
                badge_class = f"badge-{urgency.lower().replace(' ', '-')}" if urgency.lower() != "system busy" else "badge-low"
                
                st.markdown("---")
                st.markdown(f"**Assessed Urgency:** <span class='badge {badge_class}'>{urgency.upper()}</span>", unsafe_allow_html=True)
                st.markdown(f"**🩺 Recommended Specialization:** {res.get('recommended_specialization', 'General Physician')}")
                st.info(f"**Agent Recommendation:** {res.get('recommendation', '')}")

    with col2:
        st.markdown("### Step 2: Book Appointment")
        if st.session_state.conflict_data:
            c_data = st.session_state.conflict_data
            st.error(f"⚠️ **Schedule Conflict:** {c_data['req_doc']} is booked on {c_data['req_date']}.")
            
            if st.button(f"📅 Book {c_data['req_doc']} on {c_data['alt_date']}", use_container_width=True):
                c_data['appt_record']['appointment_date'] = c_data['alt_date']
                add_appointment(c_data['appt_record'])
                st.success("✅ Rescheduled & Confirmed!")
                st.session_state.conflict_data = None
                st.rerun()
            
            if c_data['alt_doc']:
                if st.button(f"👨‍⚕️ See {c_data['alt_doc']['name']} instead", use_container_width=True):
                    c_data['appt_record']['doctor_name'] = c_data['alt_doc']['name']
                    c_data['appt_record']['specialization'] = c_data['alt_doc']['specialty']
                    add_appointment(c_data['appt_record'])
                    st.success("✅ Routed & Confirmed!")
                    st.session_state.conflict_data = None
                    st.rerun()
        else:
            with st.container(border=True):
                with st.form("booking_form"):
                    p_name = st.text_input("Full Name")
                    p_age = st.number_input("Age", min_value=0, value=30)
                    p_email = st.text_input("Email")
                    p_phone = st.text_input("WhatsApp Number")
                    doc_options = [f"{d['name']} ({d['specialty']})" for d in doctors_db]
                    d_selection = st.selectbox("Select Available Doctor", doc_options)
                    a_date = st.date_input("Date")
                    a_time = st.time_input("Time")
                    
                    if st.form_submit_button("Confirm Booking", type="primary", use_container_width=True):
                        if not st.session_state.triage_result:
                            st.error("Please complete Step 1 first.")
                        elif not p_name or not p_email:
                            st.error("Contact details required.")
                        else:
                            d_name = d_selection.split(" (")[0]
                            spec = d_selection.split("(")[1].replace(")", "")
                            
                            new_record = {
                                "patient_name": p_name, "patient_age": p_age, "patient_email": p_email, "patient_phone": p_phone,
                                "doctor_name": d_name, "specialization": spec, "appointment_date": str(a_date), "appointment_time": str(a_time),
                                "symptoms": triage_symptoms, "triage_result": st.session_state.triage_result
                            }
                            
                            if not check_availability(d_name, str(a_date)):
                                # Conflict logic
                                alt_doc = next((d for d in doctors_db if d['specialty'] == spec and d['name'] != d_name and check_availability(d['name'], str(a_date))), None)
                                st.session_state.conflict_data = {"req_doc": d_name, "req_date": str(a_date), "alt_date": str(a_date + timedelta(days=1)), "alt_doc": alt_doc, "appt_record": new_record}
                                st.rerun()
                            else:
                                add_appointment(new_record)
                                st.success("✅ Appointment Confirmed!")
                                send_real_email(p_email, "Booking Confirmation", f"Confirmed with {d_name} on {a_date}")

# ==========================================
#     DOCTOR DASHBOARD VIEW
# ==========================================
elif role_view == "👨‍⚕️ Doctor Dashboard":
    st.markdown("<h1 class='role-header'>Clinical Command Center</h1>", unsafe_allow_html=True)
    
    appointments = get_all_appointments()
    col_q, col_c = st.columns([1.2, 2.5], gap="large")
    
    with col_q:
        st.markdown("### 📋 Patient Queue")
        if not appointments:
            st.info("No active appointments.")
        else:
            for appt in appointments:
                with st.container():
                    st.markdown("<div class='history-card'>", unsafe_allow_html=True)
                    urgency = appt['triage_result'].get('urgency', 'Routine')
                    color = "🟢" if appt['completed'] else ("🔴" if urgency.lower()=="emergency" else "🟠")
                    st.markdown(f"**{color} {appt['patient_name']}**")
                    st.caption(f"{appt['appointment_date']} | {appt['doctor_name']}")
                    
                    if st.button("🩺 Consult", key=f"c_{appt['id']}", use_container_width=True):
                        st.session_state.active_consultation_id = appt['id']
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

    with col_c:
        if st.session_state.active_consultation_id:
            active_appt = next((a for a in appointments if a['id'] == st.session_state.active_consultation_id), None)
            if active_appt:
                st.markdown(f"### 🩺 Consulting: {active_appt['patient_name']}")
                t1, t2 = st.tabs(["Clinical Data", "E-Prescribing"])
                
                with t1:
                    st.info(f"**AI Triage Summary:**\n{active_appt['triage_result'].get('doctor_summary', 'N/A')}")
                    st.write(f"**Symptom Record:** {active_appt['symptoms']}")
                
                with t2:
                    is_done = st.checkbox("Visit Complete", value=active_appt['completed'])
                    if is_done:
                        with st.form(f"rx_{active_appt['id']}"):
                            meds = st.text_input("Prescribe Medications", value=", ".join(active_appt['prescription']['medicines']) if active_appt['prescription'] else "")
                            if st.form_submit_button("Sign & Generate QR"):
                                rx_data = {"patient": active_appt['patient_name'], "medicines": [m.strip() for m in meds.split(",")], "date": str(datetime.now())}
                                update_appointment_status(active_appt['id'], True, rx_data)
                                st.success("Prescription Logged.")
                                st.rerun()
                    else:
                        update_appointment_status(active_appt['id'], False)

# ==========================================
#     SYSTEM ADMIN VIEW
# ==========================================
elif role_view == "🛡️ System Admin":
    st.markdown("<h1 class='role-header'>Admin Panel</h1>", unsafe_allow_html=True)
    appointments = get_all_appointments()
    if appointments:
        df = pd.DataFrame(appointments)
        st.metric("Total Volume", len(df))
        st.dataframe(df[['patient_name', 'doctor_name', 'appointment_date', 'completed']], use_container_width=True)
        
        record_to_del = st.selectbox("Delete Record:", [f"{a['id']}: {a['patient_name']}" for a in appointments], index=None)
        if st.button("🗑️ Delete Permanently") and record_to_del:
            delete_appointment(int(record_to_del.split(":")[0]))
            st.success("Deleted.")
            st.rerun()

# ==========================================
#     24/7 SUPPORT DESK VIEW
# ==========================================
elif role_view == "🎧 24/7 Support Desk":
    st.markdown("<h1 class='role-header'>24/7 Support Agent</h1>", unsafe_allow_html=True)
    if 'support_messages' not in st.session_state:
        st.session_state.support_messages = [{"role": "assistant", "content": "How can I help you today?"}]

    for m in st.session_state.support_messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if query := st.chat_input("Type here..."):
        st.session_state.support_messages.append({"role": "user", "content": query})
        with st.chat_message("user"): st.markdown(query)
        with st.spinner("AI Agent executing..."):
            response = st.session_state.bot.respond(query, st.session_state)
        st.session_state.support_messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"): st.markdown(response)
        st.rerun()