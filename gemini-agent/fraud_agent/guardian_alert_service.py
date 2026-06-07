import os
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Try to import Twilio and SendGrid clients
try:
    from twilio.rest import Client as TwilioClient
except ImportError:
    TwilioClient = None
    logging.warning("Twilio client not installed. Twilio alerts will be disabled.")

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
except ImportError:
    SendGridAPIClient = None
    Mail = None
    logging.warning("SendGrid client not installed. SendGrid alerts will be disabled.")

def _send_twilio_sms(to_phone_number: str, message_body: str) -> Dict[str, Any]:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")

    if not all([account_sid, auth_token, twilio_phone_number]):
        logging.error("Twilio credentials or phone number missing. Cannot send SMS.")
        return {"status": "failed", "message": "Twilio credentials or phone number missing."}

    if TwilioClient is None:
        logging.error("Twilio client not available. Cannot send SMS.")
        return {"status": "failed", "message": "Twilio client not available."}

    try:
        client = TwilioClient(account_sid, auth_token)
        message = client.messages.create(
            to=to_phone_number,
            from_=twilio_phone_number,
            body=message_body
        )
        logging.info(f"Twilio SMS sent successfully. SID: {message.sid}")
        return {"status": "success", "sid": message.sid}
    except Exception as e:
        logging.error(f"Failed to send Twilio SMS: {e}")
        return {"status": "failed", "message": str(e)}

def _send_sendgrid_email(to_email: str, subject: str, html_content: str) -> Dict[str, Any]:
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("SENDGRID_FROM_EMAIL")

    if not all([sendgrid_api_key, from_email]):
        logging.error("SendGrid API key or sender email missing. Cannot send email.")
        return {"status": "failed", "message": "SendGrid API key or sender email missing."}

    if SendGridAPIClient is None or Mail is None:
        logging.error("SendGrid client not available. Cannot send email.")
        return {"status": "failed", "message": "SendGrid client not available."}

    try:
        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )
        sendgrid_client = SendGridAPIClient(sendgrid_api_key)
        response = sendgrid_client.send(message)
        logging.info(f"SendGrid email sent successfully. Status Code: {response.status_code}")
        return {"status": "success", "status_code": response.status_code, "body": response.body}
    except Exception as e:
        logging.error(f"Failed to send SendGrid email: {e}")
        return {"status": "failed", "message": str(e)}

def send_fraud_alert(
    threat_score: float,
    case_id: str,
    summary: str,
    customer_contact: Dict[str, str]
) -> Dict[str, Any]:
    """
    Sends fraud alerts based on threat score and available contact information.
    """
    alert_results = {}
    alert_threshold = float(os.getenv("FRAUD_ALERT_THRESHOLD", "0.8"))

    if threat_score >= alert_threshold:
        logging.info(f"Threat score {threat_score} >= alert threshold {alert_threshold}. Sending alerts for case {case_id}.")

        alert_message = f"FRAUD ALERT! Case ID: {case_id}. Threat Score: {threat_score:.2f}. Summary: {summary}"
        alert_subject = f"Fraud Alert: Case {case_id} - Threat Score {threat_score:.2f}"

        # Send SMS via Twilio
        if "phone" in customer_contact and customer_contact["phone"]:
            logging.info(f"Attempting to send Twilio SMS to {customer_contact['phone']}")
            twilio_result = _send_twilio_sms(customer_contact["phone"], alert_message)
            alert_results["twilio_sms"] = twilio_result
        else:
            logging.info("No customer phone number provided for Twilio SMS.")
            alert_results["twilio_sms"] = {"status": "skipped", "message": "No customer phone number."}

        # Send Email via SendGrid
        if "email" in customer_contact and customer_contact["email"]:
            logging.info(f"Attempting to send SendGrid email to {customer_contact['email']}")
            sendgrid_result = _send_sendgrid_email(customer_contact["email"], alert_subject, f"<p>{alert_message}</p>")
            alert_results["sendgrid_email"] = sendgrid_result
        else:
            logging.info("No customer email provided for SendGrid email.")
            alert_results["sendgrid_email"] = {"status": "skipped", "message": "No customer email."}
    else:
        logging.info(f"Threat score {threat_score} < alert threshold {alert_threshold}. No alerts sent for case {case_id}.")
        alert_results = {"status": "skipped", "message": "Threat score below alert threshold."}

    return alert_results

if __name__ == "__main__":
    # Example usage (for testing purposes)
    # Set environment variables before running this block
    os.environ["TWILIO_ACCOUNT_SID"] = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    os.environ["TWILIO_AUTH_TOKEN"] = "your_auth_token"
    os.environ["TWILIO_PHONE_NUMBER"] = "+15017122661"
    os.environ["SENDGRID_API_KEY"] = "SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    os.environ["SENDGRID_FROM_EMAIL"] = "test@example.com"
    os.environ["FRAUD_ALERT_THRESHOLD"] = "0.8"

    print("--- Testing send_fraud_alert with high threat score ---")
    results_high = send_fraud_alert(
        threat_score=0.9,
        case_id="CASE-12345",
        summary="Suspicious activity detected on account.",
        customer_contact={"phone": "+1234567890", "email": "customer@example.com"}
    )
    print(results_high)

    print("\n--- Testing send_fraud_alert with low threat score ---")
    results_low = send_fraud_alert(
        threat_score=0.7,
        case_id="CASE-67890",
        summary="Minor anomaly detected.",
        customer_contact={"phone": "+1234567890", "email": "customer@example.com"}
    )
    print(results_low)
