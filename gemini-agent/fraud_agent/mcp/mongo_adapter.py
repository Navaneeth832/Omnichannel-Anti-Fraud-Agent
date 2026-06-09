from __future__ import annotations

import os
from copy import deepcopy
from datetime import datetime, timezone
from typing import Iterable, Optional
from uuid import uuid4
from difflib import SequenceMatcher
try:
    from pymongo import ASCENDING, MongoClient
except ImportError:  # pragma: no cover
    print("no mongo")
    ASCENDING = 1
    MongoClient = None

from ..config import get_settings
from ..utils import normalize_identity, normalize_text

_SEEDED_INSTITUTION_RULES = [
    {"institution": "State Bank of India", "normalized_aliases": ["statebankofindia", "sbi", "sbibank", "statebank"], "aliases": ["SBI", "SBI Bank", "State Bank", "State Bank of India"], "allowed_communication_channels": ["official website", "registered email", "branch visit", "verified app", "official customer care"], "prohibited_channels": ["whatsapp", "personal mobile", "telegram", "signal", "unverified domains"], "legal_proceedings_conducted_via_video": False, "immediate_financial_settlement_allowed_over_phone": False},
    {"institution": "Central Bureau of Investigation", "normalized_aliases": ["centralbureauofinvestigation", "cbi", "centralbureau", "cbiindia"], "aliases": ["CBI", "Central Bureau", "CBI India"], "allowed_communication_channels": ["official office", "registered email", "court notice", "official website"], "prohibited_channels": ["whatsapp", "telegram", "signal", "personal mobile", "video arrest"], "legal_proceedings_conducted_via_video": False, "immediate_financial_settlement_allowed_over_phone": False},
    {"institution": "Police", "normalized_aliases": ["police", "cyberpolice", "localpolice", "policedepartment"], "aliases": ["Cyber Police", "Local Police", "Police Department"], "allowed_communication_channels": ["official notice", "station visit", "court notice", "official office"], "prohibited_channels": ["whatsapp", "personal mobile", "telegram", "signal", "video arrest"], "legal_proceedings_conducted_via_video": False, "immediate_financial_settlement_allowed_over_phone": False},
]

_SEEDED_BLACKLIST = [
    {"offender_identity": "+919999111111", "normalized_identity": "919999111111", "identity_type": "phone_number", "reported_carrier_platform": "whatsapp", "claimed_persona": "SBI officer", "calculated_threat_score": 0.94, "scam_type": "banking_impersonation", "timestamp_logged": "2026-05-29T16:32:11Z"}
]

_MEMORY = {"InstitutionalRules": deepcopy(_SEEDED_INSTITUTION_RULES), "ThreatBlacklist": deepcopy(_SEEDED_BLACKLIST), "Cases": [], "GuardianProfiles": [], "AlertLogs": []}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _use_real_backend() -> bool:
    settings = get_settings()
    return bool(settings.mongodb_uri) and MongoClient is not None


def _db():
    settings = get_settings()
    if not _use_real_backend():
        if settings.strict_production_mode:
            raise RuntimeError("MongoDB unavailable in STRICT_PRODUCTION_MODE. Set MONGODB_URI and install pymongo.")
        return None
    client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=2000)
    client.admin.command("ping")
    return client[settings.mongodb_database]


def _collection(name: str):
    db = _db()
    return None if db is None else db[name]


