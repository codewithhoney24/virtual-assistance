import streamlit as st
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.logger import log_info
from users.patient import Patient
from users.doctor import Doctor
from services.appoinment import Appointment
from services.prescription import Prescription
from chatbot.chatbot_engine import ChatBot
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Download NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
except Exception as e:
    st.error(f"Failed to download NLTK data: {e}")

# Initialize chatbot
bot = ChatBot()

# Streamlit app
st.title("🩺 Virtual Health Assistant")

# Initialize session state
if 'patient' not in st.session_state:
    st.session_state.patient = None
if 'doctor' not in st.session_state:
    st.session_state.doctor = None
if 'appointment' not in st.session_state:
    st.session_state.appointment = None
if 'prescription' not in st.session_state:
    st.session_state.prescription = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'visit_completed' not in st.session_state:
    st.session_state.visit_completed = False
if 'prescription_meds' not in st.session_state:
    st.session_state.prescription_meds = ""
if 'next_appointment' not in st.session_state:
    st.session_state.next_appointment = None
if 'visit_status' not in st.session_state:
    st.session_state.visit_status = "Visit Incomplete"

# Patient, Doctor, and Appointment Form
with st.form("health_form"):
    st.header("👤 Patient Details")
    p_name = st.text_input("Patient Name", key="patient_name_input")
    p_age = st.number_input("Patient Age", min_value=0, max_value=150, value=30, key="patient_age_input")
    p_email = st.text_input("Patient Email", key="patient_email_input")
    symptoms = st.text_input("Symptoms (comma-separated)", key="symptoms_input")

    st.header("🩻 Doctor Details")
    d_name = st.text_input("Doctor Name", key="doctor_name_input")
    specialization = st.selectbox("Doctor Specialization", [
        "Cardiologist", "Dermatologist", "Neurologist", "Pediatrician", "Gynecologist",
        "Orthopedic Surgeon", "Psychiatrist", "ENT Specialist", "Dentist"
    ], key="doctor_specialization_input")
    d_experience = st.selectbox("Doctor Experience/Expertise", ["MBBS", "FCPS", "MD", "MS", "DPT", "Other"],
                                key="doctor_experience_input")

    st.header("📅 Appointment Details")
    appointment_date = st.date_input("Appointment Date", key="appointment_date_input")
    appointment_time = st.time_input("Appointment Time", key="appointment_time_input")

    submit_button = st.form_submit_button("Submit")

# Doctor's Visit Status Checkbox
visit_completed_checkbox = st.checkbox("Doctor's Visit is Complete", key="visit_complete_checkbox")
st.session_state.visit_completed = visit_completed_checkbox

# Handle form submission
if submit_button:
    if not p_name or not p_email or not symptoms:
        st.error("Please fill in all patient details.")
    elif not d_name or not specialization or not d_experience:
        st.error("Please fill in all doctor details.")
    else:
        # Create and store objects
        patient = Patient(p_name, p_age, p_email, [s.strip() for s in symptoms.split(",")])
        doctor = Doctor(d_name, specialization, d_experience)
        appointment = Appointment(p_name, d_name, str(appointment_date), str(appointment_time))

        st.session_state.patient = patient
        st.session_state.doctor = doctor
        st.session_state.appointment = appointment

        log_info(f"Form submitted for patient: {p_name}")

        # Display Information
        st.subheader("🧍 Patient Details")
        st.write(patient.get_details())
        st.write(patient.describe_symptoms())

        st.subheader("👨‍⚕️ Doctor Details")
        st.write(doctor.get_details())
        st.write(doctor.get_specialization())

        st.subheader("📅 Appointment Details")
        st.write(appointment.confirm_appointment())

        # Display visit status message
        if st.session_state.get('visit_status') == "Visit Complete":
            st.success("Doctor's visit marked as complete. Prescription details will be handled separately.")
        else:
            st.info("Doctor's visit is incomplete. Prescription cannot be issued yet.")

# Conditionally display and handle Prescription Details
if st.session_state.patient:
    if st.session_state.visit_completed:
        with st.form("prescription_form", clear_on_submit=True):
            st.header("💊 Prescription Details")
            meds = st.text_input("Medicines (comma-separated)", key="prescription_meds_input")
            prescription_submit_button = st.form_submit_button("Submit")

            if prescription_submit_button:
                if meds:
                    prescription = Prescription(st.session_state.patient.name, [m.strip() for m in meds.split(",")])
                    st.session_state.prescription = prescription
                    qr_path = prescription.generate_qr()

                    st.subheader("Issued Prescription")
                    st.write(f"Medicines: {', '.join(prescription.medicines)}")
                    st.image(qr_path, caption="Prescription QR Code")
                else:
                    st.warning("Please enter medicines for the prescription.")
    else:
        st.info("Please mark the Doctor's Visit as Complete to issue a prescription.")
else:
    st.info("Please fill out Patient, Doctor, and Appointment details first to proceed with the visit status and prescription.")

# Chatbot Interface
st.header("💬 Chat with Virtual Health Assistant")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if query := st.chat_input("Ask a question:"):
    with st.chat_message("user"):
        st.markdown(query)
    st.session_state.messages.append({"role": "user", "content": query})

    response = bot.respond(query, st.session_state)
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
