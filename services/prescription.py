import qrcode
import os

class Prescription:
    def __init__(self, patient_name: str, medicines: list):
        """
        Initialize a Prescription object.
        
        Args:
            patient_name (str): Name of the patient.
            medicines (list): List of prescribed medicines.
        """
        self.patient_name = patient_name
        self.medicines = medicines if medicines else []
    
    def generate_qr(self) -> str:
        """
        Generate a QR code containing prescription details and save it to a file.
        
        Returns:
            str: Path to the generated QR code image.
        """
        if not self.patient_name or not self.medicines:
            return "Prescription details incomplete."
        
        prescription_data = f"Patient: {self.patient_name}\nMedicines: {', '.join(self.medicines)}"
        
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(prescription_data)
        qr.make(fit=True)
        
        qr_dir = "qr_codes"
        if not os.path.exists(qr_dir):
            os.makedirs(qr_dir)
        
        qr_path = os.path.join(qr_dir, f"prescription_{self.patient_name.replace(' ', '_')}.png")
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(qr_path)
        
        return qr_path