import os
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
    """Tests that the animatic generation endpoint returns a GCS URL."""
    r = requests.post(f"{BASE}/animatic", json={"script": script, "duration_seconds": 15})
    r.raise_for_status()
    response_json = r.json()
    assert "gcs_url" in response_json
    assert response_json["gcs_url"].startswith("gs://")
