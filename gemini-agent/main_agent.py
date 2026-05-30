from pydantic import BaseModel
from google.adk.agents import Agent

# 1️⃣ Define the nested components of your schema
class BehavioralAnalysis(BaseModel):
    artificial_urgency: float
    social_coercion: float
    institutional_deviation: float

class DetectedEntities(BaseModel):
    institution: str
    phone_number: str
    website: str
    payment_method: str

class VerificationResults(BaseModel):
    mongodb_check: str
    elastic_check: str

# 2️⃣ Define the main Threat Report model bringing it all together
class ThreatReport(BaseModel):
    case_id: str
    timestamp: str
    threat_score: float
    risk_level: str
    fraud_type: str
    behavioral_analysis: BehavioralAnalysis
    detected_entities: DetectedEntities
    verification_results: VerificationResults
    reasoning_summary: str
    recommended_action: str
    guardian_alert_required: bool
    blacklist_candidate: bool

# 3️⃣ Load up your system prompt
with open("system_prompt/fraud_topology.txt", "r") as f:
    fraud_prompt = f.read()

# 4️⃣ Build the agent and lock in the output schema! 🚀
root_agent = Agent(
    name="fraud_detector",
    model="gemini-2.5-flash",
    instruction=fraud_prompt,
    output_schema=ThreatReport  # 👈 Boom! This forces the model to return the exact JSON structure
)