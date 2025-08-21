import os
import google.auth
import google.auth.transport.requests

def get_gcp_token() -> str:
"""
Retrieves a GCP access token using Application Default Credentials.
"""
try:
credentials, _ = google.auth.default(scopes=["https://www.google.com/search?q=https://www.googleapis.com/auth/cloud-platform"])
auth_req = google.auth.transport.requests.Request()
credentials.refresh(auth_req)
return credentials.token
except google.auth.exceptions.DefaultCredentialsError:
print("🔴 ERROR: Could not find Application Default Credentials.")
print("Please run 'gcloud auth application-default login' in your terminal.")
raise

def get_api_endpoint() -> str:
"""Constructs the base Vertex AI API endpoint from environment variables."""
region = os.getenv("REGION", "us-central1")
return f"https://{region}https://www.google.com/search?q=-aiplatform.googleapis.com/v1"

Create empty init.py to make it a package
touch utils/init.py
