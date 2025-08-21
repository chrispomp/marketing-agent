import os
import json
from typing import Dict

import requests
import google.auth
import google.auth.transport.requests

class VeoClient:
    def __init__(self):
        self.project = os.environ["GCP_PROJECT"]
        self.location = os.environ.get("VERTEX_LOCATION", "us-central1")
        self.model_name = os.environ.get("VEO_MODEL", "veo-3.0-generate-preview") # Using a model from the new docs

        # Get credentials and access token
        self.creds, _ = google.auth.default()
        self.auth_req = google.auth.transport.requests.Request()
        self.creds.refresh(self.auth_req)

        self.api_base_url = f"https://{self.location}-aiplatform.googleapis.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.creds.token}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def _get_refreshed_headers(self):
        """Refreshes the auth token if necessary and returns headers."""
        if not self.creds.valid:
            self.creds.refresh(self.auth_req)
        return {
            "Authorization": f"Bearer {self.creds.token}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def start_generate_video_job(self, prompt: str, duration_seconds: int = 8) -> str:
        """
        Starts an asynchronous video generation job using direct HTTP requests.
        Returns the operation name.
        """
        # Per docs, veo-3.0-generate-preview only supports 8s duration
        if self.model_name == "veo-3.0-generate-preview":
            duration_seconds = 8

        endpoint = f"projects/{self.project}/locations/{self.location}/publishers/google/models/{self.model_name}"
        url = f"{self.api_base_url}/{endpoint}:predictLongRunning"

        request_body = {
            "instances": [{"prompt": prompt}],
            "parameters": {
                "durationSeconds": duration_seconds,
                "generateAudio": True # Required for preview model
            }
        }

        response = requests.post(url, headers=self._get_refreshed_headers(), json=request_body)
        response.raise_for_status()

        return response.json()["name"]

    def check_video_job_status(self, operation_name: str) -> Dict:
        """
        Checks the status of a video generation job using the custom fetch method.
        Returns a dict with status and result if complete.
        """
        # The operation_name is the full resource path, so we don't need to construct it.
        # The URL for fetch is different.
        endpoint = operation_name.split('/operations/')[0]
        url = f"{self.api_base_url}/{endpoint}:fetchPredictOperation"

        request_body = {"operationName": operation_name}

        response = requests.post(url, headers=self._get_refreshed_headers(), json=request_body)
        response.raise_for_status()
        op = response.json()

        if not op.get("done", False):
            return {"status": "RUNNING"}

        if "error" in op:
            return {"status": "FAILED", "error": op["error"]}

        # Extract GCS URL from the nested response
        try:
            video_info = op["response"]["videos"][0]
            gcs_url = video_info.get("gcsUri")
            if not gcs_url:
                 # The docs say it can also return bytes
                 if "bytesBase64Encoded" in video_info:
                     return {"status": "FAILED", "error": "Job finished but returned bytes instead of a GCS URI."}
                 return {"status": "FAILED", "error": "Could not find GCS URI in successful response."}
            return {"status": "SUCCEEDED", "gcs_url": gcs_url}
        except (KeyError, IndexError) as e:
            return {"status": "FAILED", "error": f"Failed to parse successful response: {e}. Response was: {op}"}
