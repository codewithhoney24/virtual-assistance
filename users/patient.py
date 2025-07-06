class Patient:
    def __init__(self, name: str, age: int, email: str, symptoms: list):
        """
        Initialize a Patient object.
        
        Args:
            name (str): Patient's name.
            age (int): Patient's age.
            email (str): Patient's email.
            symptoms (list): List of symptoms.
        """
        self.name = name
        self.age = age
        self.email = email
        self.symptoms = symptoms if symptoms else []
    
    def get_details(self) -> str:
        """
        Return a formatted string of patient details.
        
        Returns:
            str: Patient details.
        """
        return f"Name: {self.name}, Age: {self.age}, Email: {self.email}"
    
    def describe_symptoms(self) -> str:
        """
        Return a formatted string of patient symptoms.
        
        Returns:
            str: Symptoms description or a message if none provided.
        """
        if not self.symptoms:
            return "No symptoms provided."
        return f"Symptoms: {', '.join(self.symptoms)}"