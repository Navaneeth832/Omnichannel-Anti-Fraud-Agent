import sys
sys.path.append('gemini-agent')
from fraud_agent.config import get_settings
settings = get_settings()
print(f'Gemini Key: {settings.gemini_api_key[:5]}...')
print(f'Twilio SID: {settings.twilio_account_sid[:5]}...')
print(f'Threshold: {settings.fraud_alert_threshold}')
