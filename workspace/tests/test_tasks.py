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
def override_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        def override_get_db():
            yield db
        app.dependency_overrides[get_db] = override_get_db
        yield
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_create_task():
    response = client.post("/tasks", json={"title": "Test Task", "description": "Test Description"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "Test Description"
    assert data["completed"] is False
    assert "id" in data
    assert "created_at" in data

def test_create_task_invalid_title():
    response = client.post("/tasks", json={"title": ""})
    assert response.status_code == 422 # Pydantic validation error

def test_list_tasks():
    client.post("/tasks", json={"title": "Task 1"})
    client.post("/tasks", json={"title": "Task 2"})
    
    response = client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Task 1"
    assert data[1]["title"] == "Task 2"

def test_get_task_by_id():
    post_resp = client.post("/tasks", json={"title": "Unique Task"})
    task_id = post_resp.json()["id"]

    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Unique Task"

def test_get_task_not_found():
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
    response = client.put("/tasks/999", json={"title": "Ghost Task"})
    assert response.status_code == 404

def test_delete_task():
    post_resp = client.post("/tasks", json={"title": "To Be Deleted"})
    task_id = post_resp.json()["id"]

    del_resp = client.delete(f"/tasks/{task_id}")
    assert del_resp.status_code == 204

    get_resp = client.get(f"/tasks/{task_id}")
    assert get_resp.status_code == 404

def test_delete_task_not_found():
    response = client.delete("/tasks/999")
    assert response.status_code == 404
