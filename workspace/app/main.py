from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import engine, Base, get_db
from app.schemas import TaskCreate, TaskUpdate, TaskResponse
from app import crud

# Create database tables automatically if not present
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Manager REST API", version="1.0.0")

@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    if not task.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty or whitespace only.")
    return crud.create_task(db=db, task=task)

@app.get("/tasks", response_model=List[TaskResponse])
def list_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_tasks(db=db, skip=skip, limit=limit)

@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    db_task = crud.get_task(db=db, task_id=task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    if task_update.title is not None and not task_update.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty or whitespace only.")
    db_task = crud.update_task(db=db, task_id=task_id, task_update=task_update)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = crud.delete_task(db=db, task_id=task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return
