import os
import json
import pickle
import google.generativeai as genai
from dotenv import load_dotenv

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from users.patient import Patient
from users.doctor import Doctor
from services.database_manager import add_appointment, get_all_appointments, check_availability

load_dotenv()

def get_available_doctors() -> list[dict]:
    """Returns a list of all available doctors and their specialties."""
    return [
        {"name": "Dr. Sarah Smith", "specialty": "General Physician"},
        {"name": "Dr. John Doe", "specialty": "General Physician"},
        {"name": "Dr. Alan Turing", "specialty": "Neurologist"},
        {"name": "Dr. Grace Hopper", "specialty": "Neurologist"},
        {"name": "Dr. Lovelace", "specialty": "Cardiologist"}
    ]

def check_doctor_availability(doctor_name: str, date: str) -> bool:
    """Checks if a doctor is available on a specific date (YYYY-MM-DD). Returns True if available."""
    return check_availability(doctor_name, date)

def create_appointment(patient_name: str, patient_age: int, patient_email: str, patient_phone: str, symptoms: str, doctor_name: str, date: str, time: str) -> str:
    """
    Books an appointment for a patient using the database.
    """
    if not check_doctor_availability(doctor_name, date):
        return f"Failed: {doctor_name} is already booked on {date}. Please try another date or doctor."

    # Find doctor specialty
    docs = get_available_doctors()
    spec = "General Physician"
    for d in docs:
        if d['name'] == doctor_name:
            spec = d['specialty']
            break
            
    try:
        new_record = {
            "patient_name": patient_name,
            "patient_age": patient_age,
            "patient_email": patient_email,
            "patient_phone": patient_phone,
            "doctor_name": doctor_name,
            "specialization": spec,
            "appointment_date": str(date),
            "appointment_time": str(time),
            "symptoms": symptoms,
            "triage_result": {
                "urgency": "Routine", 
                "recommendation": "Agent booked", 
                "doctor_summary": "Booked via 24/7 Agent",
                "recommended_specialization": spec
            }
        }
        add_appointment(new_record)
        return f"Success: Appointment confirmed for {patient_name} with {doctor_name} on {date} at {time}."
    except Exception as e:
        return f"Failed to save appointment: {str(e)}"

