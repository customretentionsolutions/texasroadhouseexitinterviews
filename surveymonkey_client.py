"""
Thin wrapper around the SurveyMonkey API for pulling collector responses.

Includes a simple in-memory cache so the client-facing app doesn't hit
SurveyMonkey's API on every single page load (which would be slow and
risks hitting rate limits). Cache resets when the app restarts.
"""

import os
import time
import requests

API_TOKEN = os.environ.get("SURVEYMONKEY_API_TOKEN")
BASE_URL = "https://api.surveymonkey.com/v3"

CACHE_TTL_SECONDS = 15 * 60  # 15 minutes - adjust once we settle on refresh cadence

_cache = {}  # key -> (timestamp, data)


def _headers():
    if not API_TOKEN:
        raise RuntimeError(
            "SURVEYMONKEY_API_TOKEN is not set. Set it as an environment variable."
        )
    return {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
    }


def _cached_get(cache_key, url, params=None):
    now = time.time()
    if cache_key in _cache:
        ts, data = _cache[cache_key]
        if now - ts < CACHE_TTL_SECONDS:
            return data

    resp = requests.get(url, headers=_headers(), params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    _cache[cache_key] = (now, data)
    return data


def get_collector_info(collector_id):
    """Returns collector metadata, including its parent survey_id."""
    url = f"{BASE_URL}/collectors/{collector_id}"
    return _cached_get(f"collector_info:{collector_id}", url)


def get_survey_details(survey_id):
    """Returns full survey structure (pages, questions, answer choices)."""
    url = f"{BASE_URL}/surveys/{survey_id}/details"
    return _cached_get(f"survey_details:{survey_id}", url)


def get_collector_responses(collector_id, per_page=100):
    """
    Returns all completed responses for a single collector, paginating
    through SurveyMonkey's API as needed.
    """
    cache_key = f"responses:{collector_id}"
    now = time.time()
    if cache_key in _cache:
        ts, data = _cache[cache_key]
        if now - ts < CACHE_TTL_SECONDS:
            return data

    all_responses = []
    url = f"{BASE_URL}/collectors/{collector_id}/responses/bulk"
    params = {"per_page": per_page, "page": 1}

    while url:
        resp = requests.get(url, headers=_headers(), params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        all_responses.extend(payload.get("data", []))

        next_link = payload.get("links", {}).get("next")
        if next_link:
            url = next_link
            params = None  # next link already includes query params
        else:
            url = None

    _cache[cache_key] = (now, all_responses)
    return all_responses


def get_brand_responses(collector_ids):
    """Combines responses across multiple collectors for one brand."""
    combined = []
    for cid in collector_ids:
        combined.extend(get_collector_responses(cid))
    return combined


def clear_cache():
    """Manual cache bust, e.g. for a 'refresh now' button."""
    _cache.clear()
