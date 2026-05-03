"""
Fetches available models for each provider.
"""
import json
import httpx
from provider_registry import get_provider


def fetch_models(provider_id: str, api_key: str, base_url: str = None) -> list:
    provider = get_provider(provider_id)

    # Use hardcoded list if available
    if provider.get("hardcoded_models"):
        return [{"id": m} for m in provider["hardcoded_models"]]

    effective_url = base_url or provider["base_url"]
    endpoint = provider.get("models_endpoint", "/models")
    if not endpoint:
        return []

    url = f"{effective_url}{endpoint}"
    headers = {}
    if api_key and provider.get("auth_type") == "bearer":
        headers["Authorization"] = f"Bearer {api_key}"
    elif api_key and provider.get("auth_type") == "x-api-key":
        headers["x-api-key"] = api_key
    elif api_key and provider.get("auth_type") == "api-key":
        headers["api-key"] = api_key

    resp = httpx.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if isinstance(data, list):
        return [{"id": m.get("id") or m.get("name")} for m in data if m.get("id") or m.get("name")]
    elif "data" in data:
        return [{"id": m.get("id"), "context_length": m.get("context_length")} for m in data["data"] if m.get("id")]
    elif "models" in data:
        return [{"id": m.get("name") or m.get("id")} for m in data["models"]]
    return []
