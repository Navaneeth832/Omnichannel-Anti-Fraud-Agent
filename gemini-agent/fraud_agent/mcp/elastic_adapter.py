from __future__ import annotations

import os
from copy import deepcopy
from typing import List

try:
    from elasticsearch import Elasticsearch
except Exception:  # pragma: no cover - optional dependency
    Elasticsearch = None

from ..utils import dedupe_preserve_order, normalize_identity, normalize_text


_MOCK_REGISTRY = [
    {
        "brand": "State Bank of India",
        "domain": "sbi.co.in",
        "aliases": ["onlinesbi.sbi", "www.onlinesbi.sbi"],
        "official": True,
    },
    {
        "brand": "State Bank of India",
        "domain": "onlinesbi.sbi",
        "aliases": ["onlinesbi.sbi"],
        "official": True,
    },
    {
        "brand": "Central Bureau of Investigation",
        "domain": "cbi.gov.in",
        "aliases": ["cbi.nic.in"],
        "official": True,
    },
    {
        "brand": "Police",
        "domain": "police.gov.in",
        "aliases": ["cybercrime.gov.in"],
        "official": True,
    },
]


def _use_real_backend() -> bool:
    return bool(os.getenv("ELASTIC_NODE")) and bool(os.getenv("ELASTIC_API_KEY")) and Elasticsearch is not None


def _client():
    if not _use_real_backend():
        if os.getenv("STRICT_PRODUCTION_MODE", "false").lower() == "true":
            raise RuntimeError("Elasticsearch is not configured, and STRICT_PRODUCTION_MODE is enabled. Cannot fall back to mock.")
        return None
    try:
        client = Elasticsearch(
            os.getenv("ELASTIC_NODE", ""),
            api_key=os.getenv("ELASTIC_API_KEY", ""),
            request_timeout=1,
            retry_on_timeout=False,
            max_retries=0,
        )
        client.info() # A simple call to check connection
        return client
    except Exception as e:
        if os.getenv("STRICT_PRODUCTION_MODE", "false").lower() == "true":
            raise RuntimeError(f"Failed to connect to Elasticsearch in STRICT_PRODUCTION_MODE: {e}")
        return None


def _index_name() -> str:
    return os.getenv("ELASTICSEARCH_INDEX", "anti-scam-threat-registry")


def levenshtein_distance(left: str, right: str) -> int:
    left = left or ""
    right = right or ""
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)
    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current = [i]
        for j, right_char in enumerate(right, start=1):
            insert_cost = current[j - 1] + 1
            delete_cost = previous[j] + 1
            replace_cost = previous[j - 1] + (left_char != right_char)
            current.append(min(insert_cost, delete_cost, replace_cost))
        previous = current
    return previous[-1]


def levenshtein_similarity(left: str, right: str) -> float:
    left = normalize_identity(left)
    right = normalize_identity(right)
    if not left and not right:
        return 1.0
    longest = max(len(left), len(right), 1)
    return round(1.0 - levenshtein_distance(left, right) / longest, 4)


