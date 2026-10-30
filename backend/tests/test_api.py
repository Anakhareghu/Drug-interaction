import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_health():
    response = client.get(f"{settings.API_V1_STR}/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_get_cohort():
    response = client.get(f"{settings.API_V1_STR}/cohort")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 7

def test_get_drugs():
    response = client.get(f"{settings.API_V1_STR}/drugs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 7
    assert "cefamandole" in data

def test_get_drug_info():
    response = client.get(f"{settings.API_V1_STR}/drugs/cefamandole")
    assert response.status_code == 200
    data = response.json()
    assert data["drug_name"] == "cefamandole"
    assert "chembl_id" in data

def test_get_invalid_drug():
    response = client.get(f"{settings.API_V1_STR}/drugs/invalid_drug")
    assert response.status_code == 404

def test_get_trajectories():
    response = client.get(f"{settings.API_V1_STR}/pk/trajectories")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 7

def test_get_similarity():
    response = client.get(f"{settings.API_V1_STR}/pk/similarity")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_get_network():
    response = client.get(f"{settings.API_V1_STR}/network")
    assert response.status_code == 200
    data = response.json()
    assert "edges" in data
    assert isinstance(data["edges"], list)

def test_get_clustering():
    response = client.get(f"{settings.API_V1_STR}/clustering")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 7

def test_get_coupling():
    response = client.get(f"{settings.API_V1_STR}/coupling")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_results():
    response = client.get(f"{settings.API_V1_STR}/results")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 7
