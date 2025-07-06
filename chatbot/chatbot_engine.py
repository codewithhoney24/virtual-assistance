import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class ChatBot:
    def __init__(self):
        """
        Initialize the ChatBot with Google Gemini API.
        """
        api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_GEMINI_API_KEY not found in .env file")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.responses = {
            "hello": "Hi! I'm your Virtual Health Assistant. How can I help you today?",
            "help": "I can assist with your symptoms, appointment details, or general health questions. For medical advice, consult a professional."
        }
    
    def respond(self, query: str, session_state: dict) -> str:
        """
        Generate a response to the user's query using Gemini API or predefined responses.
        
        Args:
            query (str): User's query.
            session_state (dict): Streamlit session state containing patient, doctor, etc.
        
        Returns:
            str: Response to the query.
        """
        query = query.lower().strip()
        
        # Handle predefined responses
        if query in self.responses:
            return self.responses[query]
        
        # Handle session-based queries
        if "symptoms" in query and session_state.get('patient'):
            return session_state.patient.describe_symptoms()
        if "appointment" in query and session_state.get('appointment'):
            return session_state.appointment.confirm_appointment()
        if "next appointment" in query or "book appointment" in query:
            return "Doctor se appointment ke liye, Virtual Health Assistant form mein 'Appointment Details' ko dobara fill karein."
        if "prescription" in query and session_state.get('prescription'):
            return f"Medicines: {', '.join(session_state.prescription.medicines)}"
        
        # Use Gemini API for general queries
        try:
            response = self.model.generate_content(
                f"You are a virtual health assistant. Provide a concise, accurate response to the following health-related query, avoiding any sensitive or protected information. If the query is not health-related, respond with a general helpful message. Query: {query}"
            )
            return response.text
        except Exception as e:
            return f"Error processing query: {str(e)}. Please try again or ask a different question."