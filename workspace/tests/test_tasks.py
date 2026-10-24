import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def override_dependency():
    Base.metadata.create_all(bind=engine)
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_create_task():
    response = client.post("/tasks", json={"title": "Test Task", "description": "Test Desc"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "Test Desc"
    assert data["completed"] is False
    assert "id" in data
    assert "created_at" in data

def test_create_task_invalid():
    response = client.post("/tasks", json={"description": "Missing title"})
    assert response.status_code == 422

def test_read_tasks():
    client.post("/tasks", json={"title": "Task 1"})
    client.post("/tasks", json={"title": "Task 2"})
    response = client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Task 1"

def test_read_task_by_id():
    post_resp = client.post("/tasks", json={"title": "Find Me"})
    task_id = post_resp.json()["id"]

    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Find Me"

def test_read_task_not_found():
    response = client.get("/tasks/999")
    assert response.status_code == 404

def test_update_task():
    post_resp = client.post("/tasks", json={"title": "Old Title"})
    task_id = post_resp.json()["id"]

    response = client.put(f"/tasks/{task_id}", json={"title": "New Title", "completed": True})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert data["completed"] is True

def test_update_task_not_found():
    response = client.put("/tasks/999", json={"title": "Ghost"})
    assert response.status_code == 404

def test_delete_task():
    post_resp = client.post("/tasks", json={"title": "Delete Me"})
    task_id = post_resp.json()["id"]

    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 204

    get_resp = client.get(f"/tasks/{task_id}")
    assert get_resp.status_code == 404

def test_delete_task_not_found():
    response = client.delete("/tasks/999")
    assert response.status_code == 404
