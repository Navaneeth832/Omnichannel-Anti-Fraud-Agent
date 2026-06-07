# Member 1 Phase 3 Integration Setup

## Environment Variables

Set these values in your local `.env` or deployment secret store:

- `MONGODB_URI` - MongoDB connection string for the `InstitutionalRules` and `ThreatBlacklist` collections
- `ELASTIC_NODE` - Elasticsearch cluster endpoint
- `ELASTIC_API_KEY` - Elasticsearch API key
- `ELASTICSEARCH_INDEX` - Elasticsearch index name, defaults to `anti-scam-threat-registry`

## Where The Connections Go

- MongoDB reads `MONGODB_URI`
- Elasticsearch reads `ELASTIC_NODE`, `ELASTIC_API_KEY`, and `ELASTICSEARCH_INDEX`

## Connection Verification

You can verify the adapters by running the test suite or by importing the orchestrator in Python:

```python
from fraud_agent.orchestrator import analyze_text

result = analyze_text("CBI officer on WhatsApp asking for urgent payment")
print(result["risk_level"], result["threat_score"])
```

If the real services are configured, the adapters will use them automatically. If the environment variables are missing, the code falls back to the built-in mock registry and mock blacklist so you can still run local tests.

## Running Tests

From the repository root:

```bash
pytest
```

If you want to focus only on the fraud integration tests:

```bash
pytest tests/test_phase3_integration.py
```

## Switching Between Mock And Real Services

- Leave `MONGODB_URI` unset to use the mock MongoDB dataset
- Leave `ELASTIC_NODE` and `ELASTIC_API_KEY` unset to use the mock Elasticsearch registry
- Set the variables above to point at your live services to use real backends

The orchestrator does not need code changes when switching modes. It reads the active environment on each run and selects the appropriate backend automatically.