def ensure_schema_and_indexes() -> None:
    db = _db()
    if db is None:
        return
    validators = {
        "Cases": {"$jsonSchema": {"bsonType": "object", "required": ["case_id", "timestamp", "evidence", "threat_report", "alert_status"], "properties": {"case_id": {"bsonType": "string"}, "timestamp": {"bsonType": "string"}, "evidence": {"bsonType": "object"}, "threat_report": {"bsonType": "object"}, "alert_status": {"bsonType": "string"}}}},
        "GuardianProfiles": {"$jsonSchema": {"bsonType": "object", "required": ["guardian_name", "escalation_enabled"], "properties": {"guardian_name": {"bsonType": "string"}, "guardian_phone": {"bsonType": "string"}, "guardian_email": {"bsonType": "string"}, "escalation_enabled": {"bsonType": "bool"}}}},
        "AlertLogs": {"$jsonSchema": {"bsonType": "object", "required": ["alert_id", "case_id", "provider", "timestamp", "status", "provider_response"], "properties": {"alert_id": {"bsonType": "string"}, "case_id": {"bsonType": "string"}, "provider": {"bsonType": "string"}, "timestamp": {"bsonType": "string"}, "status": {"bsonType": "string"}}}},
    }
    for name, validator in validators.items():
        if name not in db.list_collection_names():
            db.create_collection(name, validator=validator)
        else:
            db.command("collMod", name, validator=validator)
    db.InstitutionalRules.create_index([("normalized_aliases", ASCENDING)], name="idx_normalized_aliases")
    db.ThreatBlacklist.create_index([("normalized_identity", ASCENDING), ("identity_type", ASCENDING)], name="idx_blacklist_identity")
    db.Cases.create_index([("case_id", ASCENDING)], unique=True, name="idx_case_id")
    db.Cases.create_index([("timestamp", ASCENDING)], name="idx_case_timestamp")
    db.GuardianProfiles.create_index([("escalation_enabled", ASCENDING)], name="idx_guardian_escalation")
    db.AlertLogs.create_index([("case_id", ASCENDING), ("timestamp", ASCENDING)], name="idx_alert_case_timestamp")


def _normalize_rule_record(record: dict, matched_alias: Optional[str] = None) -> dict:
    normalized = deepcopy(record)
    normalized.pop("_id", None)
    normalized.setdefault("aliases", [])
    normalized.setdefault("allowed_communication_channels", [])
    normalized.setdefault("prohibited_channels", [])
    normalized["matched_alias"] = matched_alias or normalized.get("institution", "")
    return normalized




def get_institution_rules(institution_name: str) -> dict:
    if not institution_name:
        return {}

    key = normalize_identity(institution_name)

    if _use_real_backend():
        collection = _collection("InstitutionalRules")

        if collection is not None:

            # 1. Exact normalized match
            record = collection.find_one(
                {"normalized_aliases": key},
                {"_id": 0}
            )

            # 2. Exact institution/alias match (case-insensitive)
            if not record:
                record = collection.find_one(
                    {
                        "$or": [
                            {
                                "institution": {
                                    "$regex": f"^{institution_name}$",
                                    "$options": "i"
                                }
                            },
                            {
                                "aliases": {
                                    "$regex": f"^{institution_name}$",
                                    "$options": "i"
                                }
                            }
                        ]
                    },
                    {"_id": 0}
                )

            # 3. Containment + fuzzy fallback
            if not record:
                candidates = list(
                    collection.find(
                        {},
                        {
                            "_id": 0,
                            "institution": 1,
                            "aliases": 1,
                            "normalized_aliases": 1
                        }
                    )
                )

                best_match = None
                best_score = 0.0

                for candidate in candidates:

                    names = [candidate.get("institution", "")]
                    names.extend(candidate.get("aliases", []))
                    names.extend(candidate.get("normalized_aliases", []))

                    for name in names:

                        candidate_key = normalize_identity(str(name))

                        # Fixes:
                        # "Central Bureau of Investigation, Cyber Crime Division (claimed)"
                        # -> matches
                        # "Central Bureau of Investigation"
                        if (
                            candidate_key in key
                            or key in candidate_key
                        ):
                            return _normalize_rule_record(
                                candidate,
                                institution_name
                            )

                        score = SequenceMatcher(
                            None,
                            key,
                            candidate_key
                        ).ratio()

                        if score > best_score:
                            best_score = score
                            best_match = candidate

                if best_score >= 0.75:
                    record = best_match

            return (
                _normalize_rule_record(record, institution_name)
                if record else {}
            )

    # Memory fallback
    for record in _MEMORY["InstitutionalRules"]:

        names = [record.get("institution", "")]
        names.extend(record.get("aliases", []))
        names.extend(record.get("normalized_aliases", []))

        for name in names:

            candidate_key = normalize_identity(str(name))

            if (
                candidate_key == key
                or candidate_key in key
                or key in candidate_key
            ):
                return _normalize_rule_record(
                    record,
                    institution_name
                )

    return {}

