from __future__ import annotations

import os
from typing import Dict, Any

try:
    from pymongo import MongoClient
except ImportError:
    MongoClient = None

try:
    from elasticsearch import Elasticsearch
except ImportError:
    Elasticsearch = None

from fraud_agent.mcp import mongo_adapter
from fraud_agent.mcp import elastic_adapter

def _get_status(is_connected: bool, is_mock_mode: bool, is_misconfigured: bool) -> str:
    if is_mock_mode:
        return "MOCK_MODE"
    if is_misconfigured:
        return "MISCONFIGURED"
    if is_connected:
        return "CONNECTED"
    return "DISCONNECTED"

def check_gemini_status() -> Dict[str, str]:
    api_key = os.getenv("GEMINI_API_KEY")
    status = _get_status(bool(api_key), False, not bool(api_key))
    return {"status": status}

def check_mongodb_status() -> Dict[str, str]:
    if not mongo_adapter._use_real_backend():
        return {"status": "MOCK_MODE"}

    uri = os.getenv("MONGODB_URI")
    database_name = os.getenv("MONGODB_DATABASE")

    if not uri or not database_name:
        return {"status": "MISCONFIGURED"}

    if MongoClient is None:
        return {"status": "MISCONFIGURED"} # pymongo not installed

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=1000)
        # The ping command is cheap and does not require auth.
        client.admin.command('ping')
        return {"status": "CONNECTED"}
    except Exception:
        return {"status": "DISCONNECTED"}

def check_elasticsearch_status() -> Dict[str, str]:
    if not elastic_adapter._use_real_backend():
        return {"status": "MOCK_MODE"}

    node = os.getenv("ELASTIC_NODE")
    api_key = os.getenv("ELASTIC_API_KEY")

    if not node or not api_key:
        return {"status": "MISCONFIGURED"}

    if Elasticsearch is None:
        return {"status": "MISCONFIGURED"} # elasticsearch client not installed

    try:
        client = Elasticsearch(node, api_key=api_key, request_timeout=1, retry_on_timeout=False, max_retries=0)
        client.info() # A simple call to check connection
        return {"status": "CONNECTED"}
    except Exception:
        return {"status": "DISCONNECTED"}

def check_twilio_status() -> Dict[str, str]:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    status = _get_status(bool(account_sid and auth_token), False, not (bool(account_sid and auth_token)))
    return {"status": status}

def check_sendgrid_status() -> Dict[str, str]:
    api_key = os.getenv("SENDGRID_API_KEY")
    status = _get_status(bool(api_key), False, not bool(api_key))
    return {"status": status}

def check_eventarc_status() -> Dict[str, str]:
    gcp_project_id = os.getenv("GCP_PROJECT_ID")
    status = _get_status(bool(gcp_project_id), False, not bool(gcp_project_id))
    return {"status": status}

def check_cloud_functions_status() -> Dict[str, str]:
    gcp_project_id = os.getenv("GCP_PROJECT_ID")
    status = _get_status(bool(gcp_project_id), False, not bool(gcp_project_id))
    return {"status": status}

def check_system_health() -> Dict[str, Any]:
    return {
        "gemini": check_gemini_status(),
        "mongodb": check_mongodb_status(),
        "elasticsearch": check_elasticsearch_status(),
        "twilio": check_twilio_status(),
        "sendgrid": check_sendgrid_status(),
        "eventarc": check_eventarc_status(),
        "cloud_functions": check_cloud_functions_status(),
    }

if __name__ == "__main__":
    health_report = check_system_health()
    import json
    print(json.dumps(health_report, indent=2))
