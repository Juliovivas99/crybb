"""
Minimal Replicate client for Google nano-banana.
Uses plain requests; no heavy SDKs.
"""
from __future__ import annotations

import time
from typing import List
import requests

from src.retry import retry_http


class AIGenerationError(Exception):
    def __init__(self, message: str, prediction_id: str | None = None):
        super().__init__(message)
        self.prediction_id = prediction_id


@retry_http
def _post_prediction(*, model: str, token: str, prompt: str, image_urls: List[str]) -> dict:
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "version": model,  # Keep this as is
        "input": {
            "prompt": prompt,
            "image_input": image_urls,  # ← Change from "image" to "image_input"
            "aspect_ratio": "match_input_image",  # ← Add this parameter
            "output_format": "jpg",
        },
    }
    r = requests.post(url, json=payload, headers=headers, timeout=30)
    if r.status_code >= 400:
        raise AIGenerationError(f"Replicate POST error {r.status_code}: {r.text}")
    return r.json()


@retry_http
def _get_prediction(*, pred_id: str, token: str) -> dict:
    url = f"https://api.replicate.com/v1/predictions/{pred_id}"
    headers = {"Authorization": f"Token {token}"}
    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code >= 400:
        raise AIGenerationError(f"Replicate GET error {r.status_code}: {r.text}", prediction_id=pred_id)
    return r.json()


@retry_http
def _download(url: str) -> bytes:
    r = requests.get(url, timeout=60)
    if r.status_code != 200 or not r.content:
        raise AIGenerationError(f"Failed to download output: status={r.status_code}")
    return r.content


def run_nano_banana(*, prompt: str, image_urls: List[str], cfg) -> bytes:
    token = cfg.REPLICATE_API_TOKEN
    if not token:
        raise AIGenerationError("REPLICATE_API_TOKEN missing")

    # Replicate expects a model version id for \"version\"; allow passing full slug in env
    model = cfg.REPLICATE_MODEL

    created = _post_prediction(model=model, token=token, prompt=prompt, image_urls=image_urls)
    pred_id = created.get("id")
    if not pred_id:
        raise AIGenerationError("Prediction ID missing from Replicate response")

    deadline = time.time() + float(cfg.REPLICATE_TIMEOUT_SECS)
    interval = float(cfg.REPLICATE_POLL_INTERVAL_SECS)

    # Poll loop
    while True:
        if time.time() > deadline:
            raise AIGenerationError("Prediction timed out", prediction_id=pred_id)
        data = _get_prediction(pred_id=pred_id, token=token)
        status = data.get("status")
        if status in ("succeeded", "failed", "canceled"):
            if status != "succeeded":
                err = data.get("error") or data.get("logs") or status
                raise AIGenerationError(f"Prediction {status}: {err}", prediction_id=pred_id)
            # Expect output as list of URLs
            output = data.get("output") or []
            if isinstance(output, list) and output:
                return _download(output[0])
            if isinstance(output, str) and output:
                return _download(output)
            raise AIGenerationError("Empty output from Replicate", prediction_id=pred_id)
        time.sleep(interval)


