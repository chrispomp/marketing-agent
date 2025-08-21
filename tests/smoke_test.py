import os
import time
import requests
import pytest

BASE = os.environ.get("BASE_URL", "http://localhost:8080/v1/marketing")

@pytest.fixture(scope="module")
def brief():
    """Generates a brief and returns it."""
    r = requests.post(f"{BASE}/brief", json={"prompt": "A new energy drink for software developers."})
    r.raise_for_status()
    return r.json()["markdown"]

@pytest.fixture(scope="module")
def script(brief):
    """Generates a script from a brief and returns it."""
    r = requests.post(f"{BASE}/script", json={"brief_markdown": brief})
    r.raise_for_status()
    return r.json()["screenplay"]

def test_brief_generation(brief):
    """Tests that the brief generation endpoint returns a non-empty string."""
    assert brief and isinstance(brief, str)

def test_script_generation(script):
    """Tests that the script generation endpoint returns a non-empty string."""
    assert script and isinstance(script, str)

def test_storyboard_generation(script):
    """Tests that the storyboard generation endpoint returns a list of storyboard items."""
    r = requests.post(f"{BASE}/storyboard", json={"script": script})
    r.raise_for_status()
    response_json = r.json()
    assert "storyboard" in response_json
    storyboard = response_json["storyboard"]
    assert isinstance(storyboard, list)
    assert len(storyboard) > 0
    for item in storyboard:
        assert "scene_number" in item
        assert "gcs_url" in item
        assert item["gcs_url"].startswith("gs://")

def test_animatic_generation(script):
    """
    Tests that the animatic generation endpoint starts a job, can be polled,
    and eventually returns a GCS URL.
    """
    # Start the job
    r_start = requests.post(f"{BASE}/animatic", json={"script": script, "duration_seconds": 15})
    r_start.raise_for_status()
    response_json = r_start.json()
    assert "job_name" in response_json
    job_name = response_json["job_name"]
    assert job_name

    # Poll for completion
    timeout_seconds = 180  # 3 minutes
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        r_status = requests.get(f"{BASE}/animatic/status/{job_name}")
        r_status.raise_for_status()
        status_json = r_status.json()
        status = status_json["status"]

        if status == "SUCCEEDED":
            assert "gcs_url" in status_json
            assert status_json["gcs_url"].startswith("gs://")
            return  # Test succeeded

        if status == "FAILED":
            pytest.fail(f"Animatic generation failed: {status_json.get('error')}")

        time.sleep(10)  # Wait 10 seconds before polling again

    pytest.fail("Animatic generation timed out.")
