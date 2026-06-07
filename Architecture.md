# NexusHealth AI: System Architecture

NexusHealth AI is an advanced Multi-Agent Telemedicine Platform built with Python, Streamlit, and Google Gemini. It automates patient triage, appointment scheduling, and clinical documentation while enforcing strict medical safety standards.

---

## 1. High-Level Architecture

The system follows a **Modular Monolith** architecture with a role-based frontend and a tool-equipped AI backend.

### Components:
- **Frontend (UI Layer):** Streamlit-based SPA (Single Page Application) with role-based navigation.
- **AI Decision Engine:** Google Gemini (1.5-flash/pro) integrated with Function Calling (Tools).
- **Service Layer:** Independent services for Appointment booking, Digital Prescriptions (QR), and Notifications.
- **Data Persistence:** Local flat-file DB (`appointments_db.pkl`) using Python's `pickle` for reliable serialization.

---

## 2. AI Agentic Workflows

The platform utilizes a **Dual-Agent Architecture** to manage clinical and administrative tasks.

### A. Autonomous Clinical Triage Agent
- **Logic:** Triggered in the Patient Portal during Step 1.
- **Process:** Analyzes raw symptoms -> Determines Urgency Level -> Suggests **Recommended Specialization**.
- **Resilience:** Includes a **Local Heuristic Fallback** that uses keyword matching if the Google API is rate-limited (429).

### B. 24/7 Autonomous Booking Agent
- **Logic:** Powering the 'Support Desk'.
- **Tools:** Equipped with `get_available_doctors`, `check_doctor_availability`, and `create_appointment`.
- **Decision Engine:** Enforces **Medical Routing Safety**. It validates user requests against triage recommendations. If a user tries to book a mismatched specialist (e.g., Cardiologist for a headache), the agent pauses and issues a structured warning.

---

## 3. Medical Routing & Safety Logic

The platform implements a safety-first "Routing Logic" to prevent incorrect doctor assignments:
1. **Triage:** Symptoms are mapped to a specialty (e.g., Chest Pain -> Cardiology).
2. **Matching:** The system fetches the requested doctor's specialty.
3. **Validation:** If `Recommended Specialty != Requested Specialty`, the system blocks the booking and prompts for user override.

---

## 4. Integration & Service Layer

- **Digital Prescriptions:** Generates unique QR codes for each prescription, allowing patients to scan and view details on mobile.
- **Email Service (SMTP):** Connects to Gmail SMTP to send live confirmation emails to patients.
- **WhatsApp Service (Twilio):** Uses the Twilio Messaging API to send real-time appointment alerts to patient mobile numbers.

---

## 5. Persistence & State Management

- **Session State:** Managed by Streamlit (`st.session_state`) for real-time UI updates and chat history.
- **Permanent Storage:** Every database change (booking, deletion, prescription) is serialized to `appointments_db.pkl`. This ensures history survives browser refreshes and server restarts.

---

## 6. Technical Stack

| Layer | Technology |
| :--- | :--- |
| **Language** | Python 3.10+ |
| **Frontend** | Streamlit |
| **AI Model** | Google Gemini API (Multimodal) |
| **Data Handling** | Pandas, Pickle |
| **Communication** | Twilio API, smtplib |
| **Branding** | Custom CSS3 (NexusHealth Design System) |

---

## 7. Security & Compliance
- **HIPAA Simulation:** Implements encrypted connection UI indicators and strict data separation between roles.
- **Secure Key Management:** Sensitive API keys are managed via `.env` files and never exposed in the frontend.