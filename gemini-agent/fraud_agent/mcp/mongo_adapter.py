from __future__ import annotations

import os
from copy import deepcopy
from datetime import datetime, timezone
from typing import Iterable, Optional

try:
    from pymongo import MongoClient
except Exception:  # pragma: no cover - optional dependency
    MongoClient = None

from ..utils import normalize_identity, normalize_text


_MOCK_INSTITUTION_RULES = [
    {
        "institution": "State Bank of India",
        "aliases": ["SBI", "SBI Bank", "State Bank", "State Bank of India"],
        "allowed_communication_channels": [
            "official website",
            "registered email",
            "branch visit",
            "verified app",
            "official customer care",
        ],
        "prohibited_channels": [
            "whatsapp",
            "personal mobile",
            "telegram",
            "signal",
            "unverified domains",
        ],
        "legal_proceedings_conducted_via_video": False,
        "immediate_financial_settlement_allowed_over_phone": False,
    },
    {
        "institution": "Central Bureau of Investigation",
        "aliases": ["CBI", "Central Bureau", "CBI India"],
        "allowed_communication_channels": [
            "official office",
            "registered email",
            "court notice",
            "official website",
        ],
        "prohibited_channels": [
            "whatsapp",
            "telegram",
            "signal",
            "personal mobile",
            "video arrest",
        ],
        "legal_proceedings_conducted_via_video": False,
        "immediate_financial_settlement_allowed_over_phone": False,
    },
    {
        "institution": "Police",
        "aliases": ["Cyber Police", "Local Police", "Police Department"],
        "allowed_communication_channels": [
            "official notice",
            "station visit",
            "court notice",
            "official office",
        ],
        "prohibited_channels": [
            "whatsapp",
            "personal mobile",
            "telegram",
            "signal",
            "video arrest",
        ],
        "legal_proceedings_conducted_via_video": False,
        "immediate_financial_settlement_allowed_over_phone": False,
    },
]

_MOCK_BLACKLIST = [
    {
        "offender_identity": "+919999111111",
        "identity_type": "phone_number",
        "reported_carrier_platform": "whatsapp",
        "claimed_persona": "SBI officer",
        "calculated_threat_score": 0.94,
        "scam_type": "banking_impersonation",
        "timestamp_logged": "2026-05-29T16:32:11Z",
    }
]


def _use_real_backend() -> bool:
    return bool(os.getenv("MONGODB_URI")) and MongoClient is not None


def _get_db_collection(collection_name: str):
    if not _use_real_backend():
        if os.getenv("STRICT_PRODUCTION_MODE", "false").lower() == "true":
            raise RuntimeError("MongoDB is not configured, and STRICT_PRODUCTION_MODE is enabled. Cannot fall back to mock.")
        return None
    uri = os.getenv("MONGODB_URI", "")
    database_name = os.getenv("MONGODB_DATABASE", "fraud_agent")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=1000)
        # Attempt a quick operation to verify connection
        client.admin.command('ping')
        return client[database_name][collection_name]
    except Exception as e:
        if os.getenv("STRICT_PRODUCTION_MODE", "false").lower() == "true":
            raise RuntimeError(f"Failed to connect to MongoDB in STRICT_PRODUCTION_MODE: {e}")
        return None


def _normalize_rule_record(record: dict, matched_alias: Optional[str] = None) -> dict:
    if not record:
        return {}
    normalized = deepcopy(record)
    normalized["aliases"] = list(normalized.get("aliases", []) or [])
    normalized["allowed_communication_channels"] = list(
        normalized.get("allowed_communication_channels", []) or []
    )
    normalized["prohibited_channels"] = list(
        normalized.get("prohibited_channels", []) or []
    )
    normalized["legal_proceedings_conducted_via_video"] = bool(
        normalized.get("legal_proceedings_conducted_via_video", False)
    )
    normalized["immediate_financial_settlement_allowed_over_phone"] = bool(
        normalized.get("immediate_financial_settlement_allowed_over_phone", False)
    )
    normalized["matched_alias"] = matched_alias or normalized.get("institution", "")
    return normalized


def _matches_identity(candidate: str, target: str) -> bool:
    if not candidate or not target:
        return False
    candidate_norm = normalize_identity(candidate)
    target_norm = normalize_identity(target)
    if candidate_norm == target_norm:
        return True
    candidate_text = normalize_text(candidate)
    target_text = normalize_text(target)
    return candidate_text in target_text or target_text in candidate_text


def _iter_mock_rules():
    yield from _MOCK_INSTITUTION_RULES


def _iter_real_rules():
    collection = _get_db_collection("InstitutionalRules")
    if collection is None:
        return []
    try:
        return list(collection.find({}))
    except Exception:
        return []


def get_institution_rules(institution_name: str) -> dict:
    candidates = _iter_real_rules() if _use_real_backend() else list(_iter_mock_rules())
    for record in candidates:
        institution = record.get("institution", "")
        aliases = record.get("aliases", []) or []
        if _matches_identity(institution, institution_name):
            return _normalize_rule_record(record, matched_alias=institution)
        for alias in aliases:
            if _matches_identity(alias, institution_name):
                return _normalize_rule_record(record, matched_alias=alias)
    return {}


def _blacklist_collection():
    return _get_db_collection("ThreatBlacklist")


def _iter_blacklist_records() -> Iterable[dict]:
    if _use_real_backend():
        collection = _blacklist_collection()
        if collection is None:
            return []
        try:
            return list(collection.find({}))
        except Exception:
            return []
    return list(_MOCK_BLACKLIST)


def lookup_blacklist(identity: str) -> Optional[dict]:
    if not identity:
        return None
    for record in _iter_blacklist_records():
        offender_identity = record.get("offender_identity", "")
        if _matches_identity(offender_identity, identity):
            normalized = deepcopy(record)
            normalized["offender_identity"] = offender_identity
            return normalized
    return None


def save_blacklist_entry(record: dict) -> dict:
    payload = {
        "offender_identity": record.get("offender_identity", ""),
        "identity_type": record.get("identity_type", "unknown"),
        "reported_carrier_platform": record.get("reported_carrier_platform", ""),
        "claimed_persona": record.get("claimed_persona", ""),
        "calculated_threat_score": float(record.get("calculated_threat_score", 0.0)),
        "scam_type": record.get("scam_type", "unknown"),
        "timestamp_logged": record.get(
            "timestamp_logged",
            datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        ),
    }
    if _use_real_backend():
        collection = _blacklist_collection()
        if collection is not None:
            try:
                collection.update_one(
                    {
                        "offender_identity": payload["offender_identity"],
                        "identity_type": payload["identity_type"],
                    },
                    {"$set": payload},
                    upsert=True,
                )
            except Exception:
                pass
    else:
        for index, existing in enumerate(_MOCK_BLACKLIST):
            if (
                normalize_identity(existing.get("offender_identity", ""))
                == normalize_identity(payload["offender_identity"])
                and existing.get("identity_type", "") == payload["identity_type"]
            ):
                _MOCK_BLACKLIST[index] = payload
                return deepcopy(payload)
        _MOCK_BLACKLIST.append(payload)
    return deepcopy(payload)

