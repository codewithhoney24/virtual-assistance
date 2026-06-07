import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client

def send_real_email(to_email: str, subject: str, body: str) -> tuple[bool, str]:
    """
    Sends a real email using SMTP (configured for Gmail by default).
    Requires SENDER_EMAIL and SENDER_PASSWORD (App Password) in .env.
    """
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")

    if not sender_email or not sender_password:
        return False, "⚠️ Credentials missing. Add SENDER_EMAIL and SENDER_PASSWORD to .env"

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Using Gmail SMTP Server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        return True, "✅ Real Email sent successfully!"
    except Exception as e:
        return False, f"❌ Email Failed: {str(e)}"

def send_real_whatsapp(to_phone: str, body: str) -> tuple[bool, str]:
    """
    Sends a real WhatsApp message using the Twilio API.
    Requires TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER in .env.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

    if not account_sid or not auth_token or not twilio_number:
        return False, "⚠️ Twilio credentials missing. Add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER to .env"

    try:
        client = Client(account_sid, auth_token)
        
        # Twilio API requires 'whatsapp:' prefix
        from_whatsapp = f"whatsapp:{twilio_number}"
        
        # Ensure the destination number has the prefix and country code
        to_phone = to_phone.strip()
        if not to_phone.startswith('+'):
            return False, "❌ WhatsApp Failed: Phone number must include country code (e.g., +1234567890)"
            
        to_whatsapp = f"whatsapp:{to_phone}"
        
        message = client.messages.create(
            body=body,
            from_=from_whatsapp,
            to=to_whatsapp
        )
        return True, f"✅ Real WhatsApp sent! (Message SID: {message.sid})"
    except Exception as e:
        return False, f"❌ WhatsApp Failed: {str(e)}"