def jaro_winkler_similarity(left: str, right: str) -> float:
    left = normalize_identity(left)
    right = normalize_identity(right)
    if left == right:
        return 1.0
    if not left or not right:
        return 0.0
    max_distance = max(0, max(len(left), len(right)) // 2 - 1)
    matches_left = [False] * len(left)
    matches_right = [False] * len(right)
    matches = 0

    for i, char in enumerate(left):
        start = max(0, i - max_distance)
        end = min(i + max_distance + 1, len(right))
        for j in range(start, end):
            if matches_right[j]:
                continue
            if char == right[j]:
                matches_left[i] = matches_right[j] = True
                matches += 1
                break

    if matches == 0:
        return 0.0

    left_matches = [left[i] for i, matched in enumerate(matches_left) if matched]
    right_matches = [right[j] for j, matched in enumerate(matches_right) if matched]
    transpositions = sum(l != r for l, r in zip(left_matches, right_matches)) / 2

    jaro = (
        (matches / len(left))
        + (matches / len(right))
        + ((matches - transpositions) / matches)
    ) / 3.0

    prefix = 0
    for left_char, right_char in zip(left, right):
        if left_char == right_char:
            prefix += 1
        else:
            break
        if prefix == 4:
            break
    return round(jaro + prefix * 0.1 * (1.0 - jaro), 4)


def _mock_candidates() -> List[dict]:
    return deepcopy(_MOCK_REGISTRY)


def _fetch_candidates_from_es(search_text: str, size: int = 20) -> List[dict]:
    client = _client()
    if client is None:
        # _client() already handles STRICT_PRODUCTION_MODE, so if it's None here, it means
        # either not in strict mode or it's a mock fallback.
        return _mock_candidates()
    try:
        response = client.search(
            index=_index_name(),
            size=size,
            query={
                "multi_match": {
                    "query": search_text,
                    "fields": [
                        "domain^4",
                        "brand^2",
                        "aliases",
                    ],
                    "fuzziness": "AUTO",
                }
            },
        )
        hits = response.get("hits", {}).get("hits", [])
        candidates = []
        for hit in hits:
            source = hit.get("_source", {})
            source["_score"] = hit.get("_score", 0.0)
            candidates.append(source)
        return candidates
    except Exception as e:
        if os.getenv("STRICT_PRODUCTION_MODE", "false").lower() == "true":
            raise RuntimeError(f"Failed to search Elasticsearch in STRICT_PRODUCTION_MODE: {e}")
        return _mock_candidates()


def search_identity(identity: str) -> dict:
    identity_norm = normalize_text(identity)
    if not identity_norm:
        return {
            "identity_found": False,
            "matches": [],
            "confidence": 0.0,
            "evidence_summary": "No identity was provided.",
        }
    candidates = _fetch_candidates_from_es(identity_norm)
    matches = []
    for candidate in candidates:
        brand = candidate.get("brand", "")
        domain = candidate.get("domain", "")
        aliases = candidate.get("aliases", []) or []
        score = max(
            levenshtein_similarity(identity_norm, brand),
            levenshtein_similarity(identity_norm, domain),
            max((levenshtein_similarity(identity_norm, alias) for alias in aliases), default=0.0),
            jaro_winkler_similarity(identity_norm, brand),
            jaro_winkler_similarity(identity_norm, domain),
            max((jaro_winkler_similarity(identity_norm, alias) for alias in aliases), default=0.0),
        )
        if score >= 0.6:
            matches.append(
                {
                    "brand": brand,
                    "domain": domain,
                    "aliases": list(aliases),
                    "confidence": round(score, 4),
                    "official": bool(candidate.get("official", False)),
                }
            )
    matches.sort(key=lambda item: item["confidence"], reverse=True)
    best = matches[0]["confidence"] if matches else 0.0
    return {
        "identity_found": bool(matches),
        "matches": matches,
        "confidence": round(best, 4),
        "evidence_summary": (
            f"Matched {len(matches)} registry candidate(s) for '{identity}'."
            if matches
            else f"No registry evidence found for '{identity}'."
        ),
    }


def search_domain(domain: str) -> dict:
    domain_norm = normalize_text(domain)
    if domain_norm.startswith("www."):
        domain_norm = domain_norm[4:]
    if not domain_norm:
        return {
            "domain_found": False,
            "official_match": False,
            "matched_candidates": [],
            "typo_squatting_risk": "none",
            "confidence": 0.0,
            "evidence_summary": "No domain was provided.",
            "recommended_interpretation": "No domain evidence available.",
        }
    candidates = _fetch_candidates_from_es(domain_norm)
    matched_candidates = []
    exact_official = False
    for candidate in candidates:
        candidate_domains = [candidate.get("domain", "")] + list(candidate.get("aliases", []) or [])
        for candidate_domain in candidate_domains:
            candidate_domain = normalize_text(candidate_domain)
            if candidate_domain.startswith("www."):
                candidate_domain = candidate_domain[4:]
            if not candidate_domain:
                continue
            lev = levenshtein_similarity(domain_norm, candidate_domain)
            jw = jaro_winkler_similarity(domain_norm, candidate_domain)
            confidence = round((lev * 0.45) + (jw * 0.55), 4)
            if confidence < 0.6 and candidate_domain != domain_norm:
                continue
            matched_candidates.append(
                {
                    "domain": candidate_domain,
                    "brand": candidate.get("brand", ""),
                    "levenshtein_similarity": lev,
                    "jaro_winkler_similarity": jw,
                    "is_official": bool(candidate.get("official", False)),
                    "confidence": confidence,
                }
            )
            if candidate_domain == domain_norm and candidate.get("official", False):
                exact_official = True

    matched_candidates.sort(key=lambda item: item["confidence"], reverse=True)
    best_confidence = matched_candidates[0]["confidence"] if matched_candidates else 0.0
    official_match = exact_official or any(
        item["is_official"] and item["domain"] == domain_norm for item in matched_candidates
    )
    if official_match:
        typo_risk = "none"
    elif best_confidence >= 0.95:
        typo_risk = "critical"
    elif best_confidence >= 0.90:
        typo_risk = "high"
    elif best_confidence >= 0.80:
        typo_risk = "medium"
    elif best_confidence >= 0.65:
        typo_risk = "low"
    else:
        typo_risk = "none"
    return {
        "domain_found": bool(matched_candidates),
        "official_match": official_match,
        "matched_candidates": matched_candidates[:5],
        "typo_squatting_risk": typo_risk,
        "confidence": round(best_confidence, 4),
        "evidence_summary": (
            f"Domain '{domain}' matched {len(matched_candidates)} candidate(s); best confidence {best_confidence:.2f}."
            if matched_candidates
            else f"Domain '{domain}' has no trusted registry match."
        ),
        "recommended_interpretation": (
            "Trusted official domain."
            if official_match
            else "Potential phishing or typo-squatting infrastructure."
        ),
    }


def fuzzy_match_domain(domain: str) -> dict:
    result = search_domain(domain)
    if result["matched_candidates"]:
        top = result["matched_candidates"][0]
        result["best_candidate"] = top
        result["confidence"] = max(result["confidence"], round(top["confidence"], 4))
    else:
        result["best_candidate"] = None
    return result
