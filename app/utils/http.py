# app/utils/http.py
"""Helpers para llamadas HTTP y manejo de retries (placeholder).
Usa requests o httpx en implementaciones reales.
"""
import requests
from typing import Any, Dict




def post_json(url: str, payload: Dict[str, Any], headers: Dict[str, str] = None, timeout: int = 60):
    headers = headers or {"Content-Type": "application/json"}
    resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()
                
    return resp.json()