class ChatBot:
    # Class-level caching to prevent redundant model discovery across Streamlit reloads
    _cached_model_no_tools = None
    _cached_model_with_tools = None

    def __init__(self):
        """
        Initialize the ChatBot with Google Gemini API.
        """
        self.api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            
        self.chat_session = None
        
        self.responses = {
            "hello": "Hi! I'm your Autonomous Health Agent. How can I help you today?",
            "help": "I can assess your symptoms, check doctor availability, and book appointments for you."
        }

    def update_api_key(self, new_key: str):
        """Allows updating the API key at runtime to bypass .env caching issues."""
        self.api_key = new_key
        os.environ["GOOGLE_GEMINI_API_KEY"] = new_key
        genai.configure(api_key=self.api_key)
        # Reset caches to force re-initialization with new key
        ChatBot._cached_model_no_tools = None
        ChatBot._cached_model_with_tools = None
        self.chat_session = None

    def _get_working_model(self, with_tools=False):
        """
        Dynamically finds and returns a working model, using class-level cache for extreme speed.
        Probes the API exactly once per session to ensure compatibility.
        """
        if with_tools and ChatBot._cached_model_with_tools:
            return ChatBot._cached_model_with_tools
        elif not with_tools and ChatBot._cached_model_no_tools:
            return ChatBot._cached_model_no_tools

        preferred_models = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro', 'gemini-pro']
        tools_list = [get_available_doctors, check_doctor_availability, create_appointment] if with_tools else None
        
        working_model = None
        
        # Try preferred models
        for model_name in preferred_models:
            try:
                m = genai.GenerativeModel(model_name, tools=tools_list)
                # MUST probe once to ensure it doesn't 404 later
                m.generate_content("test")
                working_model = m
                break
            except Exception:
                continue
                
        # If all preferred fail, list available and pick first
        if not working_model:
            try:
                available_models = []
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        available_models.append(m.name.replace('models/', ''))
                
                if available_models:
                    working_model = genai.GenerativeModel(available_models[0], tools=tools_list)
                else:
                    raise Exception("No models supporting generateContent found for this API key.")
            except Exception as e:
                raise Exception(f"Failed to find any working models. Error: {str(e)}")
                
        # Cache the working model
        if with_tools:
            ChatBot._cached_model_with_tools = working_model
        else:
            ChatBot._cached_model_no_tools = working_model
            
        return working_model

    def _get_chat_session(self):
        if self.chat_session is None:
            try:
                model = self._get_working_model(with_tools=True)
                self.chat_session = model.start_chat(enable_automatic_function_calling=True)
                
                # AI Telemedicine Decision Engine Instruction
                system_instruction = """System Instruction: You are the NexusHealth AI, a comprehensive Autonomous Healthcare Assistant.
Your primary tasks are medical safety through smart doctor routing, autonomous appointment booking, and providing reliable healthcare information.

SCOPE & CAPABILITIES:
- You CAN and SHOULD provide general information about common medical tests, healthy living, and clinical procedures (always add a disclaimer that you aren't a doctor).
- You KNOW how this platform works: Patients book in the 'Patient Portal', Doctors consult in the 'Command Center', and digital prescriptions with QR codes are generated after a consultation is marked complete.
- You can autonomously book appointments using tools.

CRITICAL RULES FOR BOOKING/SWITCHING:
1. Always perform symptom-based triage first. Identify the medical category.
2. Fetch available doctors using get_available_doctors().
3. Compare: (a) Symptoms -> Recommended specialization vs (b) Requested doctor's specialization.
4. Decision Logic:
   - IF MATCH: Proceed to book using create_appointment().
   - IF MISMATCH: DO NOT book immediately. Show a warning using this EXACT format:

"Your symptoms suggest a [Recommended Specialization] consultation.

Recommended Doctor: [Recommended Doctor Name] ([Recommended Specialization])

Current Appointment/Requested: [Requested Doctor Name] ([Requested Specialization])

This is not the best match for your condition.

Would you like to:
1) Switch to [Recommended Doctor Name] (Recommended)
2) Keep [Requested/Current Doctor]"

5. Wait for confirmation before booking if a mismatch occurred.

CONVERSATIONAL GUIDELINES:
- Be empathetic and professional.
- If a user asks for a test recommendation, give them common clinical examples (e.g. ECG for heart) but advise seeing a doctor.
- If a user asks about prescriptions, explain that they are generated as QR codes in the 'Consultation' tab after the doctor finishes the visit."""
                
                self.chat_session.send_message(system_instruction)
            except Exception:
                # Fallback to no-tools if there's an SDK issue
                model = self._get_working_model(with_tools=False)
                self.chat_session = model.start_chat()
        return self.chat_session

    def _generate_content_robust(self, prompt: str):
        model = self._get_working_model()
        return model.generate_content(prompt)

    def _local_heuristic_triage(self, symptoms: str) -> dict:
        """
        A local keyword-based fallback to allow the UI to proceed when the API is rate-limited.
        """
        s = symptoms.lower()
        spec = "General Physician"
        urgency = "Routine"
        
        # Simple heuristic mapping
        if any(kw in s for kw in ["chest", "heart", "palpitation", "breath"]):
            spec = "Cardiologist"
            urgency = "Urgent"
        elif any(kw in s for kw in ["head", "confused", "dizzy", "seizure", "numb"]):
            spec = "Neurologist"
            urgency = "Urgent"
        elif any(kw in s for kw in ["kid", "child", "baby"]):
            spec = "Pediatrician"
        elif any(kw in s for kw in ["stomach", "vomit", "diarrhea"]):
            spec = "Gastroenterologist"
        
        if any(kw in s for kw in ["unconscious", "bleeding", "severe", "cannot breathe"]):
            urgency = "Emergency"

        return {
            "urgency": urgency,
            "recommendation": f"Note: Using local assessment (API busy). Based on your symptoms, a {spec} is recommended.",
            "doctor_summary": f"Local Fallback Assessment: {symptoms}",
            "recommended_specialization": spec
        }

    def triage_symptoms(self, symptoms: str) -> dict:
        """
        Uses the Gemini model to analyze symptoms and return a structured triage assessment.
        Falls back to local heuristics if the API is rate-limited.
        """
        if self.api_key == "dummy_key_for_testing":
            return self._local_heuristic_triage(symptoms)

        prompt = f"""
        You are an advanced Autonomous Clinical Triaging Agent operating under strict medical safety guidelines.
        Analyze the following patient symptoms: "{symptoms}"
        
        Provide a structured JSON output with EXACTLY these four keys:
        1. "urgency": String (Must be one of: "Low", "Routine", "Urgent", "Emergency")
        2. "recommendation": String (A brief, empathetic instruction for the patient. If "Emergency", explicitly tell them to call 911/999 immediately.)
        3. "doctor_summary": String (A concise, clinical summary of the symptoms for the attending physician to read on their dashboard.)
        4. "recommended_specialization": String (The exact medical specialization best suited for these symptoms, e.g., "Cardiologist", "Neurologist", "General Physician").
        
        Return ONLY valid JSON. No markdown formatting, no backticks.
        """
        
        try:
            response = self._generate_content_robust(prompt)
            raw_text = response.text.strip()
            # Clean potential markdown block formatting returned by the LLM
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:-3].strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:-3].strip()
                
            return json.loads(raw_text)
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                # FIX: Fallback to local heuristic so the user isn't blocked!
                return self._local_heuristic_triage(symptoms)
            
            # Try to list models to help debugging
            try:
                models = [m.name for m in genai.list_models()]
                debug_info = f"Available models for this key: {', '.join(models)}"
            except Exception:
                debug_info = "Could not fetch available models."
                
            return {
                "urgency": "Error",
                "recommendation": f"Triage failed. The API key might be invalid or restricted. Proceed to book appointment manually.",
                "doctor_summary": f"API Error: {error_msg} | {debug_info}",
                "recommended_specialization": "Unknown"
            }

    def _local_conversational_fallback(self, query: str) -> str:
        """Provides a simple rule-based response when the API is rate-limited."""
        q = query.lower()
        if any(kw in q for kw in ["test", "diagnostic", "checkup"]):
            return "📋 **Local Info (API Busy):** For symptoms like chest pain, common tests include ECG, Blood work, and X-rays. For headaches, a Neurological exam may be needed. Please consult a doctor for a formal referral."
        if any(kw in q for kw in ["prescription", "download", "qr", "medicine"]):
            return "💊 **Local Info (API Busy):** Digital prescriptions are generated as QR codes in the 'Consultation' tab after the doctor marks the visit as complete."
        if any(kw in q for kw in ["book", "appointment", "schedule"]):
            return "📅 **Local Info (API Busy):** You can book appointments in the 'Patient Portal' or wait a moment for the AI agent to become available to book it for you here."
        return "⏳ **System Busy:** I am currently experiencing high traffic. Please try again in 1 minute, or use the 'Patient Portal' for immediate manual booking."

    def respond(self, query: str, session_state: dict) -> str:
        """
        Generate a conversational response and handle autonomous tool calling.
        """
        query_lower = query.lower().strip()
        
        if query_lower in self.responses:
            return self.responses[query_lower]
            
        if self.api_key == "dummy_key_for_testing":
            return "⚠️ **Notice:** Chatbot is currently running on a dummy API key. To get real AI responses, please add your Google Gemini API key to the `.env` file."
            
        try:
            chat = self._get_chat_session()
            response = chat.send_message(query)
            return response.text
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "403" in error_msg or "authentication" in error_msg.lower():
                return "❌ **API Authentication Failed:** Your Google Gemini API Key is invalid, expired, or incorrectly formatted. Please ensure you are using a standard API Key (not an OAuth token) from Google AI Studio, and that it is correctly placed in your `.env` file as `GOOGLE_GEMINI_API_KEY=your_key_here`."
            elif "429" in error_msg or "quota" in error_msg.lower():
                # FIX: Use local conversational fallback so the user isn't stuck!
                return self._local_conversational_fallback(query)
            return f"❌ **System Error:** Could not process query. Details: `{error_msg}`"