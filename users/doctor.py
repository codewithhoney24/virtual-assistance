class Doctor:
    def __init__(self, name: str, specialization: str, experience: str):
        """
        Initialize a Doctor object.
        
        Args:
            name (str): Doctor's name.
            specialization (str): Doctor's specialization.
            experience (str): Doctor's experience/expertise.
        """
        self.name = name
        self.specialization = specialization
        self.experience = experience
    
    def get_details(self) -> str:
        """
        Return a formatted string of doctor details.
        
        Returns:
            str: Doctor details.
        """
        return f"Name: {self.name}, Specialization: {self.specialization}, Experience: {self.experience}"
    
    def get_specialization(self) -> str:
        """
        Return the doctor's specialization.
        
        Returns:
            str: Specialization or a message if none provided.
        """
        return f"Specialization: {self.specialization if self.specialization else 'Not specified'}"