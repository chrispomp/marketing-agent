import os
import google.auth
import google.auth.transport.requests

def get_gcp_token() -> str:
    """
    Retrieves a GCP access token using Application Default Credentials.
    """
    try:
        credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)
        return credentials.token
    except google.auth.exceptions.DefaultCredentialsError:
        print("🔴 ERROR: Could not find Application Default Credentials.")
        print("This is required for the agent to authenticate with Google Cloud services.")
        print("\nTo fix this, please run the following command in your terminal:")
        print("gcloud auth application-default login")
        print("\nFor more information, see the official documentation:")
        print("https://cloud.google.com/docs/authentication/provide-credentials-adc")
        raise

def get_api_endpoint() -> str:
    """Constructs the base Vertex AI API endpoint from environment variables."""
    region = os.getenv("REGION", "us-central1")
    return f"https://{region}-aiplatform.googleapis.com/v1"
