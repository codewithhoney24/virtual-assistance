class Appointment:
    def __init__(self, patient_name: str, doctor_name: str, date: str, time: str):
        """
        Initialize an Appointment object.
        
        Args:
            patient_name (str): Name of the patient.
            doctor_name (str): Name of the doctor.
            date (str): Appointment date.
            time (str): Appointment time.
        """
        self.patient_name = patient_name
        self.doctor_name = doctor_name
        self.date = date
        self.time = time
    
    def confirm_appointment(self) -> str:
        """
        Return a confirmation message for the appointment.
        
        Returns:
            str: Confirmation message.
        """
        if not all([self.patient_name, self.doctor_name, self.date, self.time]):
            return "Appointment details incomplete."
        return f"Appointment confirmed for {self.patient_name} with Dr. {self.doctor_name} on {self.date} at {self.time}."