import sys
sys.path.append('gemini-agent')
from fraud_agent.orchestrator import analyze_text
import json

text = "Urgent: Your SBI account is frozen. Call +919999111111 immediately to avoid arrest by CBI."
result = analyze_text(text)
print(json.dumps(result, indent=2))
