from google.adk.agents import Agent

root_agent = Agent(
    name="fraud_detector",
    model="gemini-2.5-flash",
    instruction="""
You are a fraud detection assistant.

Analyze messages for:
- Artificial urgency
- Social coercion
- Institutional impersonation

Return a short fraud assessment.
"""
)