def lookup_blacklist(identity: str) -> Optional[dict]:
    if not identity:
        return None
    key = normalize_identity(identity)
    if _use_real_backend():
        collection = _collection("ThreatBlacklist")
        record = collection.find_one({"normalized_identity": key}, {"_id": 0}) if collection is not None else None
        return deepcopy(record) if record else None
    for record in _MEMORY["ThreatBlacklist"]:
        if record.get("normalized_identity") == key:
            return deepcopy(record)
    return None


def save_blacklist_entry(record: dict) -> dict:
    payload = {**record, "normalized_identity": normalize_identity(record.get("offender_identity", "")), "timestamp_logged": record.get("timestamp_logged", _now())}
    if _use_real_backend():
        collection = _collection("ThreatBlacklist")
        if collection is not None:
            collection.update_one({"normalized_identity": payload["normalized_identity"], "identity_type": payload.get("identity_type", "unknown")}, {"$set": payload}, upsert=True)
    else:
        _MEMORY["ThreatBlacklist"] = [item for item in _MEMORY["ThreatBlacklist"] if not (item.get("normalized_identity") == payload["normalized_identity"] and item.get("identity_type") == payload.get("identity_type"))]
        _MEMORY["ThreatBlacklist"].append(deepcopy(payload))
    return deepcopy(payload)


from ..config import get_settings

def get_guardian_profiles() -> list[dict]:
    if _use_real_backend():
        collection = _collection("GuardianProfiles")
        profiles = list(collection.find({"escalation_enabled": True}, {"_id": 0}).sort("guardian_name", ASCENDING))
        if profiles:
            return profiles
    settings = get_settings()
    if settings.trusted_guardian_phone or settings.trusted_guardian_email:
        return [{"guardian_name": settings.trusted_guardian_name, "guardian_phone": settings.trusted_guardian_phone, "guardian_email": settings.trusted_guardian_email, "escalation_enabled": True}]
    return [deepcopy(profile) for profile in _MEMORY["GuardianProfiles"] if profile.get("escalation_enabled")]


def save_case(case_id: str, evidence: dict, threat_report: dict, alert_status: str) -> dict:
    payload = {"case_id": case_id, "timestamp": threat_report.get("timestamp", _now()), "evidence": evidence, "threat_report": threat_report, "alert_status": alert_status}
    if _use_real_backend():
        ensure_schema_and_indexes()
        collection = _collection("Cases")
        if collection is not None:
            collection.update_one({"case_id": case_id}, {"$set": payload}, upsert=True)
    else:
        _MEMORY["Cases"] = [case for case in _MEMORY["Cases"] if case.get("case_id") != case_id]
        _MEMORY["Cases"].append(deepcopy(payload))
    return deepcopy(payload)


def list_cases(limit: int = 50) -> list[dict]:
    if _use_real_backend():
        collection = _collection("Cases")
        return list(collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)) if collection is not None else []
    return sorted(deepcopy(_MEMORY["Cases"]), key=lambda item: item.get("timestamp", ""), reverse=True)[:limit]


def save_alert_log(case_id: str, provider: str, status: str, provider_response: dict) -> dict:
    payload = {"alert_id": f"ALERT-{uuid4().hex[:12].upper()}", "case_id": case_id, "provider": provider, "timestamp": _now(), "status": status, "provider_response": provider_response}
    if _use_real_backend():
        ensure_schema_and_indexes()
        collection = _collection("AlertLogs")
        if collection is not None:
            collection.insert_one(payload)
    else:
        _MEMORY["AlertLogs"].append(deepcopy(payload))
    return deepcopy(payload)


def list_alert_logs(limit: int = 100) -> list[dict]:
    if _use_real_backend():
        collection = _collection("AlertLogs")
        return list(collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)) if collection is not None else []
    return sorted(deepcopy(_MEMORY["AlertLogs"]), key=lambda item: item.get("timestamp", ""), reverse=True)[:limit]
